from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equipamentos.modeladora_de_paes import ModeladoraDePaes
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular 
from utils.logs.logger_factory import setup_logger
import unicodedata
logger = setup_logger("GestorModeladoras")


class GestorModeladoras:
    """
    🥖 Gestor responsável pela alocação e controle de Modeladoras de Pães.
    Utiliza backward scheduling e prioriza equipamentos com menor FIP.
    """

    def __init__(self, modeladoras: List[ModeladoraDePaes]):
        self.modeladoras = modeladoras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================  
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[ModeladoraDePaes]:
        ordenadas = sorted(
            self.modeladoras,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        # logger.info("📊 Ordem das modeladoras por FIP:")
        # for m in ordenadas:
        #     fip = atividade.fips_equipamentos.get(m, 999)
        #     logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _obter_capacidade_unidade_por_minuto_explicita_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        """
        🔍 Verifica se há um valor explícito de 'capacidade_unidade_por_minuto' no JSON da atividade
        para a chave 
        para alguma chave que contenha 'modeladora' no nome. Se houver, retorna esse valor.
        """
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "modeladora" in chave_normalizada:
                    capacidade_gramas = conteudo.get("capacidade_unidade_por_minuto")
                    if capacidade_gramas is not None:
                        logger.info(
                            f"📦 JSON da atividade {atividade.id_atividade} define capacidade_unidade_por_minuto = {atividade.quantidade_unidades}g para o equipamento '{chave}'"
                        )
                        return capacidade_gramas
            logger.info(f"ℹ️ Nenhuma capacidade_unidade_por_minuto definida no JSON da atividade {atividade.id_atividade}.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar capacidade_unidade_por_minuto no JSON da atividade: {e}")
            return None
    # ==========================================================
    # 🎯 Alocação
    # ==========================================================    
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_unidades: int
    ) -> Tuple[bool, Optional[ModeladoraDePaes], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final = fim
        modeladoras_ordenadas = self._ordenar_por_fip(atividade)

        # logger.info(
        #     f"🧪 Tentando alocar atividade {atividade.id} ({quantidade_unidades} unid) "
        #     f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')} (dur: {duracao})."
        # )

        while horario_final - duracao >= inicio:
            horario_inicio = horario_final - duracao

            for modeladora in modeladoras_ordenadas:
                if modeladora.esta_disponivel(horario_inicio, horario_final):
                    sucesso = modeladora.ocupar(
                        ordem_id=atividade.ordem_id,
                        pedido_id=atividade.pedido_id,
                        atividade_id=atividade.id_atividade,
                        quantidade=quantidade_unidades,
                        inicio=horario_inicio,
                        fim=horario_final,
                        
                    )

                    if sucesso:
                        atividade.equipamento_alocado = modeladora
                        atividade.equipamentos_selecionados = [modeladora]
                        atividade.inicio_planejado = horario_inicio
                        atividade.fim_planejado = horario_final
                        atividade.alocada = True

                        logger.info(
                            f"✅ Atividade {atividade.id_atividade} alocada na modeladora {modeladora.nome} | Quantidade {quantidade_unidades} "
                            f"de {horario_inicio.strftime('%H:%M')} até {horario_final.strftime('%H:%M')}."
                        )
                        return True, modeladora, horario_inicio, horario_final

            horario_final -= timedelta(minutes=1)

        logger.warning(
            f"❌ Falha ao alocar atividade {atividade.id_atividade} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_ocupacoes_anteriores_a(self, horario_atual: datetime):
        for modeladora in self.modeladoras:
            modeladora.liberar_ocupacoes_anteriores_a(horario_atual)

    def liberar_por_atividade(self, ordem_id: int, pedido_id: int, atividade: "AtividadeModular"):
        for modeladora in self.modeladoras:
            modeladora.liberar_por_atividade(ordem_id, pedido_id, atividade.id_atividade)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for modeladora in self.modeladoras:
            modeladora.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for modeladora in self.modeladoras:
            modeladora.liberar_por_ordem(atividade.ordem_id)

    # ==========================================================
    # 📅  Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Modeladoras de Pães")
        logger.info("==============================================")
        for modeladora in self.modeladoras:
            modeladora.mostrar_agenda()
