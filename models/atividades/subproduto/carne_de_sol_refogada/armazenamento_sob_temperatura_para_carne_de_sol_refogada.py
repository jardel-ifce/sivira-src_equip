from models.atividade_base import Atividade
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


logger = setup_logger('AtividadeArmazenamentoCarneDeSol')


class ArmazenamentoSobTemperaturaParaCarneDeSolRefogada(Atividade):
    """
    🧊 Atividade de armazenamento da carne de sol refogada em câmara refrigerada.
    ✅ Ocupação feita em caixas de 30kg (20.000g por caixa).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "CAIXAS"

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: 1,
        }

    def calcular_duracao(self):
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=3)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=5)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=7)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para armazenamento sob temperatura."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para armazenamento da carne de sol refogada."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de carne de sol refogada."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_refrigeracao,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        temperatura_desejada: int
    ) -> bool:
        """
        ❄️ Realiza backward scheduling com controle de temperatura e espaço físico.
        ✔️ Tenta retroceder se falhar tanto por ocupação quanto por temperatura.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar armazenamento ID {self.id} "
            f"(quantidade: {self.quantidade_produto}g, duração: {self.duracao}) "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )

        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_tentativa = horario_final_tentativa - self.duracao

            status, inicio_real, fim_real = gestor_refrigeracao.alocar(
                inicio=horario_inicio_tentativa,
                fim=horario_final_tentativa,
                atividade=self,
                temperatura_desejada=temperatura_desejada
            )

            if status == "SUCESSO":
                self.inicio_real = inicio_real
                self.fim_real = fim_real
                self.equipamento_alocado = gestor_refrigeracao.equipamento
                self.equipamentos_selecionados = [self.equipamento_alocado]
                self.alocada = True

                temperatura_real = self.equipamento_alocado.faixa_temperatura_atual

                logger.info(
                    f"✅ Atividade {self.id} alocada com sucesso na {self.equipamento_alocado.nome}.\n"
                    f"🧊 Período: {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
                    f"| Temperatura: {temperatura_real}°C."
                )
                print(
                    f"✅ Atividade {self.id} alocada na {self.equipamento_alocado.nome} "
                    f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
                    f"com temperatura {temperatura_real}°C."
                )
                return True

            else:
                motivo = "temperatura incompatível" if status == "ERRO_TEMPERATURA" else "ocupação indisponível"
                logger.warning(
                    f"⚠️ Falha ({motivo}) para alocar atividade {self.id} no intervalo "
                    f"{horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}. "
                    f"Tentando retroceder..."
                )
                horario_final_tentativa -= timedelta(minutes=5)

        logger.error(
            f"❌ Não foi possível alocar atividade {self.id} "
            f"dentro da janela de {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )
        return False

    def iniciar(self):
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} de armazenamento iniciada na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
