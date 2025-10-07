"""
Enumeração de unidades de capacidade de equipamentos.

Define as unidades para especificar capacidade de equipamentos.
"""

from enum import Enum


class CapacidadeUnidade(Enum):
    """
    Unidades de capacidade de equipamentos.

    Attributes:
        CM2: Área em centímetros quadrados
        CM3: Volume em centímetros cúbicos
        NIVEIS: Quantidade de níveis (prateleiras, bandejas)
        OPERADORES: Número de operadores simultâneos
        GRAMAS: Capacidade em gramas
        LITROS: Capacidade em litros
        QUILOS: Capacidade em quilogramas
    """
    CM2 = "Cm2"
    CM3 = "Cm3"
    NIVEIS = "Niveis"
    OPERADORES = "Operadores"
    GRAMAS = "Gramas"
    LITROS = "Litros"
    QUILOS = "Quilos"