from datetime import timedelta
from models.atividade_base import Atividade
from models.equips.bancada import Bancada
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Laminacao1_Massas_Folhados')


class Laminacao2DeMassasParaFolhados(Atividade):
    """
    🪵 Primeira etapa de laminação de massas para folhados.
    ✅ Utiliza bancadas, com controle de ocupação por frações proporcionais.
    ✔️ Sempre ocupa 4 porções da bancada, independentemente se ela é 4/4 ou 4/6.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
        }

    def calcular_duracao(self):
        """
        🕒 Define a duração da atividade com base na quantidade de produto.
        Faixas de tempo:
        - 3000–17000g → 10 minutos
        - 17001–34000g → 15 minutos
        - 34001–50000g → 18 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 17000:
            self.duracao = timedelta(minutes=10)
        elif 17001 <= q <= 34000:
            self.duracao = timedelta(minutes=15)
        elif 34001 <= q <= 50000:
            self.duracao = timedelta(minutes=18)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para LAMINAÇÃO 1 DE MASSAS PARA FOLHADOS."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para LAMINAÇÃO 1 DE MASSAS PARA FOLHADOS."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de massa para folhados."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        inicio_jornada,
        fim_jornada,
        porcoes: int = 4  # <-- Sempre ocupa 4 porções da bancada
    ):
        """
        🚀 Realiza o backward scheduling:
        ✅ Aloca a bancada se houver disponibilidade.
        ✔️ Usa 4 porções proporcional à capacidade da bancada (4/4 ou 4/6).
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Iniciando tentativa de alocação da atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g) até {fim_jornada.strftime('%H:%M')}."
        )

        sucesso, bancada, inicio_real, fim_real = gestor_bancadas.alocar(
            inicio=inicio_jornada,
            fim=fim_jornada,
            atividade=self,
            porcoes=porcoes
        )

        if not sucesso:
            logger.warning(
                f"❌ Falha na alocação da bancada para a atividade {self.id} "
                f"dentro da jornada até {fim_jornada.strftime('%H:%M')}."
            )
            return False

        # ✅ Registrar alocação
        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.bancada_alocada = bancada
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada e iniciada na bancada {bancada.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
            f"ocupando {porcoes}/{bancada.capacidade_total.denominator} da bancada."
        )
        return True

    def iniciar(self):
        """
        🟢 Marca oficialmente o início da atividade na bancada alocada.
        """
        if not self.alocada:
            raise Exception(f"❌ Atividade {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada oficialmente na bancada {self.bancada_alocada.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na bancada {self.bancada_alocada.nome}."
        )
