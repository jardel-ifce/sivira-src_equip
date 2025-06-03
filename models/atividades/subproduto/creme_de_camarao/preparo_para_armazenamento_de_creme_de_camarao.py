from models.atividade_base import Atividade
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🦐 Logger específico para esta atividade
logger = setup_logger('Atividade_Preparo_Armazenamento_Creme_Camarao')


class PreparoParaArmazenamentoDeCremeDeCamarao(Atividade):
    """
    🦐 Atividade de preparo para armazenamento do creme de camarão.
    ✔️ Equipamentos:
       - 🪵 Bancada (ocupação por frações, exclusiva no tempo por fração).
       - ⚖️ Balança Digital (registro de uso por peso, uso concorrente).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "CAIXAS"
        self.bancada_alocada = None
        self.balanca_alocada = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.BALANCAS: 1,
        }

    def calcular_duracao(self):
        self.duracao = self._definir_duracao_por_faixa(self.quantidade_produto)
        logger.info(f"🕒 Duração calculada: {self.duracao} para {self.quantidade_produto}g.")

    def _definir_duracao_por_faixa(self, quantidade):
        if 3000 <= quantidade <= 20000:
            return timedelta(minutes=3)
        elif 20001 <= quantidade <= 40000:
            return timedelta(minutes=5)
        elif 40001 <= quantidade <= 60000:
            return timedelta(minutes=7)
        else:
            logger.error(f"❌ Quantidade {quantidade}g inválida para esta atividade.")
            raise ValueError(f"❌ Quantidade {quantidade} inválida para PreparoParaArmazenamentoDeCremeDeCamarao.")

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        gestor_balancas,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        fracoes_necessarias: int = 2
    ) -> bool:
        self.calcular_duracao()
        return self._tentar_alocar_com_equipamentos(
            gestor_bancadas, gestor_balancas, inicio_jornada, fim_jornada, fracoes_necessarias
        )

    def _tentar_alocar_com_equipamentos(
        self,
        gestor_bancadas,
        gestor_balancas,
        inicio_jornada,
        fim_jornada,
        fracoes_necessarias
    ):
        horario_final = fim_jornada

        while horario_final - self.duracao >= inicio_jornada:
            horario_inicio = horario_final - self.duracao

            sucesso_bancada, bancada, ini_b, fim_b = self._tentar_alocar_bancada(
                gestor_bancadas, horario_inicio, horario_final, fracoes_necessarias
            )
            if not sucesso_bancada:
                horario_final -= timedelta(minutes=1)
                continue

            sucesso_balanca, balanca, _, _ = self._tentar_alocar_balanca(
                gestor_balancas, inicio_jornada, fim_jornada
            )
            if not sucesso_balanca:
                gestor_bancadas.liberar_por_atividade(self)
                return False

            self._registrar_sucesso(bancada, balanca, ini_b, fim_b)
            return True

        return False

    def _tentar_alocar_bancada(self, gestor, inicio, fim, fracoes):
        return gestor.alocar(
            inicio=inicio,
            fim=fim,
            atividade=self,
            fracoes_necessarias=fracoes
        )

    def _tentar_alocar_balanca(self, gestor, inicio, fim):
        return gestor.alocar(
            inicio=inicio,
            fim=fim,
            atividade=self,
            quantidade_gramas=self.quantidade_produto
        )

    def _registrar_sucesso(self, bancada, balanca, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.bancada_alocada = bancada
        self.balanca_alocada = balanca
        self.equipamento_alocado = [bancada, balanca]
        self.equipamentos_selecionados = [bancada, balanca]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada!\n"
            f"🪵 Bancada: {bancada.nome} ({inicio.strftime('%H:%M')}–{fim.strftime('%H:%M')})\n"
            f"⚖️ Balança: {balanca.nome} com {self.quantidade_produto}g"
        )
        print(
            f"✅ Atividade {self.id} alocada com sucesso."
        )

    def iniciar(self):
        if not self.alocada:
            raise Exception(f"❌ Atividade {self.id} não alocada ainda.")
        logger.info(f"🚀 Atividade {self.id} iniciada na bancada {self.bancada_alocada.nome} às {self.inicio_real.strftime('%H:%M')}")
