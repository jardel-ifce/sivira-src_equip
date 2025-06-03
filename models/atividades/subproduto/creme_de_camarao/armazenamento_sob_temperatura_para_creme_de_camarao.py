from models.atividade_base import Atividade
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🧊 Logger específico
logger = setup_logger('AtividadeArmazenamentoCremeDeCamarao')


class ArmazenamentoSobTemperaturaParaCremeDeCamarao(Atividade):
    """
    🧊 Atividade de armazenamento do creme de camarão em câmara refrigerada.
    ✅ Ocupação feita em caixas de 30kg (20.000g por caixa).
    ✅ Controle rigoroso de temperatura por janela de tempo.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "CAIXAS"
        self.equipamento_alocado = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: 1,
        }

    def calcular_duracao(self):
        """
        📏 Calcula a duração com base na faixa de quantidade.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=3)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=5)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=7)
        else:
            logger.error(f"❌ Quantidade {q} fora da faixa válida para armazenamento.")
            raise ValueError(
                f"❌ Quantidade {q} fora da faixa válida para armazenamento do creme de camarão."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de creme de camarão."
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
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar armazenamento ID {self.id} "
            f"(quantidade: {self.quantidade_produto}g | duração: {self.duracao}) "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )

        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_tentativa = horario_final_tentativa - self.duracao

            status, equipamento, i_real, f_real = gestor_refrigeracao.alocar(
                inicio=horario_inicio_tentativa,
                fim=horario_final_tentativa,
                atividade=self,
                temperatura_desejada=temperatura_desejada
            )

            if status == "SUCESSO":
                self._registrar_sucesso(equipamento, i_real, f_real)
                return True

            motivo = "temperatura incompatível" if status == "ERRO_TEMPERATURA" else "ocupação indisponível"
            logger.warning(
                f"⚠️ Falha ({motivo}) para alocar atividade {self.id} no intervalo "
                f"{horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}. "
                f"Tentando retroceder..."
            )

            horario_final_tentativa -= timedelta(minutes=1)

        logger.error(
            f"❌ Não foi possível alocar atividade {self.id} "
            f"dentro da janela de {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )
        return False

    def _registrar_sucesso(self, equipamento, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.equipamento_alocado = equipamento
        self.equipamentos_selecionados = [equipamento]
        self.alocada = True

        temperatura_real = equipamento.faixa_temperatura_atual

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso na {equipamento.nome}.\n"
            f"🧊 Período: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"| Temperatura: {temperatura_real}°C."
        )
        print(
            f"✅ Atividade {self.id} alocada na {equipamento.nome} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"com temperatura {temperatura_real}°C."
        )

    def iniciar(self):
        """
        ✅ Inicia oficialmente a atividade de armazenamento.
        """
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
