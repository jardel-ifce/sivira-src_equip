from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor

class Freezer(Equipamento):
    """
    Classe que representa um Freezer.
    """
    def __init__(
        self,
        # Atributos fixos
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_caixa_30kg: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.REFRIGERACAO_CONGELAMENTO,
            setor=setor,
            numero_operadores=0,
            status_ativo=True
        )
        self.capacidade_caixa_30kg = capacidade_caixa_30kg
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = 0

    def ocupar_capacidade_caixa_30kg (self, quantidade: int) -> bool:
        """
        Tenta ocupar uma capacidade de caixas de 30kg com uma quantidade de caixas. 
        Retorna True se for possível, False se ultrapassar a capacidade
        """
        if self.capacidade_caixa_30kg_atual + quantidade > self.capacidade_caixa_30kg:
            print(f"Erro: Não é possível ocupar mais de {self.capacidade_caixa_30kg} caixas.")
            return False
        self.capacidade_caixa_30kg_atual += quantidade
        return True
    
    def liberar_capacidade_caixa_30kg(self, quantidade: int) -> bool:
        """
        Tenta liberar uma capacidade de caixas de 30kg com uma quantidade de caixas. 
        Retorna True se for possível, False se não houver caixas a serem liberadas.
        """
        if self.capacidade_caixa_30kg_atual - quantidade < 0:
            print(f"Erro: Não é possível liberar mais de {self.capacidade_caixa_30kg} caixas.")
            return False
        self.capacidade_caixa_30kg_atual -= quantidade
        return True

