from models.atividade_base import Atividade
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🦐 Logger específico para esta atividade
logger = setup_logger('Atividade_Preparo_Armazenamento_Creme_Camarao')


class PreparoParaArmazenamentoDeCremeDeCamarao(Atividade):
    """
    🦐 Atividade de preparo para armazenamento do creme de camarão.
    ✔️ Equipamentos:
       - 🪵 Bancada (ocupação por frações, exclusiva no tempo por fração)
       - ⚖️ Balança Digital (registro de uso por peso, uso concorrente)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "CAIXAS"
        self.bancada_alocada = None
        self.balanca_alocada = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.BALANCAS: 1
        }

    def calcular_duracao(self):
        q = self.quantidade_produto

        if q < 3000:
            logger.error(f"❌ Quantidade {q}g inválida para esta atividade.")
            raise ValueError(f"❌ Quantidade {q}g inválida para PreparoParaArmazenamentoDeCremeDeCamarao.")
        elif 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=3)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=5)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=7)
        else:
            logger.error(f"❌ Quantidade {q}g acima do máximo permitido.")
            raise ValueError(f"❌ Quantidade {q}g inválida para PreparoParaArmazenamentoDeCremeDeCamarao.")

        logger.info(f"🕒 Duração calculada: {self.duracao} para {q}g.")
