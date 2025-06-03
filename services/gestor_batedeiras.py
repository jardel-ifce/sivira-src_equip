from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from models.equips.batedeira_industrial import BatedeiraIndustrial
from models.atividade_base import Atividade
from utils.gerador_ocupacao import GeradorDeOcupacaoID
from utils.logger_factory import setup_logger


# 🏭 Logger específico para o gestor de batedeiras
logger = setup_logger('GestorBatedeiras')


class GestorBatedeiras:
    """
    🏭 Gestor especializado para controle de batedeiras industriais,
    utilizando backward scheduling com prioridade por FIP.
    """

    def __init__(self, batedeiras: List[BatedeiraIndustrial]):
        self.batedeiras = batedeiras
        self.gerador_ocupacao_id = GeradorDeOcupacaoID()

    # ==========================================================
    # 🧠 Ordenação por FIP
    # ==========================================================
    def _ordenar_por_fip(self, atividade: Atividade) -> List[BatedeiraIndustrial]:
        ordenadas = sorted(
            self.batedeiras,
            key=lambda b: atividade.fips_equipamentos.get(b, 999)
        )
        logger.info("📊 Ordem das batedeiras por FIP (prioridade):")
        for b in ordenadas:
            fip = atividade.fips_equipamentos.get(b, 999)
            logger.info(f"🔹 {b.nome} (FIP: {fip})")
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
    ) -> Tuple[bool, Optional[BatedeiraIndustrial], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final_tentativa = fim

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {quantidade}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        batedeiras_ordenadas = self._ordenar_por_fip(atividade)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for batedeira in batedeiras_ordenadas:
                if (
                    batedeira.validar_capacidade(quantidade)
                    and batedeira.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    ocupacao_id = self.gerador_ocupacao_id.gerar_id()

                    sucesso = batedeira.ocupar(
                        ocupacao_id=ocupacao_id,
                        quantidade_gramas=quantidade,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        atividade_id=atividade.id
                    )
                    if sucesso:
                        atividade.equipamentos_selecionados.append(batedeira)
                        atividade.inicio_planejado = horario_inicio_tentativa
                        atividade.fim_planejado = horario_final_tentativa
                        atividade.alocada = True

                        logger.info(
                            f"✅ Atividade {atividade.id} alocada na batedeira {batedeira.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        return True, batedeira, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma batedeira "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for batedeira in self.batedeiras:
            batedeira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for batedeira in self.batedeiras:
            batedeira.ocupacoes.clear()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Batedeiras")
        logger.info("==============================================")
        for batedeira in self.batedeiras:
            batedeira.mostrar_agenda()

    # ==========================================================
    # 🔍 Consulta
    # ==========================================================
    def obter_batedeira_por_id(self, id: int) -> Optional[BatedeiraIndustrial]:
        for batedeira in self.batedeiras:
            if batedeira.id == id:
                return batedeira
        return None
