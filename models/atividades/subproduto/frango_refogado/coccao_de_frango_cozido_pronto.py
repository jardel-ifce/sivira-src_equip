from datetime import timedelta
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Coccao_Frango_Cozido_Pronto')


class CoccaoDeFrangoCozidoPronto(Atividade):
    """
    🔥🍗 Atividade que representa a cocção do frango cozido pronto.
    ✅ Utiliza fogões, com alocação baseada na disponibilidade e FIP dos equipamentos.
    """

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
                f"❌ Quantidade {q} fora das faixas válidas para COCCAO DE FRANGO COZIDO PRONTO."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para COCCAO DE FRANGO COZIDO PRONTO."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de frango cozido pronto."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_fogoes,
        inicio_janela,
        horario_limite
    ):
        """
        🔥 Realiza o backward scheduling:
        Aloca o fogão com menor FIP disponível dentro da janela.
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

        self._registrar_sucesso(fogao, inicio_real, fim_real)
        return True

    def _registrar_sucesso(self, fogao, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.fogao_alocado = fogao
        self.equipamento_alocado = fogao
        self.equipamentos_selecionados = [fogao]
        self.alocada = True

        logger.info(
            f"✅ Atividade '{self.id}' alocada com sucesso!\n"
            f"🔥 Fogão: {fogao.nome} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        print(
            f"✅ Atividade {self.id} alocada: Fogão {fogao.nome} ({inicio.strftime('%H:%M')} – {fim.strftime('%H:%M')})."
        )

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
            f"🚀 Cocção do frango cozido pronto iniciada no Fogão {self.fogao_alocado.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"no Fogão {self.fogao_alocado.nome}."
        )
