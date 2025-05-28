from datetime import timedelta
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para essa atividade
logger = setup_logger('Atividade_Preparo_Coccao_Carne_Sol')


class PreparoParaCoccaoDeCarneDeSolRefogada(Atividade):
    """
    🍳 Atividade que representa o preparo para cocção de carne de sol refogada.
    ✅ Utiliza bancada (ocupação por frações, EXCLUSIVA no tempo por fração).
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
            raise ValueError(
                f"❌ Quantidade {q} inválida para esta atividade."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de carne de sol refogada."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        inicio_jornada,
        fim_jornada,
        fracoes_necessarias: int = 1  # 🪵 Número de frações que ocupará na bancada
    ):
        """
        🪵 Realiza o backward scheduling para bancada.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Iniciando tentativa de alocação da atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g, duração: {self.duracao}) "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )

        sucesso, bancada, inicio_real, fim_real = gestor_bancadas.alocar(
            inicio=inicio_jornada,
            fim=fim_jornada,
            atividade=self,
            fracoes_necessarias=fracoes_necessarias
        )

        if not sucesso:
            logger.error(
                f"❌ Falha na alocação da bancada para a atividade {self.id}."
            )
            return False

        # ✅ Registrar alocação
        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.bancada_alocada = bancada
        self.equipamento_alocado = bancada
        self.equipamentos_selecionados = [bancada]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🪵 Bancada: {bancada.nome} de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}."
        )

        return True

    def iniciar(self):
        """
        🟢 Marca o início da atividade.
        """
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} foi iniciada oficialmente "
            f"na bancada {self.bancada_alocada.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na bancada {self.bancada_alocada.nome}."
        )
