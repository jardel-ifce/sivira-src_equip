from datetime import timedelta
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Mistura_Massas_Crocantes')


class MisturaDeMassasCrocantes(Atividade):
    """
    🌀 Atividade que representa a mistura de massas crocantes.
    ✅ Utiliza masseiras (misturadoras), com controle de ocupação realizado pelo gestor.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.masseira_alocada = None
        self.ocupacao_id = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.MISTURADORAS: 1,
        }

    def calcular_duracao(self):
        """
        🕒 Define a duração da atividade com base na quantidade de produto.
        Faixas de tempo:
        - 3000–17000g → 7 minutos
        - 17001–34000g → 11 minutos
        - 34001–50000g → 15 minutos
        """
        q = self.quantidade_produto

        if 3000 <= q <= 17000:
            self.duracao = timedelta(minutes=7)
        elif 17001 <= q <= 34000:
            self.duracao = timedelta(minutes=11)
        elif 34001 <= q <= 50000:
            self.duracao = timedelta(minutes=15)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE MASSAS CROCANTES."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE MASSAS CROCANTES."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de massa crocante."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_misturadoras,
        inicio_janela,
        horario_limite
    ):
        """
        🚀 Realiza o backward scheduling:
        ✅ Aloca a masseira se houver disponibilidade.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Iniciando tentativa de alocação da atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g) até {horario_limite.strftime('%H:%M')}."
        )

        sucesso, masseira, inicio_real, fim_real = gestor_misturadoras.alocar(
            inicio=inicio_janela,
            fim=horario_limite,
            atividade=self,
            quantidade=self.quantidade_produto
        )

        if not sucesso:
            logger.error(f"❌ Falha na alocação da masseira para a atividade {self.id}.")
            return False

        # ✅ Registrar alocação
        self._registrar_sucesso(
            masseira=masseira,
            inicio=inicio_real,
            fim=fim_real
        )

        return True

    def _registrar_sucesso(self, masseira, inicio, fim):
        """
        ✅ Atualiza os atributos da atividade com sucesso de alocação.
        """
        self.inicio_real = inicio
        self.fim_real = fim
        self.inicio_planejado = inicio
        self.fim_planejado = fim
        self.alocada = True
        self.masseira_alocada = masseira
        self.equipamentos_selecionados.append(masseira)

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso na masseira {masseira.nome} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )

    def iniciar(self):
        """
        🟢 Marca oficialmente o início da atividade.
        """
        if not self.alocada or not self.masseira_alocada:
            raise Exception(f"❌ Atividade {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada oficialmente na masseira {self.masseira_alocada.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na masseira {self.masseira_alocada.nome}."
        )
