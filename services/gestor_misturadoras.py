from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from models.equips.masseira import Masseira
from models.atividade_base import Atividade
from utils.gerador_ocupacao import GeradorDeOcupacaoID
from utils.logger_factory import setup_logger

# 🔥 Logger exclusivo para o Gestor de Misturadoras
logger = setup_logger('GestorMisturadoras')


class GestorMisturadoras:
    """
    🌀 Gestor especializado no controle de Masseiras (Misturadoras).
    ✔️ Utiliza Backward Scheduling (agendamento reverso) com FIP.
    ✔️ Controle rigoroso por janela de tempo e capacidade de mistura.
    ✔️ Logs completos para rastreabilidade e auditoria.
    """

    def __init__(self, masseiras: List[Masseira]):
        self.masseiras = masseiras
        self.gerador_ocupacao_id = GeradorDeOcupacaoID()

    # ==========================================================
    # 🧠 Ordenação por FIP
    # ==========================================================
    def _ordenar_por_fip(self, atividade: Atividade) -> List[Masseira]:
        ordenadas = sorted(
            self.masseiras,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        logger.info("📊 Ordem das masseiras por FIP (prioridade):")
        for m in ordenadas:
            fip = atividade.fips_equipamentos.get(m, 999)
            logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas

    # ==========================================================
    # 🎯 Alocação backward
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade: float
    ) -> Tuple[bool, Optional[Masseira], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final_tentativa = fim

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {quantidade}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        masseiras_ordenadas = self._ordenar_por_fip(atividade)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for masseira in masseiras_ordenadas:
                if (
                    masseira.validar_capacidade(quantidade)
                    and masseira.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    ocupacao_id = self.gerador_ocupacao_id.gerar_id()

                    sucesso = masseira.ocupar(
                        ocupacao_id=ocupacao_id,
                        quantidade_gramas=quantidade,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        atividade_id=atividade.id
                    )

                    if sucesso:
                        atividade.equipamentos_selecionados.append(masseira)
                        atividade.inicio_planejado = horario_inicio_tentativa
                        atividade.fim_planejado = horario_final_tentativa
                        atividade.alocada = True

                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na masseira {masseira.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        return True, masseira, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma masseira "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for masseira in self.masseiras:
            masseira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for masseira in self.masseiras:
            masseira.ocupacoes.clear()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Masseiras")
        logger.info("==============================================")
        for masseira in self.masseiras:
            masseira.mostrar_agenda()

    # ==========================================================
    # 🔍 Consulta
    # ==========================================================
    def obter_masseira_por_id(self, id: int) -> Optional[Masseira]:
        for masseira in self.masseiras:
            if masseira.id == id:
                return masseira
        return None
