from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.fogao import Fogao
from models.atividade_base import Atividade
from utils.gerador_ocupacao import GeradorDeOcupacaoID
from utils.logger_factory import setup_logger

# 🔥 Logger específico para o gestor de fogões
logger = setup_logger('GestorFogoes')


class GestorFogoes:
    """
    🔥 Gestor especializado no controle de fogões.
    Utiliza backward scheduling, levando em conta:
    - Ocupação por bocas
    - Vínculo com ID de ocupação e ID da atividade
    """

    def __init__(self, fogoes: List[Fogao]):
        self.fogoes = fogoes
        self.gerador_ocupacao_id = GeradorDeOcupacaoID()

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade
    ) -> Tuple[bool, Optional[Fogao], Optional[datetime], Optional[datetime]]:
        """
        🔥 Faz a alocação backward:
        Busca o horário mais tardio possível dentro da janela,
        respeitando ocupação por boca e a capacidade dos fogões.

        Retorna:
        (sucesso, fogao, inicio_real, fim_real)
        """
        duracao = atividade.duracao
        quantidade_gramas = atividade.quantidade_produto

        equipamentos_ordenados = sorted(
            self.fogoes,
            key=lambda fogao: atividade.fips_equipamentos.get(fogao, 999)
        )

        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicial_tentativa = horario_final_tentativa - duracao

            for fogao in equipamentos_ordenados:

                # 🔍 Simulação da ocupação (sem gerar ID ainda)
                pode_ocupar = fogao.ocupar(
                    ocupacao_id=None,
                    atividade_id=atividade.id,
                    quantidade_gramas=quantidade_gramas,
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa
                )

                if pode_ocupar:
                    # ✅ Agora sim, gerar o ID e registrar
                    ocupacao_id = self.gerador_ocupacao_id.gerar_id()
                    sucesso = fogao.ocupar(
                        ocupacao_id=ocupacao_id,
                        atividade_id=atividade.id,
                        quantidade_gramas=quantidade_gramas,
                        inicio=horario_inicial_tentativa,
                        fim=horario_final_tentativa
                    )

                    if sucesso:
                        logger.info(
                            f"✅ Fogão {fogao.nome} alocado para Atividade {atividade.id} "
                            f"de {horario_inicial_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        return True, fogao, horario_inicial_tentativa, horario_final_tentativa
                    else:
                        logger.debug(
                            f"# DEBUG: Falha inesperada na alocação real após simulação positiva."
                        )
                else:
                    logger.debug(
                        f"# DEBUG: Fogão {fogao.nome} não pode atender à atividade {atividade.id} nessa janela."
                    )

            # ⏪ Retrocede a tentativa
            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Nenhum fogão disponível para alocar a atividade {atividade.id} "
            f"dentro da janela {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        for fogao in self.fogoes:
            fogao.liberar_por_atividade(atividade_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for fogao in self.fogoes:
            fogao.liberar_bocas_terminadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for fogao in self.fogoes:
            fogao.liberar_todas_bocas()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda dos Fogões")
        logger.info("==============================================")
        for fogao in self.fogoes:
            fogao.mostrar_agenda()
