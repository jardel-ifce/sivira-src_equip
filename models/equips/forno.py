from models.equips.equipamento import Equipamento
from enums.tipo_coccao import TipoCoccao
from enums.tipo_setor import TipoSetor

class Forno(Equipamento):
    """"
    Classe Forno que herda da classe Equipamento.
    """
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor

    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoCoccao.FORNO,
            setor=setor,
            numero_operadores = 0,
            status_ativo=True
        )
    

