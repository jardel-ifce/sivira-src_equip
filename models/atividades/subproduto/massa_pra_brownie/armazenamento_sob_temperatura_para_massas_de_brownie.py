from enums.tipo_equipamento import TipoEquipamento
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger
from datetime import timedelta, datetime


# 🔥 Logger específico
logger = setup_logger('AtividadeArmazenamentoMassaBrownie')


class ArmazenamentoSobTemperaturaParaMassasDeBrownie(Atividade):
    """
    🍫 Atividade de armazenamento das massas de brownie em câmara refrigerada a 4°C.
    ✅ Ocupação por níveis de tela (1000g = 1 nível).
    ✅ Conversão e controle de ocupação feitos pela própria câmara.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "NIVEIS_DE_TELA"

    @property
    def quantidade_por_tipo_equipamento(self):
        """
        Define o tipo de equipamento necessário para esta atividade.
        """
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: 1,
        }

    def calcular_duracao(self):
        """
        Duração conforme a quantidade:
        - 3000–17000g → 3 minutos
        - 17001–34000g → 5 minutos
        - 34001–50000g → 7 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 17000:
            self.duracao = timedelta(minutes=3)
        elif 17001 <= q <= 34000:
            self.duracao = timedelta(minutes=5)
        elif 34001 <= q <= 50000:
            self.duracao = timedelta(minutes=7)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para armazenamento de massas de brownie."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para armazenamento de massas de brownie."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de massa de brownie."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_refrigeracao,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        temperatura_desejada: int = 4
    ) -> bool:
        """
        ❄️ Faz a tentativa de alocação utilizando backward scheduling.
        ✔️ Retrocede em blocos de 5 minutos até encontrar uma janela válida.
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
        A câmara faz a conversão de gramas para níveis de tela.
        """
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        sucesso = self.equipamento_alocado.ocupar_por_tela(self.quantidade_produto)

        if not sucesso:
            raise Exception(
                f"❌ Falha ao ocupar níveis de tela na {self.equipamento_alocado.nome} "
                f"para {self.quantidade_produto}g de massa de brownie."
            )

        temperatura_ok = self.equipamento_alocado.selecionar_faixa_temperatura(4)

        if not temperatura_ok:
            raise Exception(
                f"❌ Não foi possível ajustar a temperatura da {self.equipamento_alocado.nome} para 4°C."
            )

        logger.info(
            f"🚀 Armazenamento iniciado na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')} "
            f"com temperatura 4°C."
        )
