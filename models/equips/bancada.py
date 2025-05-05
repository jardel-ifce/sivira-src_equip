from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from models.equips.equipamento import Equipamento  
from fractions import Fraction

class Bancada(Equipamento):
    """
    Classe que representa uma bancada.
    """
    def __init__(
            # Atributos fixos
            self, 
            id: int, 
            nome: str, 
            setor: TipoSetor, 
            # Atributos dinâmicos
            capacidade_fracionamento: tuple[int, int],
            numero_operadores: int = 0
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.BANCADAS,
            setor=setor,
            status_ativo=True,
            numero_operadores= numero_operadores
        )
        self.capacidade_total= Fraction(*capacidade_fracionamento)
        self.capacidade_ocupada= Fraction(0, 1)

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
    
    def capacidade_disponivel(self) -> Fraction:
        """
        Retorna a fração ainda disponível da bancada.
        """
        return self.capacidade_total - self.capacidade_ocupada

    def __str__(self):
        return super().__str__() + (
            f"Capacidade Total: {self.capacidade_total}\n"
            f"Capacidade Ocupada: {self.capacidade_ocupada}\n"
        )