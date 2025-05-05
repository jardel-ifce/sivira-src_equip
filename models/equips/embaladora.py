from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor  
from enums.tipo_embalagem import TipoEmbalagem
from typing import List

class Embaladora(Equipamento):
    """
    Classe que representa uma Embaladora.
    """
    def __init__(
        self,
        # Atributos fixos
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_gramas: int,
        lista_tipo_embalagem: List[TipoEmbalagem],
        numero_operadores: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.EMBALADORAS,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True
        )
        self.capacidade_gramas = capacidade_gramas
        self.capacidade_gramas_atual = 0
        self.lista_tipo_embalagem = lista_tipo_embalagem

    def ocupar_capacidade_gramas(self, gramas: int) -> bool:
        """
        Ocupa uma quantidade de gramas na capacidade da embaladora.
        """
        if gramas + self.capacidade_gramas_atual > self.capacidade_gramas:
            print(f"Erro: Não é possível ocupar mais de {self.capacidade_gramas} gramas.")
            return False
        self.capacidade_gramas_atual += gramas

    def liberar_capacidade_gramas(self, gramas: int) -> bool:
        """
        Libera uma quantidade de gramas da capacidade da embaladora.
        """
        if gramas - self.capacidade_gramas_atual < 0:
            print(f"Erro: Não é possível liberar mais de {self.capacidade_gramas} gramas.")
            return False
        self.capacidade_gramas_atual -= gramas

    