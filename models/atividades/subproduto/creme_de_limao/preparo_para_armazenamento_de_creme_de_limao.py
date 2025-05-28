from datetime import timedelta
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger


# 🔥 Logger específico para essa atividade
logger = setup_logger('Atividade_Preparo_Armazenamento_Creme_Limao')


class PreparoParaArmazenamentoDeCremeDeLimao(Atividade):
    """
    🍋 Atividade de preparo para armazenamento do creme de limão.
    Equipamentos:
    - Bancada (fracionada, permite sobreposição).
    - Balança (ocupação exclusiva no tempo).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        """
        Define os tipos de equipamentos necessários.
        """
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.BALANCAS: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade baseada na quantidade produzida.
        Faixas oficiais:
        - 3000–10000g  → 3 minutos
        - 10001–20000g → 5 minutos
        - 20001–30000g → 7 minutos
        """
        q = self.quantidade_produto
        if 3000 <= q <= 10000:
            self.duracao = timedelta(minutes=3)
        elif 10001 <= q <= 20000:
            self.duracao = timedelta(minutes=5)
        elif 20001 <= q <= 30000:
            self.duracao = timedelta(minutes=7)
        else:
            raise ValueError(
                f"❌ Quantidade {q} inválida para esta atividade."
            )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        gestor_balancas,
        inicio_jornada,
        fim_jornada,
        porcoes_bancada: int = 2  # 🔥 Número de porções da bancada
    ):
        """
        Realiza o backward scheduling:
        1️⃣ Aloca primeiro a balança (ocupação exclusiva no tempo).
        2️⃣ Depois aloca a bancada (ocupação fracionada e permite sobreposição).
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Iniciando tentativa de alocação da atividade '{self.id}' "
            f"(quantidade: {self.quantidade_produto}g) até {fim_jornada.strftime('%H:%M')}."
        )

        # 🔹 Alocação da balança (ocupação exclusiva no tempo)
        sucesso_balanca, balanca, inicio_balanca, fim_balanca = gestor_balancas.alocar(
            inicio=inicio_jornada,
            fim=fim_jornada,
            atividade=self,
            quantidade=self.quantidade_produto
        )

        if not sucesso_balanca:
            logger.error(f"❌ Falha na alocação da balança para a atividade '{self.id}'.")
            return False

        # 🔹 Calcular janela da bancada (imediatamente antes da balança)
        fim_bancada = inicio_balanca
        inicio_bancada = fim_bancada - self.duracao

        sucesso_bancada, bancada, inicio_bancada_real, fim_bancada_real = gestor_bancadas.alocar(
            inicio=inicio_bancada,
            fim=fim_bancada,
            atividade=self,
            porcoes=porcoes_bancada
        )

        if not sucesso_bancada:
            # 🔥 Rollback da balança
            gestor_balancas.liberar(
                inicio=inicio_balanca,
                fim=fim_balanca,
                atividade_id=self.id
            )
            logger.error(f"❌ Falha na alocação da bancada para a atividade '{self.id}'.")
            return False

        # ✅ Registrar alocação
        self.inicio_real = inicio_bancada_real
        self.fim_real = fim_balanca
        self.bancada_alocada = bancada
        self.balanca_alocada = balanca
        self.alocada = True

        logger.info(
            f"✅ Atividade '{self.id}' alocada com sucesso!\n"
            f"🪵 Bancada: {bancada.nome} de {inicio_bancada_real.strftime('%H:%M')} até {fim_bancada_real.strftime('%H:%M')}\n"
            f"⚖️ Balança: {balanca.nome} de {inicio_balanca.strftime('%H:%M')} até {fim_balanca.strftime('%H:%M')}"
        )

        return True

    def iniciar(self):
        """
        🟢 Marca o início da atividade.
        """
        logger.info(
            f"🚀 Atividade {self.id} ({self.descricao}) foi iniciada oficialmente "
            f"no horário {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} ({self.descricao}) iniciada às {self.inicio_real.strftime('%H:%M')}."
        )
