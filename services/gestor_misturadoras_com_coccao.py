from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.hot_mix import HotMix
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger


# 🔥 Logger específico para este gestor
logger = setup_logger('GestorMisturadorasComCoccao')


class GestorMisturadorasComCoccao:
    """
    🍳 Gestor especializado para controle das Misturadoras com Cocção (HotMix).
    ✔️ Alocação backward (do fim para o início).
    ✔️ Validação de capacidade (peso) e disponibilidade no tempo.
    ✔️ Priorização por FIP (Fator de Importância dos Equipamentos).
    """

    def __init__(self, hotmixes: List[HotMix]):
        self.hotmixes = hotmixes

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade
    ) -> Tuple[bool, Optional[HotMix], Optional[datetime], Optional[datetime]]:
        """
        🚀 Realiza a alocação backward scheduling.
        Retorna:
        (sucesso, hotmix_alocado, inicio_real, fim_real)
        """
        duracao = atividade.duracao
        quantidade = atividade.quantidade_produto

        horario_final_tentativa = fim

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {quantidade}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for hotmix in sorted(
                self.hotmixes,
                key=lambda h: atividade.fips_equipamentos.get(h, 999)
            ):
                if (
                    hotmix.validar_capacidade(quantidade)
                    and hotmix.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    sucesso = hotmix.ocupar(
                        quantidade_gramas=quantidade,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        atividade_id=atividade.id
                    )
                    if sucesso:
                        atividade.equipamentos_selecionados.append(hotmix)
                        atividade.inicio_planejado = horario_inicio_tentativa
                        atividade.fim_planejado = horario_final_tentativa
                        atividade.alocada = True

                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na {hotmix.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        return True, hotmix, horario_inicio_tentativa, horario_final_tentativa

            # Retrocede no tempo (passo de 5 minutos)
            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma HotMix "
            f"dentro da janela até {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for hotmix in self.hotmixes:
            hotmix.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for hotmix in self.hotmixes:
            hotmix.ocupacoes.clear()

    # ==========================================================
    # 🔍 Consulta e Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("\n========================")
        logger.info("📅 Agenda das HotMix")
        logger.info("========================")
        for hotmix in self.hotmixes:
            hotmix.mostrar_agenda()

    def obter_hotmix_por_id(self, id: int) -> Optional[HotMix]:
        for hotmix in self.hotmixes:
            if hotmix.id == id:
                return hotmix
        return None
