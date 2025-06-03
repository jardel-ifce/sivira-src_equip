from models.atividade_base import Atividade
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Coccao_Creme_De_Frango')


class CoccaoDeCremeDeFrango(Atividade):
    """
    🔥🍗 Atividade que representa a cocção do creme de frango.
    ✅ Utiliza fogões, ocupando bocas de acordo com a quantidade de produto.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FOGOES: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade conforme a quantidade.
        Faixas:
        - 3000–20000g → 30 minutos
        - 20001–40000g → 60 minutos
        - 40001–60000g → 90 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=30)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=60)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=90)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para cocção de creme de frango."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para cocção de creme de frango."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de creme de frango."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_fogoes,
        inicio_jornada: datetime,
        fim_jornada: datetime
    ) -> bool:
        """
        🔥 Realiza tentativa de alocação utilizando backward scheduling.
        Retrocede se falhar por ocupação.
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

            sucesso, equipamento, inicio_real, fim_real = gestor_fogoes.alocar(
                inicio=horario_inicio_tentativa,
                fim=horario_final_tentativa,
                atividade=self
            )

            if sucesso:
                self._registrar_sucesso(equipamento, inicio_real, fim_real)
                return True

            logger.warning(
                f"⚠️ Falha na alocação do fogão para atividade {self.id} entre "
                f"{horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}. Retrocedendo..."
            )
            horario_final_tentativa -= timedelta(minutes=1)

        logger.error(
            f"❌ Não foi possível alocar atividade {self.id} "
            f"dentro da janela de {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}"
        )
        return False

    def _registrar_sucesso(self, equipamento, inicio_real, fim_real):
        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.fogao_alocado = equipamento
        self.equipamento_alocado = equipamento
        self.equipamentos_selecionados = [equipamento]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso na {equipamento.nome}.\n"
            f"🔥 Período: {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}"
        )
        print(
            f"✅ Atividade {self.id} alocada na {equipamento.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}"
        )

    def iniciar(self):
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} de cocção iniciada na {self.fogao_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada na {self.fogao_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}"
        )
