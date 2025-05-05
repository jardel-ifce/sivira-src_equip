from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from fractions import Fraction

class Fritadeira(Equipamento):
    """
    Classe que representa uma fritadeira.
    """
    def __init__(
        self,
        id: int,
        nome: str,
        setor: str,
        numero_operadores: int,
        capacidade_fracionamento: tuple[int, int],
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        capacidade_gramas_atual: int,
        setup_min: int,
        setup_max: int,
        setup_atual: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int,
        faixa_temperatura_atual: int,
    ):
        super().__init__(
            id = id, 
            nome = nome, 
            setor = setor,
            tipo_equipamento = TipoEquipamento.FRITADEIRAS, 
            numero_operadores = numero_operadores
        )
        self.capacidade_total= Fraction(*capacidade_fracionamento)
        self.capacidade_ocupada= Fraction(0, 1)
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.capacidade_gramas_atual = capacidade_gramas_atual
        self.setup_min = setup_min
        self.setup_max = setup_max
        self.setup_atual = setup_atual
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = faixa_temperatura_atual
        
    def ocupar(self, quantidade: tuple[int, int]):
        """
        Tenta ocupar parte da bancada. Retorna True se for possível, False se ultrapassar a capacidade.
        """
        quantidade_frac = Fraction(*quantidade)  # Converte o tuple em Fraction
        if self.capacidade_ocupada + quantidade_frac <= self.capacidade_total:
            self.capacidade_ocupada += quantidade_frac
            return True
        return False
    
    def liberar(self, quantidade: Fraction) -> None:
        """
        Libera parte da bancada. Garante que a ocupação não fique negativa.
        """
        self.capacidade_ocupada -= quantidade
        if self.capacidade_ocupada < 0:
            self.capacidade_ocupada = Fraction(0, 1)
            return False        

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
    
    def configurar_setup(self, setup: int) -> bool:
        """
        Define o setup da divisora.
        """
        if setup < self.setup_min:
            print(f"Não é possível definir o setup pois o valor está abaixo do mínimo permitido {self.setup_min} da divisora.")
            return False
        elif setup > self.setup_max:
            print(f"Não é possível definir o setup pois o valor está acima do máximo permitido {self.setup_max} da divisora.")
            return False
        self.setup_atual = setup
        return 
    
    def configurar_faixa_temperatura(self, faixa: int) -> bool:
        """
        Define a faixa de temperatura da divisora.
        """
        if faixa < self.faixa_temperatura_min:
            print(f"Não é possível definir a faixa de temperatura pois o valor está abaixo do mínimo permitido {self.faixa_temperatura_min} da divisora.")
            return False
        elif faixa > self.faixa_temperatura_max:
            print(f"Não é possível definir a faixa de temperatura pois o valor está acima do máximo permitido {self.faixa_temperatura_max} da divisora.")
            return False
        self.faixa_temperatura_atual = faixa
        return