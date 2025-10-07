"""
Enumeração de políticas de produção.

Define os modos de produção para itens do sistema.
"""

from enum import Enum


class PoliticaProducao(Enum):
    """
    Políticas de produção para itens.

    Attributes:
        SOB_DEMANDA: Produzido apenas quando necessário
        ESTOCADO: Mantém estoque físico, requer reabastecimento
        AMBOS: Pode operar em ambos os modos
    """
    SOB_DEMANDA = "SOB_DEMANDA"
    ESTOCADO = "ESTOCADO"
    AMBOS = "AMBOS"

    def __str__(self):
        """
        Retorna a representação textual do modo de produção.

        Returns:
            str: Nome da política de produção
        """
        return self.name