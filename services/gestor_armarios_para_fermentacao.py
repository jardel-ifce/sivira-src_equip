from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union
from models.equips.armario_esqueleto import ArmarioEsqueleto
from models.equips.armario_fermentador import ArmarioFermentador
from models.atividade_base import Atividade
from utils.conversores_ocupacao import gramas_para_niveis_tela
from utils.logger_factory import setup_logger

# 🔳 Logger exclusivo do gestor de Armários Esqueleto
logger = setup_logger('GestorArmariosParaFermentacao')

Armarios = Union[ArmarioEsqueleto, ArmarioFermentador]


class GestorArmariosParaFermentacao:
    """
    🔳 Gestor especializado no controle de Armários para Fermentação (tipo Esqueleto).
    Utiliza backward scheduling e FIP.
    """

    def __init__(self, armarios: List[Armarios]):
        self.armarios = armarios

    def _ordenar_por_fip(self, atividade: Atividade) -> List[Armarios]:
        ordenadas = sorted(
            self.armarios,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        logger.info("📊 Ordem dos armários esqueleto por FIP (prioridade):")
        for m in ordenadas:
            fip = atividade.fips_equipamentos.get(m, 999)
            logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade_gramas: int
    ) -> Tuple[bool, Optional[ArmarioEsqueleto], Optional[datetime], Optional[datetime]]:
        """
        🔳 Faz a alocação utilizando backward scheduling por FIP.
        Converte a quantidade de gramas para níveis de tela automaticamente.
        Retorna (True, equipamento, inicio_real, fim_real) se sucesso.
        Caso contrário: (False, None, None, None)
        """
        duracao = atividade.duracao
        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim

        logger.info(
            f"🌟 Tentando alocar atividade {atividade.id} ({quantidade_gramas}g | {duracao}) entre "
            f"{inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}"
        )
        niveis_necessarios = gramas_para_niveis_tela(quantidade_gramas)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for armario in equipamentos_ordenados:
                if not armario.verificar_espaco_niveis(niveis_necessarios, horario_inicio_tentativa, horario_final_tentativa):
                    continue

                sucesso = armario.ocupar_niveis(
                    atividade_id=atividade.id,
                    quantidade=niveis_necessarios,
                    inicio=horario_inicio_tentativa,
                    fim=horario_final_tentativa
                )

                if sucesso:
                    atividade.equipamento_alocado = armario
                    atividade.equipamentos_selecionados = [armario]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {atividade.id} alocada no armário {armario.nome} | "
                        f"{horario_inicio_tentativa.strftime('%H:%M')} → {horario_final_tentativa.strftime('%H:%M')} | "
                        f"{niveis_necessarios} níveis"
                    )
                    return True, armario, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id} não alocada entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}"
        )
        return False, None, None, None

    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: Atividade) -> None:
        logger.info(f"🧹 Liberando níveis da atividade {atividade.id} em todos os armários.")
        for armario in self.armarios:
            armario.liberar_por_atividade(atividade.id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        logger.info(f"🔄 Liberando ocupações finalizadas até {horario_atual.strftime('%H:%M')}.")
        for armario in self.armarios:
            armario.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self) -> None:
        logger.info("🧼 Liberando todas as ocupações de todos os armários.")
        for armario in self.armarios:
            armario.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self) -> None:
        logger.info("==============================================")
        logger.info("📅 Agenda dos Armários para Fermentação")
        logger.info("==============================================")
        for armario in self.armarios:
            armario.mostrar_agenda()
