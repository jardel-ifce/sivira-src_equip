"""
Enumeração de tipos de produtos modelados.

Define as categorias de produtos que passam por processo de modelagem.
"""

from enum import Enum


class TipoProdutoModelado(Enum):
    """
    Tipos de produtos que requerem modelagem.

    Attributes:
        PAES: Produtos de panificação
        SALGADOS: Produtos salgados modelados
    """
    PAES = "Pães"
    SALGADOS = "Salgados"