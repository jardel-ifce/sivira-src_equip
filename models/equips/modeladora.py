from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_produto_modelado import TipoProdutoModelado
from enums.tipo_atividade import TipoAtividade
from typing import List, Tuple
from datetime import datetime


class Modeladora(Equipamento):
    """
    Classe que representa uma Modeladora.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        tipo_produto_modelado: TipoProdutoModelado,
        capacidade_min_unidades_por_min: int,
        capacidade_max_unidades_por_min: int,
        numero_operadores: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.MODELADORAS,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True,
        )

        self.tipo_produto_modelado = tipo_produto_modelado
        self.capacidade_min_unidades_por_min = capacidade_min_unidades_por_min
        self.capacidade_max_unidades_por_min = capacidade_max_unidades_por_min
        self.capacidade_unidades_atual = 0

        self.ocupacao: List[Tuple[datetime, datetime, TipoAtividade]] = []

    # ============================================
    # 🏗️ Ocupação de Unidades
    # ============================================
    def ocupar_capacidade_unidades(self, quantidade: int) -> bool:
        if quantidade < self.capacidade_min_unidades_por_min:
            print(
                f"❌ Quantidade {quantidade} abaixo do mínimo permitido ({self.capacidade_min_unidades_por_min}) na modeladora {self.nome}."
            )
            return False

        if self.capacidade_unidades_atual + quantidade > self.capacidade_max_unidades_por_min:
            print(
                f"❌ Modeladora {self.nome} sem capacidade suficiente. "
                f"Máximo permitido: {self.capacidade_max_unidades_por_min}. "
                f"Disponível: {self.unidades_disponiveis()} unidades."
            )
            return False

        self.capacidade_unidades_atual += quantidade
        print(
            f"✅ Ocupou {quantidade} unidades na modeladora {self.nome}. "
            f"Ocupação atual: {self.capacidade_unidades_atual}/{self.capacidade_max_unidades_por_min} unidades."
        )
        return True

    def liberar_capacidade_unidades(self, quantidade: int) -> bool:
        if self.capacidade_unidades_atual - quantidade < 0:
            print(
                f"❌ Não é possível liberar {quantidade} unidades. "
                f"Apenas {self.capacidade_unidades_atual} estão ocupadas."
            )
            return False

        self.capacidade_unidades_atual -= quantidade
        print(
            f"🟩 Liberou {quantidade} unidades da modeladora {self.nome}. "
            f"Ocupação atual: {self.capacidade_unidades_atual}/{self.capacidade_max_unidades_por_min} unidades."
        )
        return True

    def liberar_toda_capacidade(self):
        print(
            f"🟩 Liberou toda a capacidade ocupada ({self.capacidade_unidades_atual} unidades) da modeladora {self.nome}."
        )
        self.capacidade_unidades_atual = 0

    def unidades_disponiveis(self) -> int:
        return self.capacidade_max_unidades_por_min - self.capacidade_unidades_atual

    # ============================================
    # 🔍 Status e Representação
    # ============================================
    def __str__(self):
        return (
            super().__str__() +
            f"\n🛠️ Tipo de Produto Modelado: {self.tipo_produto_modelado.name}"
            f"\n📦 Capacidade mínima: {self.capacidade_min_unidades_por_min} unidades/min"
            f"\n📦 Capacidade máxima: {self.capacidade_max_unidades_por_min} unidades/min"
            f"\n📦 Ocupação atual: {self.capacidade_unidades_atual} unidades | Disponível: {self.unidades_disponiveis()} unidades"
        )
