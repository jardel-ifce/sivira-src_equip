from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento

class DivisoraDeMassas(Equipamento):
    """
    Classe que representa uma divisora de massas.
    """
    def __init__(
        self, 
        id: int, 
        nome: str, 
        setor: TipoSetor, 
        numero_operadores: int, 
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        boleadora: bool,
        capacidade_divisao_unidades_por_segundo: int,
        capacidade_boleamento_unidades_por_segundo: int

    ):
        super().__init__(
            id = id, 
            nome = nome, 
            setor = setor, 
            numero_operadores = numero_operadores,
            tipo_equipamento = TipoEquipamento.DIVISORAS_BOLEADORAS,
            status_ativo=True
        )
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.capacidade_gramas_atual = 0
        self.boleadora = boleadora
        self.capacidade_divisao_unidades_por_segundo = capacidade_divisao_unidades_por_segundo
        self.capacidade_boleamento_unidades_por_segundo = capacidade_boleamento_unidades_por_segundo

    def ocupar_capacidade_gramas(self, gramas: int) -> bool:
        """
        Ocupa a capacidade de massa do equipamento.
        """
        if gramas < self.capacidade_gramas_min:
            print(f"Não é possível ocupar a capacidade de pois o valor está abaixo do mínimo permitido {self.capacidade_gramas_min} da divisora.")
            return False
        elif gramas + self.capacidade_gramas_atual > self.capacidade_gramas_max:
            print(f"Não é possível ocupar a capacidade de pois o valor está acima do máximo permitido {self.capacidade_gramas_max} da divisora.")
            return False          
        self.capacidadade_gramas_atual += gramas
        return True
    
    def liberar_capacidade_gramas(self, gramas: int) -> bool:
        """
        Desocupa a capacidade de massa da divisora.
        """
        if self.capacidadade_gramas_atual - gramas < 0:
            print("Não é possível desocupar a capacidade de unidades da divisora.")
            return False
        self.capacidadade_unidades_atual -= gramas
        return True
    