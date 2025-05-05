from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.velocidade import Velocidade
from typing import List
from enums.pressao_chama import PressaoChama

class HotMix(Equipamento):
    """"
    Classe que representa um equipamento de tipo HotMix.
    """
    def __init__(
        self,
        # Atributos fixos
        id: int,
        nome: str,
        setor: str,
        velocidades_suportadas: List[Velocidade],
        pressao_chama_suportadas: List[PressaoChama],
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.MISTURADORAS_COM_COCCAO,
            setor=setor,
            numero_operadores=1,
            status_ativo=True
        )
        # Atributos dinâmicos
        self.velocidade_atual: Velocidade = Velocidade.BAIXA
        self.velocidades_suportadas: List[Velocidade] = velocidades_suportadas
        self.pressao_chama_suportadas: List[PressaoChama] = pressao_chama_suportadas
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max

    def setar_velocidade(self, nova_velocidade: Velocidade) -> bool:
        """
        Define a velocidade atual do equipamento, caso esteja entre as suportadas.
        """
        if nova_velocidade in self.velocidades_suportadas:
            self.velocidade_atual = nova_velocidade
            print(f"{self.nome} | Velocidade ajustada para {nova_velocidade.name}.")
            return True
        print(f"{self.nome} | Velocidade {nova_velocidade.name} não suportada.")
        return False

    def suporta_pressao(self, pressao: PressaoChama) -> bool:
        """
        Verifica se a pressão de chama fornecida é suportada pela HotMix.
        """
        return pressao in self.pressao_chama_suportadas

    def ocupar(self, quantidade_gramas: int) -> bool:
        """
        Ocupa a capacidade da HotMix com uma determinada quantidade de gramas.
        """
        if self.ocupado:
            print(f"{self.nome} já está ocupado.")
            return False
        if not (self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max):
            print(f"{self.nome} | Quantidade {quantidade_gramas}g fora da capacidade suportada.")
            return False
        self.ocupado = True
        print(f"{self.nome} | ocupado com {quantidade_gramas}g.")
        return True

    def liberar(self) -> None:
        """
        Libera o equipamento, tornando-o disponível.
        """
        self.ocupado = False
        print(f"{self.nome} liberada.")
