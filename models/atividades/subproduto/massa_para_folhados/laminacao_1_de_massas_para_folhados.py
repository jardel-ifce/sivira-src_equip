from datetime import timedelta
from models.atividade_base import Atividade
from models.equips.bancada import Bancada
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger
from datetime import datetime


# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Laminacao1_Massas_Folhados')


class Laminacao1DeMassasParaFolhados(Atividade):
    """
    🪵 Primeira etapa de laminação de massas para folhados.
    ✅ Utiliza bancadas, com controle de ocupação por frações proporcionais.
    ✔️ Sempre ocupa 4 porções da bancada, independentemente se ela é 4/4 ou 4/6.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bancada_alocada= None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
        }

    def calcular_duracao(self):
        self.duracao = self._definir_duracao_por_faixa(self.quantidade_produto)
        logger.info(f"🕒 Duração calculada: {self.duracao} para {self.quantidade_produto}g de massas folhadas.")

    def _definir_duracao_por_faixa(self, quantidade):
        if 3000 <= quantidade <= 6000:
            return timedelta(minutes=10)
        elif 6001 <= quantidade <= 13000:
            return timedelta(minutes=15)
        elif 13001 <= quantidade <= 20000:
            return timedelta(minutes=20)
        else:
            logger.error(f"❌ Quantidade {quantidade}g inválida para armazenamento.")
            raise ValueError(f"❌ Quantidade inválida: {quantidade}g.")

    def tentar_alocar_e_iniciar(
        self,
        gestor_bancadas,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        fracoes_necessarias: int
    ) -> bool:
        self.calcular_duracao()
        return self._tentar_alocar_com_equipamentos(
            gestor_bancadas, inicio_jornada, fim_jornada, fracoes_necessarias
        )

    def _tentar_alocar_com_equipamentos(
        self,
        gestor_bancadas,
        inicio_jornada,
        fim_jornada,
        temperatura_desejada
    ) -> bool:
        horario_final = fim_jornada

        while horario_final - self.duracao >= inicio_jornada:
            horario_inicio = horario_final - self.duracao

            sucesso_bancada, bancada, ini_b, fim_b = self._tentar_alocar_bancada(
                gestor_bancadas, horario_inicio, horario_final, temperatura_desejada
            )
            if not sucesso_bancada:
                horario_final -= timedelta(minutes=1)
                continue
            self._registrar_sucesso_bancada(bancada, ini_b, fim_b)
            return True
        return False
    
    def _tentar_alocar_bancada(self, gestor_bancadas, inicio, fim, fracoes_necessarias):
        return gestor_bancadas.alocar(
            inicio=inicio,
            fim=fim,
            atividade=self,
            fracoes_necessarias=fracoes_necessarias,
        )
    def _registrar_sucesso_bancada(self, bancada, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.bancada_alocada = bancada
        self.equipamento_alocado = [bancada]
        self.equipamentos_selecionados = [bancada]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada!\n"
            f"❄️ Bancada: {bancada.nome} ({inicio.strftime('%H:%M')}–{fim.strftime('%H:%M')})\n"
        )
        print(
            f"✅ Atividade {self.id} alocada com sucesso."
        )
    
    def iniciar(self):
        if not self.alocada:
            raise Exception(f"❌ Atividade {self.id} não alocada ainda.")
        logger.info(f"🚀 Atividade {self.id} iniciada.")
