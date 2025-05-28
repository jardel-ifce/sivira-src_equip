from datetime import timedelta
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Coccao_Creme_De_Queijo')


class CoccaoDeCremeDeQueijo(Atividade):
    """
    🔥🧀 Atividade que representa a cocção do creme de queijo.
    ✅ Utiliza fogões, ocupando bocas de acordo com a quantidade de produto.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FOGOES: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade conforme a quantidade produzida.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=15)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=30)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=45)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para COCCAO DE CREME DE QUEIJO."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para COCCAO DE CREME DE QUEIJO."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de creme de queijo."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_fogoes,
        inicio_janela,
        horario_limite
    ):
        """
        Realiza o backward scheduling:
        🔥 Aloca o fogão se houver bocas disponíveis.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Iniciando tentativa de alocação da atividade '{self.id}' "
            f"(quantidade: {self.quantidade_produto}g) com deadline até {horario_limite.strftime('%H:%M')}."
        )

        sucesso, fogao, inicio_real, fim_real = gestor_fogoes.alocar(
            inicio=inicio_janela,
            fim=horario_limite,
            atividade=self
        )

        if not sucesso:
            logger.error(f"❌ Falha na alocação do fogão para a atividade '{self.id}'.")
            return False

        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.fogao_alocado = fogao
        self.alocada = True

        logger.info(
            f"✅ Atividade '{self.id}' alocada com sucesso!\n"
            f"🔥 Fogão: {fogao.nome} de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}"
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
            raise Exception("❌ Atividade não alocada ainda.")

        logger.info(
            f"🚀 Cocção do creme de queijo iniciada no Fogão {self.fogao_alocado.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"no Fogão {self.fogao_alocado.nome}."
        )
