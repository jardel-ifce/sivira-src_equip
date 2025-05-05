from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento

class BalancaDigital(Equipamento):
    """
    Classe que representa uma Balança Digital.
    """
    def __init__(
            # Atributos fixos
            self, 
            id: int, 
            nome: str, 
            setor: TipoSetor, 
            capacidade_gramas_min: int,
            capacidade_gramas_max: int,
            # Atributos dinâmicos
            capacidade_atual: int = 0,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.BALANCAS,
            setor=setor,
            numero_operadores=1,
            status_ativo=True,
        )
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.capacidade_atual = capacidade_atual

    def pesar(self, quantidade: int) -> bool:
        """
        Tenta pesar uma quantidade. Retorna True se for possível, False se ultrapassar a capacidade.
        """
        if self.capacidade_atual + quantidade > self.capacidade_gramas_max:
            print(f"Erro: Não é possível pesar {quantidade} gramas. Capacidade máxima de {self.capacidade_gramas_max} gramas excedida.")
            return False
        self.capacidade_atual += quantidade
        return True

    def liberar(self, quantidade: int) -> None:
        """
        Libera parte da capacidade ocupada. Evita capacidade negativa.
        """
        if quantidade > self.capacidade_atual:
            print(f"Erro: Não é possível liberar {quantidade} gramas. Apenas {self.capacidade_atual} gramas estão ocupadas.")
            self.capacidade_atual = 0
            return
        self.capacidade_atual -= quantidade
        if self.capacidade_atual < 0:
            self.capacidade_atual = 0
