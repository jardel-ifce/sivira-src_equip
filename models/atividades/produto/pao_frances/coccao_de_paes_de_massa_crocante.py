from datetime import timedelta
from models.atividade_base import Atividade
from models.equips.balanca_digital import BalancaDigital
from models.equips.bancada import Bancada
from models.equips.modeladora import Modeladora
from models.equips.forno import Forno
from enums.tipo_atividade import TipoAtividade
from enums.tipo_equipamento import TipoEquipamento

class CoccaoDePaesDeMassaCrocante(Atividade):
    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.FORNOS: 1,
        }

    def calcular_duracao(self):
        self.duracao = timedelta(minutes=20)

    def iniciar(self):
        for equipamento in self.equipamentos_selecionados:
            if isinstance(equipamento, Forno):
                equipamento.assar(self.quantidade_produto)
