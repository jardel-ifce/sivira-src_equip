from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from models.equips.balanca_digital import BalancaDigital
from utils.logger_factory import setup_logger


# ⚖️ Logger específico para o gestor de balanças
logger = setup_logger('GestorBalancas')


class GestorBalancas:
    """
    ⚖️ Gestor especializado para controle de balanças digitais,
    utilizando Backward Scheduling (agendamento reverso no tempo).
    """

    def __init__(self, balancas: List[BalancaDigital]):
        self.balancas = balancas

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade,
        quantidade_gramas: float
    ) -> Tuple[bool, Optional[BalancaDigital], Optional[datetime], Optional[datetime]]:
        """
        🎯 Realiza a alocação backward (do fim para o início).
        Retorna (True, balanca, inicio_real, fim_real) se sucesso,
        caso contrário (False, None, None, None).
        """
        duracao = atividade.duracao

        horario_final_tentativa = fim

        logger.info(
            f"🎯 Iniciando tentativa de alocação da atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {quantidade_gramas}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for balanca in self.balancas:
                if (
                    balanca.validar_peso(quantidade_gramas) and
                    balanca.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    sucesso = balanca.ocupar(
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        quantidade_gramas=quantidade_gramas,
                        atividade_id=atividade.id
                    )
                    if sucesso:
                        atividade.equipamento_alocado = balanca
                        atividade.equipamentos_selecionados = [balanca]
                        atividade.alocada = True

                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na balança {balanca.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )

                        return True, balanca, horario_inicio_tentativa, horario_final_tentativa

            # ⏪ Retrocede 5 minutos
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
        🔄 Libera todas as ocupações associadas a uma atividade específica.
        """
        logger.info(
            f"🧹 Liberando ocupações da atividade {atividade.id} nas balanças."
        )
        for balanca in self.balancas:
            balanca.liberar_por_atividade(atividade.id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        logger.info(
            f"🔄 Liberando ocupações finalizadas das balanças até {horario_atual.strftime('%H:%M')}."
        )
        for balanca in self.balancas:
            balanca.liberar_ocupacoes_terminadas(horario_atual)

    def liberar_todas_ocupacoes(self) -> None:
        logger.info(f"🧹 Liberando todas as ocupações de todas as balanças.")
        for balanca in self.balancas:
            balanca.liberar_todas_ocupacoes()

    def liberar_intervalo(self, inicio: datetime, fim: datetime) -> None:
        """
        🧹 Libera ocupações que estão dentro do intervalo especificado para todas as balanças.
        """
        logger.info(
            f"🧹 Liberando ocupações das balanças no intervalo "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        for balanca in self.balancas:
            balanca.liberar_intervalo(inicio, fim)

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self) -> None:
        logger.info("\n============================")
        logger.info("📅 Agenda das Balanças")
        logger.info("============================")

        for balanca in self.balancas:
            balanca.mostrar_agenda()
