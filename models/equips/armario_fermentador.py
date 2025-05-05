from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento

class ArmarioFermentador(Equipamento):
    """
    Classe que representa um armário de fermentação.
    """
    def __init__(
            self, 
            id: int, 
            nome: str, 
            setor: TipoSetor,
            nivel_tela_min: int,
            nivel_tela_max: int,
            capacidade_niveis_min: int,
            capacidade_niveis_max: int
        ):
        super().__init__(
            id = id, 
            nome = nome, 
            tipo_equipamento = TipoEquipamento.ARMARIOS_PARA_FERMENTACAO, 
            setor = setor,
            status_ativo = True
        )
        self.nivel_tela_min = nivel_tela_min
        self.nivel_tela_max = nivel_tela_max
        self.nivel_tela_atual = 0
        self.capacidade_niveis_min = capacidade_niveis_min
        self.capacidade_niveis_max = capacidade_niveis_max
        self.capacidade_niveis_atual = 0
        
    def ocupar_nivel_tela(self, quantidade: int) -> bool:
        """
        Tenta ocupar um nível da tela.
        Retorna True se for possível, False se ultrapassar a capacidade.
        """
        if self.nivel_tela_atual + quantidade > self.nivel_tela:
            print(f"Erro: Não é possível ocupar mais de {self.capacidade_niveis} níveis.")
            return False
        self.nivel_tela += quantidade
        return True
    
    
    def liberar_nivel_tela(self, quantidade: int) -> bool:
        """
        Tenta liberar um nível da tela.
        Retorna True se for possível, False se não houver caixas a serem liberadas.
        """
        if self.nivel_tela_atual - quantidade < 0:
            print(f"Erro: Não é possível liberar mais de {self.capacidade_niveis} níveis.")
            return False
        self.nivel_tela -= quantidade
        return True
       
    def ocupar_capacidade_nivel(self, quantidade: int) -> bool:
        """
        Tenta ocupar uma capacidade de nível com uma quantidada determinada.
        Retorna True se for possível, False se não houver espaço para ocupar.
        """
        if self.capacidade_niveis_atual + quantidade > self.capacidade_niveis:
            print(f"Erro: Não é possível ocupar mais de {self.capacidade_niveis} níveis.")
            return False
        self.capacidade_niveis_atual += quantidade
        return 
    
    def liberar_capacidade_nivel(self, quantidade: int) -> bool:
        """
        Tenta liberar uma capacidade de nível com uma quantidada determinada.
        Retorna True se for possível, False se não houver espaço para liberar.
        """
        if self.capacidade_niveis_atual - quantidade < 0:
            print(f"Erro: Não é possível liberar mais de {self.capacidade_niveis} níveis.")
            return False
        self.capacidade_niveis_atual -= quantidade
        return True