from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor

class BatedeiraIndustrial(Equipamento):
    """
    Classe que representa um batedeira industrial.
    """
    def __init__(
        self,
        id:int,
        nome:str,
        setor:TipoSetor,
        numero_operadores:int,
        velocidade_min:int,
        velocidade_max:int,
        capacidade_gramas_min:int,
        capacidade_gramas_max:int,
        velocidade_atual:int = 0,
        capacidade_atual:int = 0
    ):
        super().__init__(
            id = id, 
            nome = nome, 
            setor = setor, 
            tipo_equipamento = TipoEquipamento.BATEDEIRAS,
            numero_operadores=numero_operadores,
            status_ativo = True
        )
        self.velocidade_min = velocidade_min
        self.velocidade_max = velocidade_max
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.velocidade_atual = velocidade_atual
        self.capacidade_atual = capacidade_atual

    def setar_velocidade(self, nova_velocidade: int) -> bool:
        """
        Define a velocidade da batedeira, se estiver dentro dos limites.
        """
        if self.velocidade_min <= nova_velocidade <= self.velocidade_max:
            self.velocidade_atual = nova_velocidade
            print(f"{self.nome} | Velocidade ajustada para {nova_velocidade.name}.")
            return True
        return False

    def ocupar(self, gramas: int) -> bool:
        """
        Ocupa a batedeira com a quantidade de gramas especificada.
        """
        if self.capacidade_atual + gramas <= self.capacidade_gramas_max:
            self.capacidade_atual += gramas
            return True
        return False

    def liberar(self, gramas: int) -> bool:
        """
        Libera a quantidade de gramas da capacidade atual.
        """
        self.capacidade_atual -= gramas
        if self.capacidade_atual < 0:
            self.capacidade_atual = 0
            return False
        return True

    def capacidade_disponivel(self) -> int:
        """
        Retorna a capacidade ainda disponível da batedeira.
        """
        return self.capacidade_gramas_max - self.capacidade_atual

    def __str__(self):
        return (
            super().__str__() +
            f"Velocidade: {self.velocidade_atual} (min: {self.velocidade_min}, max: {self.velocidade_max})\n"
            f"Capacidade Atual: {self.capacidade_atual}g (máx: {self.capacidade_gramas_max}g)\n"
        )

