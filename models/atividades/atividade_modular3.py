import os
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_item import TipoItem
from enums.tipo_profissional import TipoProfissional
from typing import List, Optional
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividade_base import Atividade
from models.funcionarios.funcionario import Funcionario
from parser.carregador_json_atividades import buscar_dados_por_id_atividade
from factory import fabrica_equipamentos
import unicodedata
from datetime import datetime, timedelta

logger = setup_logger('Atividade_Modular')


class AtividadeModular(Atividade):
    def __init__(self, id, id_atividade: int, tipo_item: TipoItem, quantidade_produto: int, *args, **kwargs):
        self.ordem_id = kwargs.get("ordem_id")
        id_produto_gerado = kwargs.get("id_produto")


        dados_atividade = kwargs.get("dados")
        if not dados_atividade:
            dados_gerais, dados_atividade = buscar_dados_por_id_atividade(id_atividade, tipo_item)
            self.nome_atividade = dados_gerais.get("nome_atividade", f"Atividade {id_atividade}")
            self.nome_item = dados_gerais.get("nome_item", "item_desconhecido")
        else:
            self.nome_atividade = f"Atividade {id_atividade}"
            self.nome_item = "item_desconhecido"
        # ================================================
        # Lógica do tempo de espera
        # ================================================        
        #self.ordem = kwargs.get("ordem")
        valor = dados_atividade.get("tempo_maximo_de_espera")
        if valor:
            # Interpreta "00:05" como HH:MM
            horas, minutos = map(int, valor.split(":"))
            self.tempo_maximo_espera = timedelta(hours=horas, minutes=minutos)
        else:
            self.tempo_maximo_espera = timedelta.max
        
        self.inicio_da_atividade_que_sucede: datetime | None = None

        # ================================================
        # Lógica dos funcionários
        # ================================================
        self.tipos_necessarios = set(
            TipoProfissional[nome] for nome in dados_atividade.get("tipos_profissionais_permitidos",[])
        )

        self.funcionarios_elegiveis = kwargs.get("funcionarios_elegiveis", [])
        self.funcionarios_necessarios: List[Funcionario] = []
        self.qtd_profissionais_requeridos: int = int(dados_atividade.get("quantidade_funcionarios", 0))

        # Seleciona somente os necessários para a atividade
        self.funcionarios_necessarios = [
            f for f in self.funcionarios_elegiveis if f.tipo_profissional in self.tipos_necessarios
        ]
        for f in self.funcionarios_necessarios:
            print(f"✔️ {f.nome} - {f.tipo_profissional.name}")
        
        # Obtém fips dos profissionais permitidos
        self.fips_profissionais_permitidos: dict[str, int] = dados_atividade.get(
            "fips_profissionais_permitidos", {}
        )

        # Quantidade de profissionais requeridos para a atividade
        self.qtd_profissionais_requeridos: int = int(dados_atividade.get("quantidade_funcionarios", 0))


        nomes_equipamentos = dados_atividade.get("equipamentos_elegiveis", [])
        equipamentos_elegiveis = [getattr(fabrica_equipamentos, nome) for nome in nomes_equipamentos]
        self.tipo_item = tipo_item

        super().__init__(
            id=id,
            id_atividade=id_atividade,
            tipos_profissionais_permitidos=[],
            quantidade_funcionarios=0,
            equipamentos_elegiveis=equipamentos_elegiveis,
            id_produto_gerado=id_produto_gerado,
            quantidade_produto=quantidade_produto
        )

        self.fips_equipamentos = {
            getattr(fabrica_equipamentos, nome): fip
            for nome, fip in dados_atividade.get("fips_equipamentos", {}).items()
        }

        self.configuracoes_equipamentos = dados_atividade.get("configuracoes_equipamentos", {})

        self._quantidade_por_tipo_equipamento = {
            TipoEquipamento[nome]: qtd
            for nome, qtd in dados_atividade.get("tipo_equipamento", {}).items()
        }

        self.duracao = self._consultar_duracao_por_faixas(dados_atividade)

    def calcular_duracao(self):
        return super().calcular_duracao()

    def _consultar_duracao_por_faixas(self, dados_atividade) -> timedelta:
        faixas = dados_atividade.get("faixas", [])
        qtd = self.quantidade_produto

        for faixa in faixas:
            min_qtd = faixa.get("quantidade_min")
            max_qtd = faixa.get("quantidade_max")

            if min_qtd is None or max_qtd is None:
                raise ValueError(f"❌ Faixa de quantidade inválida ou incompleta: {faixa}")

            if min_qtd <= qtd <= max_qtd:
                h, m, s = map(int, faixa["duracao"].split(":"))
                return timedelta(hours=h, minutes=m, seconds=s)

        raise ValueError(f"❌ Nenhuma faixa compatível com a quantidade {qtd}g.")

    def _criar_gestores_por_tipo(self) -> dict[TipoEquipamento, object]:
        gestores_por_tipo = {}

        for tipo_equipamento, _ in self._quantidade_por_tipo_equipamento.items():
            if tipo_equipamento not in MAPA_GESTOR:
                raise ValueError(f"❌ Gestor não definido para o tipo de equipamento: {tipo_equipamento.name}")

            gestor_cls = MAPA_GESTOR[tipo_equipamento]

            equipamentos_filtrados = [
                equipamento for equipamento in self.equipamentos_elegiveis
                if equipamento.tipo_equipamento == tipo_equipamento
            ]

            if not equipamentos_filtrados:
                raise ValueError(f"⚠️ Nenhum equipamento do tipo {tipo_equipamento.name} associado à atividade.")

            gestores_por_tipo[tipo_equipamento] = gestor_cls(equipamentos_filtrados)

        return gestores_por_tipo

    def tentar_alocar_e_iniciar(self, inicio_jornada: datetime, fim_jornada: datetime) -> bool:
        horario_final = fim_jornada

        while horario_final - self.duracao >= inicio_jornada:
            sucesso = True
            equipamentos_alocados = []
            ocupacoes_efetuadas = []
            horario_fim_etapa = horario_final

            for tipo_eqp, _ in reversed(list(self._quantidade_por_tipo_equipamento.items())):
                equipamentos = [eqp for eqp in self.equipamentos_elegiveis if eqp.tipo_equipamento == tipo_eqp]

                if not equipamentos:
                    logger.warning(f"⚠️ Nenhum equipamento do tipo {tipo_eqp} disponível.")
                    sucesso = False
                    break

                classe_gestor = MAPA_GESTOR.get(tipo_eqp)
                if not classe_gestor:
                    logger.warning(f"⚠️ Nenhum gestor configurado para tipo {tipo_eqp}")
                    sucesso = False
                    break

                gestor = classe_gestor(equipamentos)
                metodo_alocacao = self._resolver_metodo_alocacao(tipo_eqp)

                equipamento_exemplo = equipamentos[0]
                nome_normalizado = self._normalizar_nome(equipamento_exemplo.nome)
                config = self.configuracoes_equipamentos.get(nome_normalizado, {})

                # 🔧 Corrigido: cálculo seguro de horário de início
                inicio_previsto = horario_fim_etapa - self.duracao

                if self.duracao.total_seconds() > 0 and inicio_previsto == horario_fim_etapa:
                    inicio_previsto -= timedelta(self.duracao)

                try:
                    resultado = metodo_alocacao(
                        gestor=gestor,
                        inicio=inicio_previsto,
                        fim=horario_fim_etapa,
                        **config
                    )

                    if not resultado[0]:
                        sucesso = False
                        break

                    equipamentos_alocados.append(resultado)
                    if hasattr(resultado[1], "ultimos_ids_ocupacao"):
                        for ocupacao_id in resultado[1].ultimos_ids_ocupacao:
                            ocupacoes_efetuadas.append((resultado[1], ocupacao_id))

                    horario_fim_etapa = resultado[2]

                except Exception as e:
                    logger.error(f"❌ Erro ao alocar {tipo_eqp}: {e}")
                    sucesso = False
                    break

            if sucesso:
                inicio_funcionario, fim_funcionario = self._registrar_sucesso(equipamentos_alocados, horario_fim_etapa, horario_final)
                    # ✅ Atualiza o valor global para a próxima atividade
                #self._atualizar_inicio_na_ordem()
                profissionais = self._priorizar_funcionarios()
                # ✅ Atribui à atividade
                self.funcionarios_alocados = profissionais
                # 📝 Registra a alocação no histórico de cada profissional
                for f in profissionais:
                    f.registrar_alocacao(self.ordem_id, self.id, self.nome_atividade, inicio_funcionario, fim_funcionario)

                    logger.info(
                        f"👷 Funcionário {f.nome} alocado na atividade {self.nome_atividade} "
                        f"das {inicio_funcionario.strftime('%H:%M')} às {fim_funcionario.strftime('%H:%M')}"
                    )
                return True


            for equipamento in [e[1] for e in equipamentos_alocados]:
                try:
                    if hasattr(equipamento, "liberar_por_atividade"):
                        equipamento.liberar_por_atividade(self.id)
                        logger.info(f"↩️ Rollback: desalocada atividade {self.id} em {equipamento.nome}")
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao desalocar atividade {self.id} de {equipamento.nome}: {e}")

            horario_final -= timedelta(minutes=1)

        logger.error(f"❌ Não foi possível alocar a atividade {self.id_atividade} dentro da jornada.")
        return False


    def _registrar_sucesso(self, equipamentos_alocados, inicio: datetime, fim: datetime, **kwargs):
        self.equipamentos_selecionados = [dados[1] for dados in equipamentos_alocados]
        self.equipamento_alocado = self.equipamentos_selecionados
        self.inicio_real = inicio
        self.fim_real = fim
        self.alocada = True

        logger.info("✅ Atividade alocada com sucesso!")
        for sucesso, equipamento, i, f in equipamentos_alocados:
            if i and f:
                logger.info(f"🔧 {equipamento.nome} alocado de {i.strftime('%H:%M')} até {f.strftime('%H:%M')}")
            else:
                logger.info(f"🔧 {equipamento.nome} alocado (sem janela de tempo)")

        if self.ordem_id:
            os.makedirs("logs", exist_ok=True)
            caminho = f"logs/ordem_{self.ordem_id}.log"
            with open(caminho, "a", encoding="utf-8") as arq:
                for _, equipamento, inicio, fim in equipamentos_alocados:
                    linha = (
                        f"{self.ordem_id} | "
                        f"{self.id_atividade} | {self.nome_item} | {self.nome_atividade} | "
                        f"{equipamento.nome} | {inicio.strftime('%H:%M')} | {fim.strftime('%H:%M')}\n"
                    )
                    arq.write(linha)
        inicios = [i for _, _, i, _ in equipamentos_alocados if i]
        fins = [f for _, _, _, f in equipamentos_alocados if f]
        
        # ✅ Retorna os extremos para alocação de funcionário
        return min(inicios), max(fins)

    def _resolver_metodo_alocacao(self, tipo_equipamento):
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: self._alocar_camara,
            TipoEquipamento.BANCADAS: self._alocar_bancada,
            TipoEquipamento.FOGOES: self._alocar_fogao,
            TipoEquipamento.BATEDEIRAS: self._alocar_batedeira,
            TipoEquipamento.BALANCAS: self._alocar_balanca,
            TipoEquipamento.FORNOS: self._alocar_forno,
            TipoEquipamento.MISTURADORAS: self._alocar_misturadora,
            TipoEquipamento.MISTURADORAS_COM_COCCAO: self._alocar_misturadora_com_coccao,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: self._alocar_armario_fermentacao,
            TipoEquipamento.MODELADORAS: self._alocar_modeladora,
            TipoEquipamento.DIVISORAS_BOLEADORAS: self._alocar_divisora_boleadora,
        }.get(tipo_equipamento, lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError(f"❌ Nenhum método de alocação definido para {tipo_equipamento}")
        ))

    def _alocar_camara(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_bancada(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self)
    def _alocar_fogao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_batedeira(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_balanca(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_forno(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_misturadora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_misturadora_com_coccao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_armario_fermentacao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_modeladora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_divisora_boleadora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def mostrar_agendas_dos_gestores(self):
        try:
            gestores = self._criar_gestores_por_tipo()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível criar os gestores para mostrar agenda: {e}")
            return
        for tipo, gestor in gestores.items():
            if hasattr(gestor, "mostrar_agenda"):
                gestor.mostrar_agenda()
            else:
                logger.warning(f"⚠️ Gestor de {tipo.name} não possui método 'mostrar_agenda'.")

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")


    # MÉTODOS DE FUNCIONÁRIOS
    def _priorizar_funcionarios(self) -> List[Funcionario]:
        """
        Seleciona até N profissionais (quantidade_funcionarios) com base em:
        - tipos permitidos (self.tipos_necessarios)
        - fips definidos no JSON
        - engajamento na ordem
        - desempate com f.fip (opcional)
        """

        n = self.qtd_profissionais_requeridos
        if n == 0:
            logger.info(f"ℹ️ Atividade {self.nome_atividade} não requer funcionários.")
            return []

        # 🧪 DEBUG: tipos esperados e funcionários elegíveis
        logger.warning(f"🧪 [{self.nome_atividade}] Tipos profissionais necessários: {self.tipos_necessarios}")
        logger.warning(f"🧪 [{self.nome_atividade}] Funcionários elegíveis na ordem:")
        for f in self.funcionarios_elegiveis:
            logger.warning(f"   └ {f.nome} ({f.tipo_profissional.name})")

        # 🔍 Candidatos compatíveis (corrigido: enum direto)
        candidatos = [
            f for f in self.funcionarios_elegiveis
            if f.tipo_profissional in self.tipos_necessarios
        ]

        if not candidatos:
            logger.warning(f"⚠️ Nenhum funcionário compatível para {self.nome_atividade}")
            return []

        # 🔢 Critério de ordenação por prioridade (fip JSON + engajamento + fip real)
        def chave_ordem(f: Funcionario):
            fip_json = self.fips_profissionais_permitidos.get(f.tipo_profissional.name, 999_999)
            engajado = 0 if f.ja_esta_na_ordem(self.ordem_id) else 1
            return (fip_json, engajado, f.fip)

        selecionados = sorted(candidatos, key=chave_ordem)[:n]

        if len(selecionados) < n:
            logger.warning(
                f"⚠️ Apenas {len(selecionados)}/{n} profissionais disponíveis para {self.nome_atividade}"
            )

        return selecionados



    def _atualizar_inicio_na_ordem(self):
        """
        Atualiza o valor global de início da próxima atividade na OrdemDeProducao.
        """
        if self.ordem and self.inicio_real:
            self.ordem.inicio_atividade_sucessora = self.inicio_real
            logger.info(
                f"🔁 Atualizado início da próxima atividade na ordem para {self.inicio_real.strftime('%H:%M')} "
                f"(atividade atual: {self.nome_atividade})"
            )


from typing import List
from datetime import datetime
import os
from factory.fabrica_funcionarios import funcionarios_disponiveis
from models.funcionarios.funcionario import Funcionario
from models.atividades.atividade_modular import AtividadeModular
from parser.carregador_json_atividades import buscar_atividades_por_id_item
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from parser.carregador_json_tipos_profissionais import buscar_tipos_profissionais_por_id_item
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
        todos_funcionarios: List[Funcionario] = funcionarios_disponiveis
    ):
        self.ordem_id=ordem_id
        self.id_produto = id_produto
        self.quantidade = quantidade
        self.inicio_jornada = inicio_jornada
        self.fim_jornada = fim_jornada
        self.todos_funcionarios = todos_funcionarios
        self.funcionarios_elegiveis: List[Funcionario] = []
        self.ficha_tecnica_modular: FichaTecnicaModular | None = None
        self.atividades_modulares: List[AtividadeModular] = []
        self.inicio_atividade_sucessora: datetime | None = None # usado para lógica do tempo_de_espera

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
                    ordem_id = self.ordem_id,
                    id_produto=self.id_produto,
                    funcionarios_elegiveis=self.funcionarios_elegiveis,
                    inicio_da_atividade_que_sucede=self.inicio_atividade_sucessora, # Lógica do tempo de espera
                    ordem=self
                )
                self.atividades_modulares.append(atividade)
                if atividade.inicio_real:  # <- pode ser None se ainda não foi alocada
                    self.inicio_atividade_sucessora = atividade.inicio_real
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

    def _filtrar_funcionarios_por_item(self, id_item: int) -> List[Funcionario]:
        """
        🔎 Filtra os funcionários compatíveis com o item, com base nos tipos profissionais exigidos.

        Args:
            id_item (int): ID do produto ou subproduto.

        Returns:
            List[Funcionario]: Lista apenas com os funcionários compatíveis.
        """
        tipos_necessarios = buscar_tipos_profissionais_por_id_item(id_item)
        return [f for f in self.todos_funcionarios if f.tipo_profissional in tipos_necessarios]

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

    def exibir_historico_de_funcionarios(self):
        for funcionario in funcionarios_disponiveis:
            funcionario.exibir_historico()
	