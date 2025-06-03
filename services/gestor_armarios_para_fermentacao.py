from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.armario_esqueleto import ArmarioEsqueleto
from models.atividade_base import Atividade
from utils.conversores_ocupacao import gramas_para_niveis_tela
from utils.gerador_ocupacao import GeradorDeOcupacaoID
from utils.logger_factory import setup_logger

# 🗂️ Logger específico
logger = setup_logger('GestorArmariosParaFermentacao')


class GestorArmariosParaFermentacao:
    """
    🗂️ Gestor especializado no controle de Armários Esqueleto para fermentação.
    Utiliza backward scheduling considerando:
    - Ocupação por níveis de tela (1000g por nível)
    """

    def __init__(self, armarios: List[ArmarioEsqueleto]):
        self.armarios = armarios
        self.gerador_ocupacao_id = GeradorDeOcupacaoID()

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade
    ) -> Tuple[str, Optional[ArmarioEsqueleto], Optional[datetime], Optional[datetime]]:
        """
        🗂️ Tenta alocar backward dentro da janela, com base em FIP e níveis de tela necessários.
        Retorna:
        - "SUCESSO" se conseguiu alocar
        - "ERRO_OCUPACAO" se nenhum armário tinha espaço suficiente
        """

        duracao = atividade.duracao
        quantidade_gramas = atividade.quantidade_produto
        niveis_necessarios = gramas_para_niveis_tela(quantidade_gramas)

        armarios_ordenados = sorted(
            self.armarios,
            key=lambda armario: atividade.fips_equipamentos.get(armario, 999)
        )

        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicial_tentativa = horario_final_tentativa - duracao

            for armario in armarios_ordenados:
                if not armario.verificar_espaco_niveis(
                    niveis_necessarios, horario_inicial_tentativa, horario_final_tentativa
                ):
                    logger.info(
                        f"❌ Armário {armario.nome} sem espaço entre "
                        f"{horario_inicial_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}."
                    )
                    continue

                ocupacao_id = self.gerador_ocupacao_id.gerar_id()
                sucesso = armario.ocupar_niveis(
                    ocupacao_id=ocupacao_id,
                    atividade_id=atividade.id,
                    quantidade=niveis_necessarios,
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa
                )

                if sucesso:
                    logger.info(
                        f"✅ Armário {armario.nome} alocado para Atividade {atividade.id} "
                        f"com {niveis_necessarios} níveis de {horario_inicial_tentativa.strftime('%H:%M')} "
                        f"até {horario_final_tentativa.strftime('%H:%M')}."
                    )
                    return "SUCESSO", armario, horario_inicial_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Nenhum armário pôde ser alocado para a atividade {atividade.id} "
            f"com {niveis_necessarios} níveis entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return "ERRO_OCUPACAO", None, None, None

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade: Atividade):
        for armario in self.armarios:
            armario.liberar_por_atividade(atividade.id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for armario in self.armarios:
            armario.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for armario in self.armarios:
            armario.liberar_todas_ocupacoes()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        for armario in self.armarios:
            armario.liberar_intervalo(inicio, fim)

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda dos Armários Esqueleto")
        logger.info("==============================================")
        for armario in self.armarios:
            armario.mostrar_agenda()
