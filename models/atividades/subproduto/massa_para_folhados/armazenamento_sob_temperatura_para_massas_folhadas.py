from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger


# 🔥 Logger específico para essa atividade
logger = setup_logger('Atividade_Armazenamento_Massas_Folhadas')


class ArmazenamentoSobTemperaturaParaMassasFolhadas(Atividade):
    """
    🥐❄️ Atividade de armazenamento das massas folhadas em câmara refrigerada ou freezer a -18°C.
    ✅ Ocupação feita em caixas de 30kg (20.000g por caixa).
    ✅ Controle de temperatura e ocupação.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "CAIXAS"

    @property
    def quantidade_por_tipo_equipamento(self):
        """
        Define o tipo de equipamento necessário.
        """
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: 1,
        }

    def calcular_duracao(self):
        """
        Duração conforme a quantidade:
        - 3000–17000g → 3 minutos
        - 17001–34000g → 4 minutos
        - 34001–50000g → 5 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 17000:
            self.duracao = timedelta(minutes=3)
        elif 17001 <= q <= 34000:
            self.duracao = timedelta(minutes=4)
        elif 34001 <= q <= 50000:
            self.duracao = timedelta(minutes=5)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para armazenamento de massas folhadas."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para armazenamento de massas folhadas."
            )

        logger.info(
            f"🕒 Duração definida: {self.duracao} para {q}g de massas folhadas."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_refrigeracao,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        temperatura_desejada: int = -18
    ) -> bool:
        """
        ❄️ Faz a tentativa de alocação utilizando backward scheduling.
        ✔️ Retrocede em blocos de 5 minutos se não encontrar janela.
        ✔️ Verifica disponibilidade de ocupação e temperatura.
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

                logger.info(
                    f"✅ Atividade {self.id} alocada na {self.equipamento_alocado.nome}.\n"
                    f"🧊 De {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
                    f"| Temperatura: {temperatura_desejada}°C."
                )
                print(
                    f"✅ Atividade {self.id} alocada na {self.equipamento_alocado.nome} "
                    f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
                    f"com temperatura {temperatura_desejada}°C."
                )
                return True

            else:
                motivo = (
                    "temperatura incompatível"
                    if status == "ERRO_TEMPERATURA"
                    else "ocupação indisponível"
                )
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
        """
        🟢 Inicia oficialmente a atividade de armazenamento.
        """
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        sucesso = self.equipamento_alocado.ocupar_por_caixa(self.quantidade_produto)

        if not sucesso:
            raise Exception(
                f"❌ Falha ao ocupar caixas na {self.equipamento_alocado.nome} "
                f"para {self.quantidade_produto}g de massas folhadas."
            )

        temperatura_ok = self.equipamento_alocado.selecionar_faixa_temperatura(-18)

        if not temperatura_ok:
            raise Exception(
                f"❌ Não foi possível ajustar a temperatura da {self.equipamento_alocado.nome} para -18°C."
            )

        logger.info(
            f"🚀 Armazenamento iniciado na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
            f"com temperatura -18°C."
        )
