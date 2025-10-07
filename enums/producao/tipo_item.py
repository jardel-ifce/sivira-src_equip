"""
Enumeração de tipos de itens do sistema de produção.

Define as categorias de itens gerenciados no almoxarifado.
"""

from enum import Enum


class TipoItem(Enum):
    """
    Categorias de itens no sistema de produção.

    Attributes:
        PRODUTO: Item final comercializável
        SUBPRODUTO: Componente intermediário usado em produtos
        INSUMO: Matéria-prima base
    """
    PRODUTO = "PRODUTO"
    SUBPRODUTO = "SUBPRODUTO"
    INSUMO = "INSUMO"