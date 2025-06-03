from datetime import timedelta, datetime
from models.atividade_base import Atividade
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🍫 Logger específico
logger = setup_logger('Atividade_Preparo_Coccao_de_Massa_para_Bolo_Chocolate')


class PreparoParaCoccaoDeMassaParaBoloDeChocolate(Atividade):
    """
    🍫 Atividade de preparo para cocção da massa de bolo de chocolate.
    ✔️ Equipamentos:
       - 🪵 Bancada (ocupação por frações, exclusiva no tempo por fração).
       - 🗂️ Armário Esqueleto (ocupação por níveis, 1000g = 1 nível).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.niveis_ocupados = None
        self.armario_alocado = None
        self.bancada_alocada = None
        self.fim_bancada_real = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: 1,
        }

    def calcular_duracao(self):
        self.duracao = timedelta(minutes=20)
        logger.info(f"🕒 Duração fixada em 20 minutos para {self.quantidade_produto}g.")

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        gestor_armarios,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        fracoes_necessarias: int = 1
    ) -> bool:
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar atividade {self.id} ({self.quantidade_produto}g) entre "
            f"{inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}"
        )

        # 🔹 Alocar armário primeiro
        status_armario, armario, inicio_armario, fim_armario = gestor_armarios.alocar(
            inicio=inicio_jornada,
            fim=fim_jornada,
            atividade=self
        )

        if status_armario != "SUCESSO":
            logger.warning(
                f"❌ Armário não disponível para atividade {self.id}."
            )
            return False

        # 🔹 Alocar bancada antes do início do armário
        inicio_bancada = inicio_armario - self.duracao
        fim_bancada = inicio_armario

        sucesso_bancada, bancada, i_real, f_real = gestor_bancadas.alocar(
            inicio=inicio_bancada,
            fim=fim_bancada,
            atividade=self,
            fracoes_necessarias=fracoes_necessarias
        )

        if not sucesso_bancada:
            gestor_armarios.liberar_por_atividade(self)
            logger.warning(
                f"❌ Bancada não disponível antes do armário. Liberando armário."
            )
            return False

        self._registrar_sucesso(bancada, armario, i_real, f_real, fim_armario)
        return True

    def _registrar_sucesso(self, bancada, armario, inicio_bancada, fim_bancada, fim_armario):
        self.bancada_alocada = bancada
        self.armario_alocado = armario
        self.equipamento_alocado = [bancada, armario]
        self.equipamentos_selecionados = [bancada, armario]

        self.inicio_real = inicio_bancada
        self.fim_bancada_real = fim_bancada
        self.fim_real = fim_armario
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🪵 Bancada: {bancada.nome} de {inicio_bancada.strftime('%H:%M')} até {fim_bancada.strftime('%H:%M')}\n"
            f"🗂️ Armário: {armario.nome} de {(fim_armario - self.duracao).strftime('%H:%M')} até {fim_armario.strftime('%H:%M')}"
        )

    def iniciar(self):
        if not self.alocada:
            logger.error(f"❌ Atividade {self.id} não alocada.")
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")

        logger.info(
            f"🚀 Atividade {self.id} iniciada na bancada {self.bancada_alocada.nome} às {self.inicio_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')} na bancada {self.bancada_alocada.nome}."
        )
