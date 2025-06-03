from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from models.atividade_base import Atividade
from utils.logger_factory import setup_logger

# 🥐 Logger específico para esta atividade
logger = setup_logger('Atividade_Armazenamento_Massas_Folhadas')


class ArmazenamentoSobTemperaturaParaMassasFolhadas(Atividade):
    """
    🥐 Atividade de armazenamento das massas folhadas.
    ✔️ Equipamento: ❄️ Câmara refrigerada ou freezer.
    ✅ Ocupação em caixas (20.000g por caixa).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "CAIXAS"
        self.camara_refrigerada_alocada= None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: 1,
        }

    def calcular_duracao(self):
        self.duracao = self._definir_duracao_por_faixa(self.quantidade_produto)
        logger.info(f"🕒 Duração calculada: {self.duracao} para {self.quantidade_produto}g de massas folhadas.")

    def _definir_duracao_por_faixa(self, quantidade):
        if 3000 <= quantidade <= 17000:
            return timedelta(minutes=3)
        elif 17001 <= quantidade <= 34000:
            return timedelta(minutes=4)
        elif 34001 <= quantidade <= 50000:
            return timedelta(minutes=5)
        else:
            logger.error(f"❌ Quantidade {quantidade}g inválida para armazenamento.")
            raise ValueError(f"❌ Quantidade inválida: {quantidade}g.")

    def tentar_alocar_e_iniciar(
        self,
        gestor_refrigeracao,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        temperatura_desejada: int = -18
    ) -> bool:
        self.calcular_duracao()
        return self._tentar_alocar_com_equipamentos(
            gestor_refrigeracao, inicio_jornada, fim_jornada, temperatura_desejada
        )

    def _tentar_alocar_com_equipamentos(
        self,
        gestor_refrigeracao_congelamento,
        inicio_jornada,
        fim_jornada,
        temperatura_desejada
    ) -> bool:
        horario_final = fim_jornada

        while horario_final - self.duracao >= inicio_jornada:
            horario_inicio = horario_final - self.duracao

            sucesso_camara_refrigerada, camara_refrigerada, ini_cr, fim_cr = self._tentar_alocar_camara_refrigerada(
                gestor_refrigeracao_congelamento, horario_inicio, horario_final, temperatura_desejada
            )
            if not sucesso_camara_refrigerada:
                horario_final -= timedelta(minutes=1)
                continue
            self._registrar_sucesso_camara_refrigerada(camara_refrigerada, ini_cr, fim_cr)
            return True
        return False
    
    def _tentar_alocar_camara_refrigerada(self, gestor_camara_refrigerada, inicio, fim, temperatura_desejada):
        return gestor_camara_refrigerada.alocar(
            inicio=inicio,
            fim=fim,
            atividade=self,
            temperatura_desejada=temperatura_desejada
        )
    def _registrar_sucesso_camara_refrigerada(self, camara_refrigerada, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.camara_refrigerada_alocada = camara_refrigerada
        self.equipamento_alocado = [camara_refrigerada]
        self.equipamentos_selecionados = [camara_refrigerada]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada!\n"
            f"❄️ Câmara Refrigerada: {camara_refrigerada.nome} ({inicio.strftime('%H:%M')}–{fim.strftime('%H:%M')})\n"
        )
        print(
            f"✅ Atividade {self.id} alocada com sucesso."
        )
    
    def iniciar(self):
        if not self.alocada:
            raise Exception(f"❌ Atividade {self.id} não alocada ainda.")
        logger.info(f"🚀 Atividade {self.id} iniciada.")
