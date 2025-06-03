from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🐔 Logger específico para esta atividade
logger = setup_logger('Atividade_Preparo_Coccao_Creme_Frango')


class PreparoParaCoccaoDeCremeDeFrango(Atividade):
    """
    🐔🍳 Atividade que representa o preparo para cocção de creme de frango.
    ✅ Utiliza bancada (ocupação por frações, EXCLUSIVA no tempo por fração).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "FRACOES"
        self.bancada_alocada = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
        }

    def calcular_duracao(self):
        """
        📏 Define a duração da atividade baseada na quantidade produzida.
        """
        q = self.quantidade_produto

        if 3000 <= q <= 20000:
            self.duracao = timedelta(minutes=8)
        elif 20001 <= q <= 40000:
            self.duracao = timedelta(minutes=16)
        elif 40001 <= q <= 60000:
            self.duracao = timedelta(minutes=24)
        else:
            logger.error(
                f"❌ Quantidade {q} inválida para esta atividade."
            )
            raise ValueError(
                f"❌ Quantidade {q} inválida para PreparoParaCoccaoDeCremeDeFrango."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de creme de frango."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        inicio_jornada,
        fim_jornada,
        fracoes_necessarias: int = 1
    ) -> bool:
        """
        🪵 Realiza o backward scheduling para bancada com controle de ocupação por ID.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Iniciando tentativa de alocação da atividade {self.id} "
            f"(quantidade: {self.quantidade_produto}g, duração: {self.duracao}) "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
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
                f"❌ Não foi possível alocar bancada para atividade {self.id} "
                f"entre {horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}."
            )
            horario_final_tentativa -= timedelta(minutes=1)

        logger.error(
            f"❌ Não foi possível alocar atividade {self.id} "
            f"dentro da janela {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )
        return False

    def _registrar_sucesso(self, bancada, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.bancada_alocada = bancada
        self.equipamento_alocado = bancada
        self.equipamentos_selecionados = [bancada]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🪵 Bancada: {bancada.nome} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        print(
            f"✅ Atividade {self.id} alocada: Bancada {bancada.nome} ({inicio.strftime('%H:%M')}–{fim.strftime('%H:%M')})."
        )

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
