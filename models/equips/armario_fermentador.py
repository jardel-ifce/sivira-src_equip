from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_atividade import TipoAtividade
from typing import List, Tuple
from datetime import datetime


class ArmarioFermentador(Equipamento):
    """
    Classe que representa um Armário de Fermentação.
    Controle da ocupação por níveis de tela.
    """

    # =============================================
    # 🔧 Inicialização
    # =============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        nivel_tela_min: int,
        nivel_tela_max: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.ARMARIOS_PARA_FERMENTACAO,
            setor=setor,
            numero_operadores=0,
            status_ativo=True
        )

        self.nivel_tela_min = nivel_tela_min
        self.nivel_tela_max = nivel_tela_max
        self.nivel_tela_atual = 0
        self.ocupacao: List[Tuple[datetime, datetime, TipoAtividade]] = []

    # =============================================
    # 🗂️ Ocupação por Níveis de Tela
    # =============================================
    def ocupar(self, niveis: int) -> bool:
        """
        Ocupa uma quantidade de níveis de tela.
        """
        if self.nivel_tela_atual + niveis > self.nivel_tela_max:
            print(
                f"❌ {self.nome} | Não é possível ocupar {niveis} níveis. "
                f"Capacidade máxima: {self.nivel_tela_max}. Ocupados atualmente: {self.nivel_tela_atual}."
            )
            return False

        self.nivel_tela_atual += niveis
        print(
            f"✅ {self.nome} | Ocupou {niveis} níveis. "
            f"Ocupação atual: {self.nivel_tela_atual}/{self.nivel_tela_max}."
        )
        return True

    def liberar(self, niveis: int) -> bool:
        """
        Libera uma quantidade de níveis de tela.
        """
        self.nivel_tela_atual -= niveis

        if self.nivel_tela_atual < 0:
            print(
                f"⚠️ {self.nome} | Tentou liberar {niveis} níveis, excedendo o ocupado. "
                "Resetando ocupação para 0."
            )
            self.nivel_tela_atual = 0
            return False

        print(
            f"🟩 {self.nome} | Liberou {niveis} níveis. "
            f"Ocupação atual: {self.nivel_tela_atual}/{self.nivel_tela_max}."
        )
        return True

    def niveis_disponiveis(self) -> int:
        """
        Retorna o número de níveis de tela disponíveis para ocupação.
        """
        return self.nivel_tela_max - self.nivel_tela_atual

    # =============================================
    # 🔍 Status e Visualização
    # =============================================
    def __str__(self):
        return (
            super().__str__() +
            f"\n🗂️ Níveis de Tela Ocupados: {self.nivel_tela_atual}/{self.nivel_tela_max}"
            f"\n🧠 Níveis Disponíveis: {self.niveis_disponiveis()}"
            f"\n🟦 Status: {'Ocupado' if self.nivel_tela_atual > 0 else 'Disponível'}"
        )
