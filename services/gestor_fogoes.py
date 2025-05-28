from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from models.atividade_base import Atividade
from models.equips.forno import Forno
from utils.logger_factory import setup_logger


logger = setup_logger('GestorFogoes')


class GestorFogoes:
    """
    🔥 Gestor especializado para controle de fogões.
    ✔️ Controle de ocupação por níveis.
    ✔️ Backward Scheduling.
    ✔️ Verificação de temperatura, vaporização e velocidade.
    """

    def __init__(self, fogoes: List[Forno]):
        self.fogoes = fogoes
        self.contador_ocupacao = 1

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade_niveis: int,
        temperatura_desejada: int,
        vaporizacao_desejada: int,
        velocidade_desejada: int,
    ) -> Tuple[bool, Optional[Forno], Optional[datetime], Optional[datetime]]:
        """
        Realiza a alocação usando backward scheduling (do fim para o início).
        Retorna (True, forno, inicio_real, fim_real) se sucesso,
        caso contrário (False, None, None, None).
        """
        duracao = atividade.duracao
        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for forno in sorted(self.fogoes, key=lambda f: f.fator_de_importancia):
                if not forno.verificar_espaco_niveis(quantidade_niveis, horario_inicio_tentativa, horario_final_tentativa):
                    continue

                if not forno.verificar_compatibilidade_temperatura(horario_inicio_tentativa, horario_final_tentativa, temperatura_desejada):
                    continue

                if not forno.verificar_compatibilidade_vaporizacao(horario_inicio_tentativa, horario_final_tentativa, vaporizacao_desejada):
                    continue

                if not forno.verificar_compatibilidade_velocidade(horario_inicio_tentativa, horario_final_tentativa, velocidade_desejada):
                    continue

                # Ajusta parâmetros
                forno.selecionar_temperatura(temperatura_desejada)
                forno.selecionar_vaporizacao(vaporizacao_desejada)
                forno.selecionar_velocidade(velocidade_desejada)

                sucesso = forno.ocupar_niveis(
                    ocupacao_id=self.contador_ocupacao,
                    quantidade=quantidade_niveis,
                    inicio=horario_inicio_tentativa,
                    fim=horario_final_tentativa,
                    atividade_id=atividade.id
                )

                if sucesso:
                    logger.info(
                        f"✅ Ocupação {self.contador_ocupacao} alocada no forno {forno.nome} "
                        f"para atividade {atividade.id} de {horario_inicio_tentativa.strftime('%H:%M')} "
                        f"até {horario_final_tentativa.strftime('%H:%M')}."
                    )
                    self.contador_ocupacao += 1

                    return True, forno, horario_inicio_tentativa, horario_final_tentativa

            # 🔄 Retrocede a tentativa
            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Não foi possível alocar a atividade {atividade.id} "
            f"dentro da janela de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: Atividade):
        for forno in self.fogoes:
            forno.liberar_por_atividade(atividade.id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for forno in self.fogoes:
            forno.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for forno in self.fogoes:
            forno.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Mostrar Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("\n🗓️ AGENDA DOS FORNOS:")
        for forno in self.fogoes:
            forno.mostrar_agenda()
