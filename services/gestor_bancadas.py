from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from models.equips.bancada import Bancada
from utils.logger_factory import setup_logger


# 🪵 Logger específico para o gestor de bancadas
logger = setup_logger('GestorBancadas')


class GestorBancadas:
    """
    🪵 Gestor especializado para controle de bancadas,
    utilizando Backward Scheduling.
    """

    def __init__(self, bancadas: List[Bancada]):
        self.bancadas = bancadas

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade,
        fracoes_necessarias: int
    ) -> Tuple[bool, Optional[Bancada], Optional[datetime], Optional[datetime]]:
        """
        🪵 Realiza a alocação utilizando backward scheduling (do fim para o início).
        Retorna (True, bancada, inicio_real, fim_real) se sucesso,
        caso contrário (False, None, None, None).
        """
        duracao = atividade.duracao

        horario_final_tentativa = fim

        logger.info(
            f"🎯 Iniciando tentativa de alocação da atividade {atividade.id} "
            f"(duração: {duracao}, frações necessárias: {fracoes_necessarias}) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for bancada in self.bancadas:
                if bancada.fracoes_disponiveis(horario_inicio_tentativa, horario_final_tentativa) >= fracoes_necessarias:
                    sucesso = bancada.ocupar(
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        quantidade_fracoes=fracoes_necessarias,
                        atividade_id=atividade.id
                    )
                    if sucesso:
                        atividade.equipamento_alocado = bancada
                        atividade.equipamentos_selecionados = [bancada]
                        atividade.alocada = True

                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na bancada {bancada.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )

                        return True, bancada, horario_inicio_tentativa, horario_final_tentativa

            # Retrocede 5 minutos
            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade) -> None:
        """
        🧹 Libera todas as frações ocupadas relacionadas a uma atividade específica.
        """
        logger.info(
            f"🧹 Liberando frações associadas à atividade {atividade.id} em todas as bancadas."
        )
        for bancada in self.bancadas:
            bancada.liberar_por_atividade(atividade.id)

    def liberar_fracoes_finalizadas(self, horario_atual: datetime) -> None:
        """
        🔄 Libera frações que já terminaram seu período de ocupação.
        """
        logger.info(
            f"🔄 Liberando frações finalizadas das bancadas até {horario_atual.strftime('%H:%M')}."
        )
        for bancada in self.bancadas:
            bancada.liberar_fracoes_terminadas(horario_atual)

    def liberar_todas_fracoes(self) -> None:
        """
        🧹 Libera todas as frações ocupadas de todas as bancadas.
        """
        logger.info(f"🧹 Liberando todas as frações de todas as bancadas.")
        for bancada in self.bancadas:
            bancada.liberar_todas_fracoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self) -> None:
        """
        📅 Mostra a agenda de todas as bancadas.
        """
        logger.info("\n============================")
        logger.info("📅 Agenda das Bancadas")
        logger.info("============================")

        for bancada in self.bancadas:
            bancada.mostrar_agenda()
