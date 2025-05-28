# models/atividades/pesagem_de_massas.py

from datetime import timedelta
from models.atividade_base import Atividade
from models.equips.balanca_digital import BalancaDigital
from models.equips.bancada import Bancada
from enums.tipo_atividade import TipoAtividade
from enums.tipo_equipamento import TipoEquipamento

class PesagemDeMassas(Atividade):
    """
    Subclasse para a atividade de pesagem de massas.
    """
    @property
    def quantidade_por_tipo_equipamento(self):
        """
        Define quantos equipamentos de cada tipo são necessários para esta atividade.
        """
        return {
            TipoEquipamento.BALANCAS: 1,
            TipoEquipamento.BANCADAS: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade conforme a quantidade do produto.
        """
        q = self.quantidade_produto
        if 30 <= q <= 240:
            self.duracao = timedelta(minutes=3)
        elif 241 <= q <= 480:
            self.duracao = timedelta(minutes=6)
        elif 481 <= q <= 720:
            self.duracao = timedelta(minutes=9)
        else:
            raise ValueError(f"❌ Quantidade {q} fora das faixas definidas para PESAGEM_DE_MASSAS.")

    def iniciar(self):
        """
        Executa os métodos específicos dos equipamentos selecionados.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        for equipamento in self.equipamentos_selecionados:
            if isinstance(equipamento, BalancaDigital):
                equipamento.pesar(self.quantidade_produto)
            elif isinstance(equipamento, Bancada):
                equipamento.ocupar((1, 4))
