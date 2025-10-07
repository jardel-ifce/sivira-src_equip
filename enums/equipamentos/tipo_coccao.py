"""
Enumeração de tipos de cocção.

Define os modos de cocção disponíveis em fornos e equipamentos de cozimento.
"""

from enum import Enum


class TipoCoccao(Enum):
    """
    Tipos de cocção de equipamentos.

    Attributes:
        TURBO: Cocção com ventilação forçada
        LASTRO: Cocção por contato direto com superfície aquecida
        COMBINADO: Cocção que combina turbo e lastro
        CONTINUO: Cocção em esteira contínua
    """
    TURBO = "Turbo"
    LASTRO = "Lastro"
    COMBINADO = "Combinado"
    CONTINUO = "Continuo"

    def __str__(self):
        """
        Retorna a representação textual do tipo de cocção.

        Returns:
            str: Descrição do tipo de cocção
        """
        return self.value
