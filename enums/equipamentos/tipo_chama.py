"""
Enumeração de intensidade de chama.

Define os níveis de intensidade de chama para equipamentos a gás.
"""

from enum import Enum


class TipoChama(Enum):
    """
    Intensidades de chama.

    Attributes:
        BAIXA: Chama de baixa intensidade
        MEDIA: Chama de média intensidade
        ALTA: Chama de alta intensidade
    """
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"

    def __str__(self):
        """
        Retorna a representação textual da intensidade.

        Returns:
            str: Descrição da intensidade de chama
        """
        return self.value