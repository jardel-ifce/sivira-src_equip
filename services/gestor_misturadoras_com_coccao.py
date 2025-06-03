from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.hot_mix import HotMix
from models.atividade_base import Atividade
from utils.gerador_ocupacao import GeradorDeOcupacaoID
from utils.logger_factory import setup_logger
from enums.tipo_velocidade import TipoVelocidade
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama

# 🔥 Logger específico para este gestor
logger = setup_logger('GestorMisturadorasComCoccao')


class GestorMisturadorasComCoccao:
    """
    🍳 Gestor especializado para controle das Misturadoras com Cocção (HotMix).
    ✔️ Alocação backward (do fim para o início).
    ✔️ Validação de capacidade, velocidade, chamas e pressão de chama.
    ✔️ Priorização por FIP (Fator de Importância dos Equipamentos).
    """

    def __init__(self, hotmixes: List[HotMix]):
        self.hotmixes = hotmixes
        self.gerador_ocupacao_id = GeradorDeOcupacaoID()

    # ==========================================================
    # 🎯 Alocação Backward
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade
    ) -> Tuple[bool, Optional[HotMix], Optional[datetime], Optional[datetime]]:
        duracao = atividade.duracao
        quantidade = atividade.quantidade_produto

        # ✅ Agora buscamos os valores diretamente da atividade
        velocidade: TipoVelocidade = atividade.velocidade
        chamas: List[TipoChama] = atividade.chamas
        pressoes: List[TipoPressaoChama] = atividade.pressoes

        horario_final_tentativa = fim

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {quantidade}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        hotmixes_ordenadas = sorted(
            self.hotmixes,
            key=lambda h: atividade.fips_equipamentos.get(h, 999)
        )

        for hotmix in hotmixes_ordenadas:
            logger.info(f"🔍 Avaliando HotMix {hotmix.nome} (FIP: {atividade.fips_equipamentos.get(hotmix, 999)})")

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for hotmix in hotmixes_ordenadas:
                if not (
                    hotmix.validar_capacidade(quantidade)
                    and hotmix.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                    and hotmix.configurar_velocidade(velocidade)
                    and hotmix.verificar_chamas_suportadas(chamas)
                    and hotmix.verificar_pressoes_suportadas(pressoes)
                ):
                    continue

                ocupacao_id = self.gerador_ocupacao_id.gerar_id()

                sucesso = hotmix.ocupar(
                    ocupacao_id=ocupacao_id,
                    atividade_id=atividade.id,
                    quantidade=quantidade,
                    inicio=horario_inicio_tentativa,
                    fim=horario_final_tentativa,
                    chamas=chamas,
                    pressao_chamas=pressoes
                )

                if sucesso:
                    atividade.equipamentos_selecionados.append(hotmix)
                    atividade.inicio_planejado = horario_inicio_tentativa
                    atividade.fim_planejada = horario_final_tentativa
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {atividade.id} alocada na HotMix {hotmix.nome} "
                        f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                    )
                    return True, hotmix, horario_inicio_tentativa, horario_final_tentativa

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
            hotmix.resetar()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das HotMix")
        logger.info("==============================================")
        for hotmix in self.hotmixes:
            hotmix.mostrar_agenda()

    # ==========================================================
    # 🔍 Consulta
    # ==========================================================
    def obter_hotmix_por_id(self, id: int) -> Optional[HotMix]:
        for hotmix in self.hotmixes:
            if hotmix.id == id:
                return hotmix
        return None
