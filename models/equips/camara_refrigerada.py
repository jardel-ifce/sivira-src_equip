from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor

class CamaraRefrigerada(Equipamento):
    """
    Classe que representa uma Câmara Refrigerada.
    """
    def __init__(
        self,
        # Atributos fixos
        id: int,
        nome: str,
        setor:TipoSetor,
        capacidade_caixa_30kg: int,
        nivel_tela: int,
        capacidade_niveis: int,
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
        self.capacidade_caixa_30kg_atual = 0
        self.nivel_tela = nivel_tela
        self.nivel_tela_atual = 0
        self.capacidade_niveis = capacidade_niveis
        self.capacidade_niveis_atual = 0
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

    def ocupar_nivel_tela(self, quantidade: int) -> bool:
        """
        Tenta ocupar um nível da tela com uma quantidade de caixas de 30kg. 
        Retorna True se for possível, False se ultrapassar a capacidade.
        """
        if self.nivel_tela_atual + quantidade > self.nivel_tela:
            print(f"Erro: Não é possível ocupar mais de {self.capacidade_niveis} níveis.")
            return False
        self.nivel_tela += quantidade
        return True
    
    
    def liberar_nivel_tela(self, quantidade: int) -> bool:
        """
        Tenta liberar um nível da tela com uma quantidade de caixas de 30kg. 
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
    
    def __str__(self):
        return (
            super().__str__() +
            f"\nCapacidade de caixa 30kg: {self.capacidade_caixa_30kg} kg" +
            f"\nNível de tela: {self.nivel_tela} níveis" +
            f"\nCapacidade de níveis: {self.capacidade_niveis} níveis" +
            f"\nFaixa de temperatura mínima: {self.faixa_temperatura_min}°C" +
            f"\nFaixa de temperatura máxima: {self.faixa_temperatura_max}°C"
        )
