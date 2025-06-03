from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🔥 Logger específico para esta atividade
logger = setup_logger('AtividadeCoccaoCremeDeCamarao')


class CoccaoDeCremeDeCamarao(Atividade):
    """
    🔥🦐 Atividade que representa a cocção do creme de camarão.
    ✅ Utiliza fogões, ocupando bocas de acordo com a quantidade de produto.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FOGOES: 1,
        }

    def calcular_duracao(self):
        """
        📏 Calcula a duração com base na quantidade de produto.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=10)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=20)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=30)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para cocção do creme de camarão."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para cocção do creme de camarão."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de creme de camarão."
        )

    def tentar_alocar_e_iniciar(self, gestor_fogoes, inicio_janela: datetime, horario_limite: datetime) -> bool:
        """
        🔥 Realiza backward scheduling com verificação de disponibilidade de bocas.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar cocção ID {self.id} "
            f"(quantidade: {self.quantidade_produto}g | duração: {self.duracao}) "
            f"com deadline até {horario_limite.strftime('%H:%M')}.")

        sucesso, fogao, inicio_real, fim_real = gestor_fogoes.alocar(
            inicio=inicio_janela,
            fim=horario_limite,
            atividade=self
        )

        if not sucesso:
            logger.error(f"❌ Falha na alocação do fogão para a atividade {self.id}.")
            return False

        self._registrar_sucesso(fogao, inicio_real, fim_real)
        return True

    def _registrar_sucesso(self, fogao, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.fogao_alocado = fogao
        self.equipamentos_selecionados = [fogao]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada no fogão {fogao.nome} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        print(
            f"✅ Atividade {self.id} alocada no fogão {fogao.nome} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )

    def iniciar(self):
        """
        🟢 Marca o início da atividade de cocção.
        """
        if not self.alocada:
            logger.error(
                f"❌ Atividade {self.id} não alocada ainda. Não é possível iniciar."
            )
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Cocção do creme de camarão iniciada no fogão {self.fogao_alocado.nome} "
            f"às {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}"
        )
        print(
            f"🚀 Atividade {self.id} iniciada no fogão {self.fogao_alocado.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}"
        )
