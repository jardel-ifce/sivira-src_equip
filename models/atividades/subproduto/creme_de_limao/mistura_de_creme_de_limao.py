from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🍋 Logger específico para esta atividade
logger = setup_logger('Atividade_Mistura_Creme_De_Limao')


class MisturaDeCremeDeLimao(Atividade):
    """
    🍋 Atividade que representa a mistura de creme de limão.
    ✅ Utiliza bancada com ocupação fracionada (1/4 ou 1/6).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
        }

    def calcular_duracao(self):
        """
        📏 Define a duração da atividade baseada na quantidade de produto.
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
            logger.error(f"❌ Quantidade {q} fora das faixas válidas para mistura de creme de limão.")
            raise ValueError(f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE CREME DE LIMÃO.")

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de creme de limão."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        fracoes_necessarias: int = 1
    ) -> bool:
        """
        🛋️ Realiza o backward scheduling apenas para bancada com controle de ocupação por fração.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g, duração: {self.duracao}) "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}"
        )

        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_tentativa = horario_final_tentativa - self.duracao

            sucesso, bancada, inicio_real, fim_real = gestor_bancadas.alocar(
                inicio=horario_inicio_tentativa,
                fim=horario_final_tentativa,
                atividade=self,
                fracoes_necessarias=fracoes_necessarias
            )

            if sucesso:
                self._registrar_sucesso(bancada, inicio_real, fim_real)
                return True

            logger.warning(
                f"⚠️ Falha na alocação da bancada para a atividade {self.id} entre "
                f"{horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}. Retrocedendo..."
            )
            horario_final_tentativa -= timedelta(minutes=1)

        logger.error(f"❌ Não foi possível alocar a atividade {self.id} na janela definida.")
        return False

    def _registrar_sucesso(self, bancada, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.bancada_alocada = bancada
        self.equipamento_alocado = bancada
        self.equipamentos_selecionados = [bancada]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso na bancada {bancada.nome} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}"
        )
        print(
            f"✅ Atividade {self.id} alocada: Bancada {bancada.nome} ({inicio.strftime('%H:%M')}–{fim.strftime('%H:%M')})"
        )

    def iniciar(self):
        """
        🟢 Marca o início da atividade.
        """
        if not self.alocada:
            logger.error(f"❌ Atividade {self.id} não alocada ainda.")
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada oficialmente na bancada {self.bancada_alocada.nome} "
            f"às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} "
            f"na bancada {self.bancada_alocada.nome}."
        )
