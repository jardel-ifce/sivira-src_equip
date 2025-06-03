from models.atividade_base import Atividade
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger
from utils.consultar_duracao_por_ids import consultar_duracao_por_ids

# 🧊 Logger específico
logger = setup_logger('AtividadeArmazenamentoCarneDeSol')


class ArmazenamentoSobTemperaturaParaCarneDeSolRefogada(Atividade):
    """
    🧊 Atividade de armazenamento da carne de sol refogada em câmara refrigerada.
    ✅ Ocupação feita em caixas de 30kg (20.000g por caixa).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "CAIXAS"
        self.camara_refrigerada_alocada = None


    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: 1,
        }

    def calcular_duracao(self):
        self.duracao = consultar_duracao_por_ids(id_produto=self.id_produto_gerado, id_atividade=self.id_atividade, quantidade=self.quantidade_produto)
        logger.info(f"🕒 Duração calculada: {self.duracao} para {self.quantidade_produto}g de carne de sol refogada.")


    def tentar_alocar_e_iniciar(
        self,
        gestor_refrigeracao,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        temperatura_desejada: int
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

            sucesso, camara_refrigerada, ini_cr, fim_cr = self._tentar_alocar_camara_refrigerada(
                gestor_refrigeracao_congelamento, horario_inicio, horario_final, temperatura_desejada
            )
            if not sucesso:
                horario_final -= timedelta(minutes=1)
                continue

            self._registrar_sucesso_camara_refrigerada(camara_refrigerada, ini_cr, fim_cr)
            return True

        logger.error(
            f"❌ Não foi possível alocar atividade {self.id} "
            f"dentro da janela de {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )
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

        temperatura_real = camara_refrigerada.faixa_temperatura_atual

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso!\n"
            f"🧊 Câmara Refrigerada: {camara_refrigerada.nome} ({inicio.strftime('%H:%M')}–{fim.strftime('%H:%M')}) "
            f"| Temperatura: {temperatura_real}°C"
        )
        print(
            f"✅ Atividade {self.id} alocada na {camara_refrigerada.nome} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"com temperatura {temperatura_real}°C."
        )

    def iniciar(self):
        if not self.alocada:
            raise Exception(f"❌ Atividade {self.id} não alocada ainda.")
        logger.info(f"🚀 Atividade {self.id} iniciada.")
