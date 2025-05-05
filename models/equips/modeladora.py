from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_produto_modelado import TipoProdutoModelado

class Modeladora(Equipamento):
    """
    Classe que representa uma Modeladora.
    """
    def __init__(
        self,
        # Atributos fixos
        id: int,
        nome: str,
        setor: TipoSetor,
        tipo_produto_modelado: TipoProdutoModelado,
        capacidade_min_unidades_por_min: int,
        capacidade_max_unidades_por_min: int,
        numero_operadores:int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.MODELADORAS,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True
        )
        self.tipo_produto_modelado = tipo_produto_modelado
        self.capacidade_min_unidades_por_min = capacidade_min_unidades_por_min
        self.capacidade_max_unidades_por_min = capacidade_max_unidades_por_min
        self.capacidadade_unidades_atual = 0
        
    def ocupar_capacidade_unidades(self, quantidade: int) -> bool:
        """
        Ocupa a capacidade de unidades da modeladora.
        """
        if quantidade < self.capacidade_min_unidades_por_min:
            print(f"Não é possível ocupar a capacidade de pois o valor está abaixo do mínimo permitido {self.capacidade_min_unidades_por_min} da modeladora.")
            return False
        elif quantidade + self.capacidadade_unidades_atual > self.capacidade_max_unidades_por_min:
            print(f"Não é possível ocupar a capacidade de pois o valor está acima do máximo permitido {self.capacidade_max_unidades_por_min} da modeladora.")
            return False          
        self.capacidadade_unidades_atual += quantidade
        return True
    
    def liberar_capacidade_unidades(self, quantidade: int) -> bool:
        """
        Desocupa a capacidade de unidades da modeladora.
        """
        if self.capacidadade_unidades_atual - quantidade < 0:
            print("Não é possível desocupar a capacidade de unidades da modeladora.")
            return False
        self.capacidadade_unidades_atual -= quantidade
        return True
    