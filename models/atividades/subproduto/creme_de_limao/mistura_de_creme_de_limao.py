from datetime import timedelta
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


logger = setup_logger('Atividade_Mistura_Creme_De_Limao')


class MisturaDeCremeDeLimao(Atividade):
    """
    🍋 Atividade que representa a mistura de creme de limão.
    ✅ Utiliza bancada com ocupação fracionada (1/4 ou 1/6).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade com base na quantidade de produto.
        Faixas oficiais:
        - 3000–10000g  → 5 minutos
        - 10001–20000g → 10 minutos
        - 20001–30000g → 15 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 10000:
            self.duracao = timedelta(minutes=5)
        elif 10001 <= q <= 20000:
            self.duracao = timedelta(minutes=10)
        elif 20001 <= q <= 30000:
            self.duracao = timedelta(minutes=15)
        else:
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE CREME DE LIMÃO."
            )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        inicio_janela,
        horario_limite,
        fracao_bancada: tuple = (1, 4)  # ✅ Default 1/4, ajustável
    ):
        """
        🔥 Faz o backward scheduling apenas para bancada.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade ID {self.id} "
            f"(quantidade: {self.quantidade_produto}g) até {horario_limite.strftime('%H:%M')}."
        )

        sucesso, bancada, inicio_real, fim_real = gestor_bancadas.alocar(
            inicio=inicio_janela,
            fim=horario_limite,
            atividade=self,
            fracao=fracao_bancada
        )

        if not sucesso:
            logger.error(f"❌ Falha na alocação da bancada para a atividade ID {self.id}.")
            return False

        # ✅ Registrar
        self.inicio_real = inicio_real
        self.fim_real = fim_real
        self.bancada_alocada = bancada
        
        self.alocada = True

        logger.info(
            f"✅ Atividade ID {self.id} alocada com sucesso na bancada {bancada.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}."
        )

        return True

    def iniciar(self):
        """
        🟢 Marca o início da atividade.
        """
        if not self.alocada:
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade ID {self.id} iniciada oficialmente na bancada {self.bancada_alocada.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade ID {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na bancada {self.bancada_alocada.nome}."
        )
