from datetime import timedelta
from models.atividade_base import Atividade
from models.equips.hot_mix import HotMix
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Mistura_Massas_Para_Frituras')


class MisturaDeMassasParaFrituras(Atividade):
    """
    🍳 Atividade que representa a mistura de massas para frituras.
    ✅ Utiliza HotMix (misturadoras com cocção), com controle de ocupação realizado pelo gestor.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.MISTURADORAS_COM_COCCAO: 1,
        }

    def calcular_duracao(self):
        """
        🕒 Define a duração da atividade com base na quantidade de produto.
        Faixas de tempo:
        - 3000–10000g → 12 minutos
        - 10001–20000g → 16 minutos
        - 20001–30000g → 20 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 10000:
            self.duracao = timedelta(minutes=12)
        elif 10001 <= q <= 20000:
            self.duracao = timedelta(minutes=16)
        elif 20001 <= q <= 30000:
            self.duracao = timedelta(minutes=20)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE MASSAS PARA FRITURAS."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE MASSAS PARA FRITURAS."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de massa para frituras."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_misturadoras,
        inicio_janela,
        horario_limite
    ):
        """
        🚀 Realiza o backward scheduling:
        ✅ Aloca a HotMix se houver disponibilidade.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Iniciando tentativa de alocação da atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g) até {horario_limite.strftime('%H:%M')}."
        )

        sucesso, hotmix, inicio_real, fim_real = gestor_misturadoras.alocar(
            inicio=inicio_janela,
            fim=horario_limite,
            atividade=self
        )

        if not sucesso:
            logger.error(f"❌ Falha na alocação da HotMix para a atividade {self.id}.")
            return False

        # ✅ Registrar alocação
        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.hotmix_alocada = hotmix
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso na HotMix {hotmix.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}."
        )

        return True

    def iniciar(self):
        """
        🟢 Marca oficialmente o início da atividade na HotMix.
        """
        if not self.alocada:
            raise Exception(f"❌ Atividade {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada oficialmente na HotMix {self.hotmix_alocada.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na HotMix {self.hotmix_alocada.nome}."
        )
