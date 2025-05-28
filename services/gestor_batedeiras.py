from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from models.equips.batedeira_planetaria import BatedeiraPlanetaria
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger


logger = setup_logger('GestorBatedeiras')


class GestorBatedeiras:
    def __init__(self, batedeiras: List[BatedeiraPlanetaria]):
        self.batedeiras = batedeiras

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade: float
    ) -> Tuple[bool, Optional[BatedeiraPlanetaria], Optional[datetime], Optional[datetime]]:
        
        duracao = atividade.duracao
        horario_final_tentativa = fim

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {quantidade}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for batedeira in sorted(
                self.batedeiras,
                key=lambda b: atividade.fips_equipamentos.get(b, 999)
            ):
                if (
                    batedeira.validar_capacidade(quantidade)
                    and batedeira.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    sucesso = batedeira.ocupar(
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
                            f"✅ Atividade {atividade.id} alocada na {batedeira.nome} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        return True, batedeira, horario_inicio_tentativa, horario_final_tentativa

            # 🕑 Retrocede no tempo só depois de testar todas as batedeiras no horário atual
            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma batedeira "
            f"dentro da janela até {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for batedeira in self.batedeiras:
            batedeira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for batedeira in self.batedeiras:
            batedeira.ocupacoes.clear()

    def mostrar_agenda(self):
        logger.info("\n========================")
        logger.info("📅 Agenda das Batedeiras")
        logger.info("========================")
        for batedeira in self.batedeiras:
            batedeira.mostrar_agenda()

    def obter_batedeira_por_id(self, id: int) -> Optional[BatedeiraPlanetaria]:
        for batedeira in self.batedeiras:
            if batedeira.id == id:
                return batedeira
        return None
