from models.equips.equipamento import Equipamento
from enums.velocidade import Velocidade
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_mistura import TipoMistura

class Masseira(Equipamento):
    """
    Classe que representa uma Masseira com controle de ocupação e velocidades configuráveis.
    """

    def __init__(
        self, 
        id: int, 
        nome: str, 
        setor: str, 
        capacidade_gramas_max: int,
        capacidade_gramas_min: int,
        ritmo_execucao: TipoMistura,
        velocidades_suportadas: list[Velocidade],
        velocidade_atual: Velocidade = Velocidade.BAIXA,
        capacidade_ocupada: int = 0
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            tipo_equipamento=TipoEquipamento.MISTURADORAS,
            numero_operadores=1,
            status_ativo=True
        )

        self.capacidade_gramas_max = capacidade_gramas_max
        self.capacidade_gramas_min = capacidade_gramas_min
        self.ritmo_execucao = ritmo_execucao
        self.velocidades_suportadas = velocidades_suportadas

        if velocidade_atual in velocidades_suportadas:
            self.velocidade_atual = velocidade_atual
        else:
            raise ValueError(f"Velocidade {velocidade_atual.name} não suportada pela masseira '{nome}'.")

        self.capacidade_ocupada = capacidade_ocupada

    def configurar_velocidade(self, nova_velocidade: Velocidade) -> bool:
        """
        Configura a velocidade da masseira se suportada.
        """
        if nova_velocidade in self.velocidades_suportadas:
            self.velocidade_atual = nova_velocidade
            return True
        return False

    def ocupar(self, quantidade: int) -> bool:
        if self.capacidade_ocupada + quantidade <= self.capacidade_gramas_max:
            self.capacidade_ocupada += quantidade
            return True
        return False

    def liberar(self, quantidade: int) -> None:
        self.capacidade_ocupada = max(0, self.capacidade_ocupada - quantidade)

    def capacidade_disponivel(self) -> int:
        return self.capacidade_gramas_max - self.capacidade_ocupada

    def __str__(self):
        velocidades = ', '.join(v.name for v in self.velocidades_suportadas)
        return (
            super().__str__() + "\n"
            f"Capacidade Máxima: {self.capacidade_gramas_max}g\n"
            f"Capacidade Mínima: {self.capacidade_gramas_min}g\n"
            f"Capacidade Ocupada: {self.capacidade_ocupada}g\n"
            f"Disponível: {self.capacidade_disponivel()}g\n"
            f"Velocidade Atual: {self.velocidade_atual.name}\n"
            f"Velocidades Suportadas: {velocidades}\n"
            f"Ritmo de Execução: {self.ritmo_execucao.name}"
        )
