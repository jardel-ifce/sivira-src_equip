from datetime import timedelta
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para essa atividade
logger = setup_logger('Atividade_Preparo_Coccao_Frango_Cozido')


class PreparoParaCoccaoDeFrangoCozidoPronto(Atividade):
    """
    🍳 Atividade de preparo para cocção de frango cozido pronto.
    ✅ Equipamento:
    - Bancada (ocupação fracionada, permite sobreposição).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        """
        Define os tipos de equipamentos necessários.
        """
        return {
            TipoEquipamento.BANCADAS: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade baseada na quantidade produzida.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=8)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=16)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=24)
        else:
            raise ValueError(f"❌ Quantidade {q} inválida para esta atividade.")

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        inicio_jornada,
        fim_jornada,
        porcoes_bancada: int = 2  # 🔥 Número de porções da bancada
    ):
        """
        🔥 Realiza o backward scheduling para bancada.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Iniciando tentativa de alocação da atividade '{self.id}' "
            f"(quantidade: {self.quantidade_produto}g) até {fim_jornada.strftime('%H:%M')}."
        )

        # 🔹 Calcular janela backward
        fim = fim_jornada
        inicio = fim - self.duracao

        sucesso, bancada, inicio_real, fim_real = gestor_bancadas.alocar(
            inicio=inicio,
            fim=fim,
            atividade=self,
            porcoes=porcoes_bancada
        )

        if not sucesso:
            logger.error(
                f"❌ Falha na alocação da bancada para a atividade '{self.id}'."
            )
            return False

        # ✅ Registrar alocação
        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.bancada_alocada = bancada
        self.alocada = True

        logger.info(
            f"✅ Atividade '{self.id}' alocada com sucesso!\n"
            f"🪵 Bancada: {bancada.nome} de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}"
        )

        return True

    def iniciar(self):
        """
        🟢 Marca o início da atividade.
        """
        logger.info(
            f"🚀 Atividade {self.id} foi iniciada oficialmente "
            f"no horário {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')}."
        )
