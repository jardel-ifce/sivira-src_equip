from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equips.modeladora_de_paes import ModeladoraDePaes
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular 
from utils.logger_factory import setup_logger
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
                        atividade_id=atividade.id,
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
                            f"✅ Atividade {atividade.id} alocada na modeladora {modeladora.nome} "
                            f"de {horario_inicio.strftime('%H:%M')} até {horario_final.strftime('%H:%M')}."
                        )
                        return True, modeladora, horario_inicio, horario_final

            horario_final -= timedelta(minutes=1)

        logger.warning(
            f"❌ Falha ao alocar atividade {atividade.id} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
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
            modeladora.liberar_por_atividade(ordem_id, pedido_id, atividade.id)
    
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
