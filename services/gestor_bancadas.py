from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.bancada import Bancada
from models.atividade_base import Atividade
from utils.gerador_ocupacao import GeradorDeOcupacaoID
from utils.logger_factory import setup_logger


# 🪵 Logger específico para o gestor de bancadas
logger = setup_logger('GestorBancadas')


class GestorBancadas:
    """
    🪵 Gestor especializado para controle de bancadas,
    utilizando Backward Scheduling com FIPs.
    """

    def __init__(self, bancadas: List[Bancada]):
        self.bancadas = bancadas
        self.gerador_ocupacao_id = GeradorDeOcupacaoID()

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        fracoes_necessarias: int
    ) -> Tuple[bool, Optional[Bancada], Optional[datetime], Optional[datetime]]:
        """
        🪵 Realiza a alocação utilizando backward scheduling (do fim para o início),
        ordenando por FIP (menor valor tem prioridade).
        Retorna (True, bancada, inicio_real, fim_real) se sucesso,
        caso contrário (False, None, None, None).
        """
        duracao = atividade.duracao

        equipamentos_ordenados = sorted(
            self.bancadas,
            key=lambda bancada: atividade.fips_equipamentos.get(bancada, 999)
        )

        horario_final_tentativa = fim

        logger.info(
            f"🎯 Iniciando tentativa de alocação da atividade {atividade.id} "
            f"(duração: {duracao}, frações necessárias: {fracoes_necessarias}) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for bancada in equipamentos_ordenados:
                if bancada.fracoes_disponiveis(horario_inicio_tentativa, horario_final_tentativa) >= fracoes_necessarias:
                    # Somente gera ID se a bancada puder realmente ser ocupada
                    ocupacao_id = self.gerador_ocupacao_id.gerar_id()
                    sucesso = bancada.ocupar(
                        ocupacao_id=ocupacao_id,
                        atividade_id=atividade.id,
                        quantidade_fracoes=fracoes_necessarias,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa
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

            horario_final_tentativa -= timedelta(minutes=1)
            

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None


    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: Atividade) -> None:
        logger.info(
            f"🧹 Liberando frações associadas à atividade {atividade.id} em todas as bancadas."
        )
        for bancada in self.bancadas:
            bancada.liberar_por_atividade(atividade.id)

    def liberar_fracoes_finalizadas(self, horario_atual: datetime) -> None:
        logger.info(
            f"🔄 Liberando frações finalizadas das bancadas até {horario_atual.strftime('%H:%M')}."
        )
        for bancada in self.bancadas:
            bancada.liberar_fracoes_terminadas(horario_atual)

    def liberar_todas_fracoes(self) -> None:
        logger.info("🧹 Liberando todas as frações de todas as bancadas.")
        for bancada in self.bancadas:
            bancada.liberar_todas_fracoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self) -> None:
        logger.info("==============================================")
        logger.info("📅 Agenda das Bancadas")
        logger.info("==============================================")
        for bancada in self.bancadas:
            bancada.mostrar_agenda()
