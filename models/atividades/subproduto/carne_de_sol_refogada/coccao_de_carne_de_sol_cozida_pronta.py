from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🔥 Logger específico
logger = setup_logger('Atividade_Coccao_Carne_De_Sol')


class CoccaoDeCarneDeSolCozidaPronta(Atividade):
    """
    🔥🥩 Atividade que representa a cocção da carne de sol cozida pronta.
    ✅ Utiliza fogões, ocupando bocas de acordo com a quantidade de produto.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fogao_alocado = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FOGOES: 1,
        }

    def calcular_duracao(self):
        """
        ✅ Duração fixa de 40 minutos, para qualquer quantidade dentro da faixa.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 60000:
            self.duracao = timedelta(minutes=40)
        else:
            logger.error(
                f"❌ Quantidade {q}g fora das faixas válidas para cocção da carne de sol cozida pronta."
            )
            raise ValueError(
                f"❌ Quantidade {q}g fora das faixas válidas para cocção da carne de sol cozida pronta."
            )

        logger.info(
            f"🕒 Duração fixada em {self.duracao} para {q}g de carne de sol cozida pronta."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_fogoes,
        inicio_janela: datetime,
        horario_limite: datetime
    ) -> bool:
        """
        🔥 Realiza o backward scheduling tentando alocar fogão com bocas disponíveis.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} ({self.quantidade_produto}g) "
            f"dentro da janela até {horario_limite.strftime('%H:%M')}."
        )

        sucesso, fogao, i_real, f_real = gestor_fogoes.alocar(
            inicio=inicio_janela,
            fim=horario_limite,
            atividade=self
        )

        if not sucesso:
            logger.error(
                f"❌ Falha na alocação do fogão para atividade {self.id}."
            )
            return False

        self._registrar_sucesso(fogao, i_real, f_real)
        return True

    def _registrar_sucesso(self, fogao, inicio, fim):
        self.fogao_alocado = fogao
        self.equipamento_alocado = fogao
        self.equipamentos_selecionados = [fogao]
        self.inicio_real = inicio
        self.fim_real = fim
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🔥 Fogão: {fogao.nome} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}"
        )
        print(
            f"✅ Atividade {self.id} alocada de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"no Fogão {fogao.nome}."
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
            f"🚀 Cocção da carne de sol cozida pronta iniciada no Fogão {self.fogao_alocado.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"no Fogão {self.fogao_alocado.nome}."
        )
