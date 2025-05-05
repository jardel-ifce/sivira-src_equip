from enum import Enum
from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_chama import TipoChama
from enums.pressao_chama import PressaoChama
from enums.tipo_equipamento import TipoEquipamento

class Fogao(Equipamento):
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        chamas_suportadas: list[TipoChama],
        capacidade_por_bocas_gramas: int,
        numero_bocas: int,
        pressao_chamas_suportadas: list[PressaoChama],


    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.FOGOES,
            status_ativo=True
        )
        self.chamas_suportadas = chamas_suportadas
        self.capacidade_por_bocas_gramas = capacidade_por_bocas_gramas
        self.numero_bocas = numero_bocas
        self.pressao_chamas_suportadas = pressao_chamas_suportadas