from datetime import timedelta
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para essa atividade
logger = setup_logger('Atividade_Descanso_Massas_Folhados')


class DescansoDeMassasParaFolhados(Atividade):
    """
    ❄️ Atividade de descanso de massas para folhados.
    ✅ Utiliza câmara refrigerada ou freezer, ocupando caixas de 30kg.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "CAIXAS"

    @property
    def quantidade_por_tipo_equipamento(self):
        """
        Define os tipos de equipamentos necessários.
        """
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração fixa de 1 hora para qualquer quantidade.
        """
        self.duracao = timedelta(hours=1)
        logger.info(f"🕒 Duração definida para descanso: {self.duracao}.")

    def tentar_alocar_e_iniciar(
        self,
        gestor_refrigeracao,
        inicio_jornada,
        fim_jornada,
    ):
        """
        🔥 Realiza o backward scheduling:
        1️⃣ Aloca o equipamento (freezer ou câmara) considerando ocupação por caixas.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar descanso ID {self.id} "
            f"(quantidade: {self.quantidade_produto}g) até {fim_jornada.strftime('%H:%M')}."
        )

        sucesso, inicio_real, fim_real = gestor_refrigeracao.alocar(
            inicio=inicio_jornada,
            fim=fim_jornada,
            atividade=self
        )

        if not sucesso:
            logger.error(
                f"❌ Falha na alocação do descanso ID {self.id} na janela entre "
                f"{inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
            )
            return False

        # ✅ Registrar alocação
        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.equipamento_alocado = gestor_refrigeracao.equipamento
        self.alocada = True

        logger.info(
            f"✅ Descanso ID {self.id} alocado com sucesso na {self.equipamento_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )

        return True

    def iniciar(self):
        """
        🟢 Marca o início da atividade de descanso.
        """
        if not self.alocada:
            logger.error(f"❌ Atividade ID {self.id} não está alocada ainda.")
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Descanso ID {self.id} ({self.descricao}) iniciado oficialmente na "
            f"{self.equipamento_alocado.nome} às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Descanso ID {self.id} ({self.descricao}) iniciado às {self.inicio_real.strftime('%H:%M')} "
            f"na {self.equipamento_alocado.nome}."
        )
