from typing import List
from datetime import datetime
import os
from factory.fabrica_funcionarios import funcionarios_disponiveis
from models.funcionarios.funcionario import Funcionario
from models.atividades.atividade_modular import AtividadeModular
from parser.carregador_json_atividades import buscar_atividades_por_id_item
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from parser.carregador_json_tipos_profissionais import buscar_tipos_profissionais_por_id_item
from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
from enums.tipo_item import TipoItem
from utils.logs.logger_factory import setup_logger
from datetime import timedelta

logger = setup_logger("OrdemDeProducao")


class OrdemDeProducao:
    def __init__(
        self,
        ordem_id: int,
        id_produto: int,
        quantidade: int,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        todos_funcionarios: List[Funcionario] = funcionarios_disponiveis
    ):
        self.ordem_id = ordem_id
        self.id_produto = id_produto
        self.quantidade = quantidade
        self.inicio_jornada = inicio_jornada
        self.fim_jornada = fim_jornada
        self.todos_funcionarios = todos_funcionarios
        self.funcionarios_elegiveis: List[Funcionario] = []
        self.ficha_tecnica_modular: FichaTecnicaModular | None = None
        self.atividades_modulares: List[AtividadeModular] = []

    def montar_estrutura(self):
        _, dados_ficha = buscar_ficha_tecnica_por_id(self.id_produto, TipoItem.PRODUTO)
        self.ficha_tecnica_modular = FichaTecnicaModular(
            dados_ficha_tecnica=dados_ficha,
            quantidade_requerida=self.quantidade
        )
        self.funcionarios_elegiveis = self._filtrar_funcionarios_por_item(self.id_produto)

    def mostrar_estrutura(self):
        if self.ficha_tecnica_modular:
            self.ficha_tecnica_modular.mostrar_estrutura()

    def criar_atividades_modulares_necessarias(self):
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada.")
        self._criar_atividades_recursivas(self.ficha_tecnica_modular)

    def _criar_atividades_recursivas(self, ficha_modular: FichaTecnicaModular):
        try:
            atividades = buscar_atividades_por_id_item(ficha_modular.id_item, ficha_modular.tipo_item)
            for dados_gerais, dados_atividade in atividades:
                atividade = AtividadeModular(
                    id=len(self.atividades_modulares) + 1,
                    id_atividade=dados_atividade["id_atividade"],
                    tipo_item=ficha_modular.tipo_item,
                    quantidade_produto=ficha_modular.quantidade_requerida,
                    ordem_id=self.ordem_id,
                    id_produto=self.id_produto,
                    funcionarios_elegiveis=self.funcionarios_elegiveis
                )
                self.atividades_modulares.append(atividade)
        except Exception:
            pass  # Insumo puro

        estimativas = ficha_modular.calcular_quantidade_itens()
        for item_dict, quantidade in estimativas:
            tipo = item_dict.get("tipo_item")
            id_ficha = item_dict.get("id_ficha_tecnica")

            if tipo == "SUBPRODUTO" and id_ficha:
                _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha, TipoItem.SUBPRODUTO)
                ficha_sub = FichaTecnicaModular(dados_ficha_sub, quantidade)
                self._criar_atividades_recursivas(ficha_sub)

    def executar_atividades_em_ordem(self):
        logger.info(f"\ud83d\ude80 Iniciando execu\u00e7\u00e3o da Ordem {self.ordem_id} com {len(self.atividades_modulares)} atividades")
        current_fim = self.fim_jornada
        inicio_anterior = datetime(2025, 6, 17, 18, 1)

        try:
            atividades_produto = sorted(
                [a for a in self.atividades_modulares if a.tipo_item == TipoItem.PRODUTO],
                key=lambda a: a.id_atividade,
                reverse=True
            )

            for at in atividades_produto:
                ok, inicio_at, fim_at, tempo_max_de_espera_at = at.tentar_alocar_e_iniciar(self.inicio_jornada, current_fim)

                if tempo_max_de_espera_at and inicio_anterior - fim_at > tempo_max_de_espera_at:
                    tempo_atraso = inicio_anterior - fim_at
                    self.rollback()
                    raise RuntimeError(f"\u274c Falha ao alocar atividade PRODUTO {at.id_atividade} - Excedeu o tempo m\u00e1ximo de espera: {tempo_atraso}")

                inicio_anterior = inicio_at
                if not ok:
                    raise RuntimeError(f"\u274c Falha ao alocar atividade PRODUTO {at.id_atividade}")
                current_fim = at.inicio_real

            atividades_sub = [a for a in self.atividades_modulares if a.tipo_item == TipoItem.SUBPRODUTO]

            for at in atividades_sub:
                ok, inicio_at, fim_at, tempo_max_de_espera_at = at.tentar_alocar_e_iniciar(self.inicio_jornada, current_fim)

                if tempo_max_de_espera_at and inicio_anterior - fim_at > tempo_max_de_espera_at:
                    tempo_atraso = inicio_anterior - fim_at
                    self.rollback()
                    raise RuntimeError(f"\u274c Falha ao alocar atividade SUBPRODUTO {at.id_atividade} - Excedeu o tempo m\u00e1ximo de espera: {tempo_atraso}")

                inicio_anterior = inicio_at
                if not ok:
                    raise RuntimeError(f"\u274c Falha ao alocar atividade SUBPRODUTO {at.id_atividade}")

            logger.info("\u2705 Ordem finalizada com sucesso.")

        except Exception as e:
            logger.error(f"\ud83d\uded1 Erro na execu\u00e7\u00e3o da ordem {self.ordem_id}: {e}")
            try:
                os.makedirs("logs/erros", exist_ok=True)
                with open(f"logs/erros/ordem_{self.ordem_id}.log", "a") as f:
                    f.write(f"[{datetime.now()}] {str(e)}\n")
            except Exception as log_erro:
                logger.warning(f"\u26a0\ufe0f Falha ao registrar erro em arquivo: {log_erro}")
            self.rollback()

    def _filtrar_funcionarios_por_item(self, id_item: int) -> List[Funcionario]:
        tipos_necessarios = buscar_tipos_profissionais_por_id_item(id_item)
        return [f for f in self.todos_funcionarios if f.tipo_profissional in tipos_necessarios]

    def rollback(self):
        logger.warning(f"\ud83e\ude9d Iniciando rollback da ordem {self.ordem_id}...")

        for atividade in self.atividades_modulares:
            if atividade.alocada:
                for equipamento in atividade.equipamentos_selecionados:
                    try:
                        if hasattr(equipamento, "liberar_por_atividade"):
                            equipamento.liberar_por_atividade(atividade.id, ordem_id=atividade.ordem_id)
                            logger.info(f"\u21a9\ufe0f Liberado: Atividade {atividade.id} em {equipamento.nome}")
                    except Exception as e:
                        logger.warning(f"\u26a0\ufe0f Falha ao liberar {equipamento.nome}: {e}")
                for funcionario in self.funcionarios_elegiveis:
                    try:
                        if hasattr(funcionario, "liberar_por_atividade"):
                            funcionario.liberar_por_ordem(self.ordem_id)
                            logger.info(f"\u21a9\ufe0f Rollback: funcion\u00e1rio {funcionario.nome} liberado da ordem {self.ordem_id}")
                    except Exception as e:
                        logger.warning(f"\u26a0\ufe0f Falha ao liberar funcion\u00e1rio {funcionario.nome} da ordem {self.ordem_id}: {e}")

                self._remover_logs_ordem(atividade.ordem_id)

    def exibir_historico_de_funcionarios(self):
        for funcionario in funcionarios_disponiveis:
            funcionario.exibir_historico()

    def _remover_logs_ordem(self, ordem_id: int):
        log_path = f"logs/ordem_{ordem_id}.log"
        log_path_f = f"logs/funcionarios_{ordem_id}.log"

        try:
            if os.path.exists(log_path):
                os.remove(log_path)
                logger.info(f"\ud83d\uddd1\ufe0f Arquivo de log removido: {log_path}")
            if os.path.exists(log_path_f):
                os.remove(log_path_f)
                logger.info(f"\ud83d\uddd1\ufe0f Arquivo de log removido: {log_path_f}")
        except Exception as e:
            logger.warning(f"\u26a0\ufe0f Falha ao remover logs da ordem {ordem_id}: {e}")
