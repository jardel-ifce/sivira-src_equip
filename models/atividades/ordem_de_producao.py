from typing import List
from datetime import datetime
import os
from models.atividades.atividade_modular import AtividadeModular
from parser.carregador_json_atividades import buscar_atividades_por_id_item
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from models.ficha_tecnica_modular import FichaTecnicaModular
from enums.tipo_item import TipoItem
from utils.logger_factory import setup_logger

logger = setup_logger("OrdemDeProducao")


class OrdemDeProducao:
    def __init__(
        self,
        ordem_id: int,
        id_produto: int,
        quantidade: int,
        inicio_jornada: datetime,
        fim_jornada: datetime,
    ):
        self.ordem_id=ordem_id
        self.id_produto = id_produto
        self.quantidade = quantidade
        self.inicio_jornada = inicio_jornada
        self.fim_jornada = fim_jornada
        self.ficha_tecnica_modular: FichaTecnicaModular | None = None
        self.atividades_modulares: List[AtividadeModular] = []

    def montar_estrutura(self):
        _, dados_ficha = buscar_ficha_tecnica_por_id(self.id_produto, TipoItem.PRODUTO)
        self.ficha_tecnica_modular = FichaTecnicaModular(
            dados_ficha_tecnica=dados_ficha,
            quantidade_requerida=self.quantidade
        )

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
                    ordem_id = self.ordem_id
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
        logger.info(f"🚀 Iniciando execução da Ordem {self.ordem_id} com {len(self.atividades_modulares)} atividades")
        current_fim = self.fim_jornada

        try:
            atividades_produto = sorted(
                [a for a in self.atividades_modulares if a.tipo_item == TipoItem.PRODUTO],
                key=lambda a: a.id_atividade,
                reverse=True
            )

            for at in atividades_produto:
                ok = at.tentar_alocar_e_iniciar(self.inicio_jornada, current_fim)
                if not ok:
                    raise RuntimeError(f"❌ Falha ao alocar atividade PRODUTO {at.id_atividade}")
                current_fim = at.inicio_real

            atividades_sub = [a for a in self.atividades_modulares if a.tipo_item == TipoItem.SUBPRODUTO]

            for at in atividades_sub:
                ok = at.tentar_alocar_e_iniciar(self.inicio_jornada, current_fim)
                if not ok:
                    raise RuntimeError(f"❌ Falha ao alocar atividade SUBPRODUTO {at.id_atividade}")

            logger.info("✅ Ordem finalizada com sucesso.")

        except Exception as e:
            logger.error(f"🛑 Erro na execução da ordem {self.ordem_id}: {e}")
            self.rollback()
            raise

    def rollback(self):
        logger.warning(f"🧹 Iniciando rollback da ordem {self.ordem_id}...")

        for atividade in self.atividades_modulares:
            if atividade.alocada:
                for equipamento in atividade.equipamentos_selecionados:
                    try:
                        if hasattr(equipamento, "liberar_por_atividade"):
                            equipamento.liberar_por_atividade(atividade.id)
                            logger.info(f"↩️ Liberado: Atividade {atividade.id} em {equipamento.nome}")
                    except Exception as e:
                        logger.warning(f"⚠️ Falha ao liberar {equipamento.nome}: {e}")

        log_path = f"logs/ordem_{self.ordem_id}.log"
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
                logger.info(f"🗑️ Arquivo de log removido: {log_path}")
        except Exception as e:
            logger.warning(f"⚠️ Falha ao remover log da ordem: {e}")
