from datetime import timedelta
from models.atividade_base import Atividade
from models.equips.masseira import Masseira
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger
from datetime import datetime


# 🔥 Logger específico para esta atividade
logger = setup_logger('Atividade_Mistura_Massas_Para_Folhados')


class MisturaDeMassasParaFolhados(Atividade):
    """
    🌀 Atividade que representa a mistura de massas para folhados.
    ✅ Utiliza masseiras (misturadoras), com controle de ocupação realizado pelo gestor.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.misturadora_alocada= None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.MISTURADORAS: 1,
        }

    def calcular_duracao(self):
        self.duracao = self._definir_duracao_por_faixa(self.quantidade_produto)
        logger.info(f"🕒 Duração calculada: {self.duracao} para {self.quantidade_produto}g de massas folhadas.")

    def _definir_duracao_por_faixa(self, quantidade_produto):
        if 3000 <= quantidade_produto <= 6000:
            return timedelta(minutes=5)
        elif 6001 <= quantidade_produto <= 13000:
            return timedelta(minutes=8)
        elif 13001 <= quantidade_produto <= 20000:
            return timedelta(minutes=11)
        else:
            logger.error(f"❌ Quantidade {quantidade_produto}g inválida para armazenamento.")
            raise ValueError(f"❌ Quantidade inválida: {quantidade_produto}g.")

    def tentar_alocar_e_iniciar(
        self,
        gestor_misturadoras,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        quantidade: int,
    ) -> bool:
        self.calcular_duracao()
        return self._tentar_alocar_com_equipamentos(
            gestor_misturadoras, inicio_jornada, fim_jornada, quantidade
        )

    def _tentar_alocar_com_equipamentos(
        self,
        gestor_misturadoras,
        inicio_jornada,
        fim_jornada,
        quantidade
    ) -> bool:
        horario_final = fim_jornada

        while horario_final - self.duracao >= inicio_jornada:
            horario_inicio = horario_final - self.duracao

            sucesso_masseira, masseira, ini_m, fim_m = self._tentar_alocar_masseira(
                gestor_misturadoras, horario_inicio, horario_final, quantidade
            )
            if not sucesso_masseira:
                horario_final -= timedelta(minutes=1)
                continue
            self._registrar_sucesso_masseira(masseira, ini_m, fim_m)
            return True
        return False
    
    def _tentar_alocar_masseira(self, gestor_misturadoras, inicio, fim, quantidade):
        return gestor_misturadoras.alocar(
            inicio=inicio,
            fim=fim,
            atividade=self,
            quantidade=quantidade,
        )
    def _registrar_sucesso_masseira(self, masseira, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.masseira_alocada = masseira
        self.equipamento_alocado = [masseira]
        self.equipamentos_selecionados = [masseira]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada!\n"
            f"❄️ masseira: {masseira.nome} ({inicio.strftime('%H:%M')}–{fim.strftime('%H:%M')})\n"
        )
        print(
            f"✅ Atividade {self.id} alocada com sucesso."
        )
    
    def iniciar(self):
        if not self.alocada:
            raise Exception(f"❌ Atividade {self.id} não alocada ainda.")
        logger.info(f"🚀 Atividade {self.id} iniciada.")
