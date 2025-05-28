from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_atividade import TipoAtividade
from typing import List, Tuple
from datetime import datetime


class Freezer(Equipamento):
    """
    Classe que representa um Freezer com controle de ocupação por caixas de 30kg,
    respeitando limites mínimo e máximo de ocupação.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_caixa_30kg_min: int,
        capacidade_caixa_30kg_max: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.REFRIGERACAO_CONGELAMENTO,
            setor=setor,
            numero_operadores=0,
            status_ativo=True,
        )

        self.capacidade_caixa_30kg_min = capacidade_caixa_30kg_min
        self.capacidade_caixa_30kg_max = capacidade_caixa_30kg_max
        self.capacidade_caixa_30kg_atual = 0

        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = 0

        self.ocupacao: List[Tuple[datetime, datetime, TipoAtividade]] = []

    # ============================================
    # 📦 Métodos de Ocupação por Caixa
    # ============================================
    def ocupar_caixas(self, quantidade_caixas: int) -> bool:
        """
        Ocupa caixas no freezer, respeitando limites mínimo e máximo.
        """
        if quantidade_caixas < self.capacidade_caixa_30kg_min:
            print(
                f"❌ Ocupação mínima não atendida. "
                f"Quantidade informada: {quantidade_caixas}. "
                f"Mínimo exigido: {self.capacidade_caixa_30kg_min} caixas."
            )
            return False

        if self.capacidade_caixa_30kg_atual + quantidade_caixas > self.capacidade_caixa_30kg_max:
            print(
                f"❌ Ocupação excede a capacidade máxima do Freezer {self.nome}. "
                f"Disponível: {self.caixas_disponiveis()} caixas."
            )
            return False

        self.capacidade_caixa_30kg_atual += quantidade_caixas
        print(
            f"✅ Ocupou {quantidade_caixas} caixas no Freezer {self.nome}. "
            f"Ocupação atual: {self.capacidade_caixa_30kg_atual}/{self.capacidade_caixa_30kg_max}."
        )
        return True

    def liberar_caixas(self, quantidade_caixas: int) -> bool:
        """
        Libera caixas do freezer.
        """
        if self.capacidade_caixa_30kg_atual - quantidade_caixas < 0:
            print(
                f"❌ Não é possível liberar {quantidade_caixas} caixas. "
                f"Apenas {self.capacidade_caixa_30kg_atual} estão ocupadas."
            )
            return False

        self.capacidade_caixa_30kg_atual -= quantidade_caixas
        print(
            f"🟩 Liberou {quantidade_caixas} caixas do Freezer {self.nome}. "
            f"Ocupação atual: {self.capacidade_caixa_30kg_atual}/{self.capacidade_caixa_30kg_max}."
        )
        return True

    def liberar_todas_as_caixas(self):
        """
        Libera todas as caixas ocupadas no freezer.
        """
        print(
            f"🟩 Liberou todas as {self.capacidade_caixa_30kg_atual} caixas do Freezer {self.nome}."
        )
        self.capacidade_caixa_30kg_atual = 0

    def caixas_disponiveis(self) -> int:
        """
        Retorna o número de caixas ainda disponíveis.
        """
        return self.capacidade_caixa_30kg_max - self.capacidade_caixa_30kg_atual

    # ============================================
    # 🌡️ Controle da Temperatura
    # ============================================
    def selecionar_faixa_temperatura(self, temperatura: int) -> bool:
        """
        Seleciona a temperatura do freezer dentro dos limites permitidos.
        """
        if temperatura > self.faixa_temperatura_max or temperatura < self.faixa_temperatura_min:
            print(
                f"❌ Temperatura {temperatura}°C fora da faixa permitida "
                f"({self.faixa_temperatura_min}°C a {self.faixa_temperatura_max}°C)."
            )
            return False

        self.faixa_temperatura_atual = temperatura
        print(
            f"🌡️ Temperatura ajustada para {temperatura}°C no Freezer {self.nome}."
        )
        return True

    # ============================================
    # 🔍 Visualização e Status
    # ============================================
    def __str__(self):
        return (
            super().__str__() +
            f"\n📦 Capacidade (caixas de 30kg): {self.capacidade_caixa_30kg_min} mín. / {self.capacidade_caixa_30kg_max} máx."
            f"\n📦 Caixas ocupadas: {self.capacidade_caixa_30kg_atual} | Disponíveis: {self.caixas_disponiveis()}"
            f"\n🌡️ Temperatura: {self.faixa_temperatura_atual}°C | Faixa permitida: {self.faixa_temperatura_min}°C a {self.faixa_temperatura_max}°C"
        )
