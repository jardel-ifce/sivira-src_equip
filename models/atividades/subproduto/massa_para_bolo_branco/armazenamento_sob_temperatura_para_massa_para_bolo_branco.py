from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger
from datetime import timedelta, datetime


# 🔥 Logger específico
logger = setup_logger('AtividadeArmazenamentoMassaDeBoloBranco')


class ArmazenamentoSobTemperaturaParaMassaDeBoloBranco(Atividade):
    """
    🎂 Atividade de armazenamento da massa de bolo branco em câmara refrigerada a 4°C.
    ✅ Ocupação por níveis de tela (1000g = 1 nível).
    ✅ Conversão feita pela própria câmara.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "NIVEIS_TELA"

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
        Duração variável conforme a quantidade:
        - 3000–6000g → 3 minutos
        - 6001–13000g → 5 minutos
        - 13001–20000g → 7 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 6000:
            self.duracao = timedelta(minutes=3)
        elif 6001 <= q <= 13000:
            self.duracao = timedelta(minutes=5)
        elif 13001 <= q <= 20000:
            self.duracao = timedelta(minutes=7)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para armazenamento da massa de bolo branco."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para armazenamento da massa de bolo branco."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de massa de bolo branco."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_refrigeracao,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        temperatura_desejada: int = 4
    ) -> bool:
        """
        ❄️ Tenta alocar utilizando backward scheduling.
        ✔️ Faz retrocesso se necessário.
        ✔️ Verifica ocupação e temperatura.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} "
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
                    f"🧊 Período: {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
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
        A câmara faz a conversão de gramas para níveis de tela.
        """
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Armazenamento iniciado na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
            f"com temperatura 4°C."
        )
        print(
            f"🚀 Atividade {self.id} iniciada na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
            f"com temperatura 4°C."
        )
