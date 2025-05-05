from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor

class Equipamento:
    """
    Superclasse que representa um equipamento.
    """
    def __init__(self, id: int, nome: str, tipo_equipamento: TipoEquipamento, setor: TipoSetor, numero_operadores: int, status_ativo: bool):
        # Atributos fixos
        self.id = id
        self.nome = nome
        self.tipo_equipamento = tipo_equipamento
        self.setor = setor
        self.numero_operadores = numero_operadores
        self.status_ativo = status_ativo

    def __str__(self):
        return (
            f"ID: {self.id}\n"
            f"Nome: {self.nome}\n"
            f"Tipo de Equipamento: {self.tipo_equipamento}\n"
            f"Setor: {self.setor}\n"
            f"Número de Operadores: {self.numero_operadores}\n"
            f"Status Ativo: {'Sim' if self.status_ativo else 'Não'}\n"
        )