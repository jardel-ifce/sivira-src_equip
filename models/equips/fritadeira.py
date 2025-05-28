from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_atividade import TipoAtividade
from fractions import Fraction
from datetime import datetime
from typing import List, Tuple


class Fritadeira(Equipamento):
    """
    Classe que representa uma Fritadeira.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_fracionamento: tuple[int, int],
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        setup_min: int,
        setup_max: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            tipo_equipamento=TipoEquipamento.FRITADEIRAS,
            numero_operadores=numero_operadores,
            status_ativo=True,
        )

        # Capacidade fracionada (Ex.: 1/2, 1/3, 1/4 da fritadeira)
        self.capacidade_total = Fraction(*capacidade_fracionamento)
        self.capacidade_ocupada = Fraction(0, 1)

        # Capacidade por peso
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.capacidade_gramas_atual = 0

        # Setup operacional
        self.setup_min = setup_min
        self.setup_max = setup_max
        self.setup_atual = 0

        # Faixa de temperatura
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = 0

        self.ocupacao: List[Tuple[datetime, datetime, TipoAtividade]] = []

    # ============================================
    # 🧠 Ocupação Fracionada
    # ============================================
    def ocupar(self, quantidade: tuple[int, int]) -> bool:
        quantidade_frac = Fraction(*quantidade)

        if self.capacidade_ocupada + quantidade_frac <= self.capacidade_total:
            self.capacidade_ocupada += quantidade_frac
            print(
                f"✅ Ocupou {quantidade_frac} da fritadeira {self.nome}. "
                f"Ocupação atual: {self.capacidade_ocupada}/{self.capacidade_total}."
            )
            return True

        print(
            f"❌ Não foi possível ocupar {quantidade_frac} da fritadeira {self.nome}. "
            f"Disponível: {self.fracao_disponivel()}."
        )
        return False

    def liberar(self, quantidade: tuple[int, int] | Fraction) -> bool:
        quantidade_frac = (
            Fraction(*quantidade) if isinstance(quantidade, tuple) else quantidade
        )

        self.capacidade_ocupada -= quantidade_frac

        if self.capacidade_ocupada < 0:
            self.capacidade_ocupada = Fraction(0, 1)
            print("⚠️ Tentou liberar mais do que ocupado. Resetado para zero.")
            return False

        print(
            f"🟩 Liberou {quantidade_frac} da fritadeira {self.nome}. "
            f"Ocupação atual: {self.capacidade_ocupada}/{self.capacidade_total}."
        )
        return True

    def liberar_tudo(self):
        print(
            f"🟩 Liberou toda a ocupação fracionada da fritadeira {self.nome}. "
            f"Ocupação anterior: {self.capacidade_ocupada}/{self.capacidade_total}."
        )
        self.capacidade_ocupada = Fraction(0, 1)

    def fracao_disponivel(self) -> Fraction:
        return self.capacidade_total - self.capacidade_ocupada

    # ============================================
    # ⚖️ Ocupação por Peso
    # ============================================
    def ocupar_capacidade_gramas(self, gramas: int) -> bool:
        if gramas < self.capacidade_gramas_min:
            print(
                f"❌ Quantidade {gramas}g abaixo do mínimo permitido ({self.capacidade_gramas_min}g) na fritadeira {self.nome}."
            )
            return False

        if gramas + self.capacidade_gramas_atual > self.capacidade_gramas_max:
            print(
                f"❌ Ocupação excede a capacidade máxima ({self.capacidade_gramas_max}g) da fritadeira {self.nome}."
            )
            return False

        self.capacidade_gramas_atual += gramas
        print(
            f"✅ Ocupou {gramas}g na fritadeira {self.nome}. "
            f"Ocupação atual: {self.capacidade_gramas_atual}/{self.capacidade_gramas_max}g."
        )
        return True

    def liberar_capacidade_gramas(self, gramas: int) -> bool:
        if self.capacidade_gramas_atual - gramas < 0:
            print(
                f"❌ Não é possível liberar {gramas}g. Ocupação atual: {self.capacidade_gramas_atual}g."
            )
            return False

        self.capacidade_gramas_atual -= gramas
        print(
            f"🟩 Liberou {gramas}g da fritadeira {self.nome}. "
            f"Ocupação atual: {self.capacidade_gramas_atual}/{self.capacidade_gramas_max}g."
        )
        return True

    def liberar_toda_capacidade_gramas(self):
        print(
            f"🟩 Liberou toda a capacidade em gramas da fritadeira {self.nome}. "
            f"Ocupação anterior: {self.capacidade_gramas_atual}g."
        )
        self.capacidade_gramas_atual = 0

    def gramas_disponiveis(self) -> int:
        return self.capacidade_gramas_max - self.capacidade_gramas_atual

    # ============================================
    # ⚙️ Setup Operacional
    # ============================================
    def configurar_setup(self, setup: int) -> bool:
        if setup < self.setup_min or setup > self.setup_max:
            print(
                f"❌ Setup {setup} fora dos limites. Permitido: {self.setup_min} a {self.setup_max}."
            )
            return False

        self.setup_atual = setup
        print(f"⚙️ Setup configurado para {setup} na fritadeira {self.nome}.")
        return True

    # ============================================
    # 🌡️ Controle de Temperatura
    # ============================================
    def configurar_faixa_temperatura(self, faixa: int) -> bool:
        if faixa < self.faixa_temperatura_min or faixa > self.faixa_temperatura_max:
            print(
                f"❌ Temperatura {faixa}°C fora dos limites permitidos. "
                f"Permitido: {self.faixa_temperatura_min}°C a {self.faixa_temperatura_max}°C."
            )
            return False

        self.faixa_temperatura_atual = faixa
        print(f"🌡️ Temperatura ajustada para {faixa}°C na fritadeira {self.nome}.")
        return True

    # ============================================
    # 🔍 Status e Representação
    # ============================================
    def __str__(self):
        return (
            super().__str__() +
            f"\n🧠 Capacidade fracionada: {self.capacidade_ocupada}/{self.capacidade_total} | Disponível: {self.fracao_disponivel()}"
            f"\n⚖️ Ocupação em gramas: {self.capacidade_gramas_atual}/{self.capacidade_gramas_max}g | Disponível: {self.gramas_disponiveis()}g"
            f"\n⚙️ Setup atual: {self.setup_atual} (Limites: {self.setup_min} a {self.setup_max})"
            f"\n🌡️ Temperatura atual: {self.faixa_temperatura_atual}°C (Faixa: {self.faixa_temperatura_min}°C a {self.faixa_temperatura_max}°C)"
        )
