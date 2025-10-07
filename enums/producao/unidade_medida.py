"""
Enumeração de unidades de medida.

Define as unidades de medida utilizadas no sistema para quantificação de itens e recursos.
"""

from enum import Enum


class UnidadeMedida(Enum):
    """
    Unidades de medida do sistema.

    Attributes:
        GRAMAS: Peso em gramas
        LITROS: Volume em litros
        METROS: Comprimento em metros
        CENTIMETROS: Comprimento em centímetros
        MILILITROS: Volume em mililitros
        UNIDADE: Contagem por unidades
        PORCOES: Contagem por porções
        FUNCIONARIOS: Quantidade de funcionários
        UNIDADES_POR_HORA: Taxa de produção
        COLHERES: Medida culinária em colheres
        XICARAS: Medida culinária em xícaras
    """
    GRAMAS = "GRAMAS"
    LITROS = "LITROS"
    METROS = "METROS"
    CENTIMETROS = "CENTIMETROS"
    MILILITROS = "MILILITROS"
    UNIDADE = "UNIDADE"
    PORCOES = "PORCOES"
    FUNCIONARIOS = "FUNCIONARIOS"
    UNIDADES_POR_HORA = "UNIDADES_POR_HORA"
    COLHERES = "COLHERES"
    XICARAS = "XICARAS"

    def __str__(self):
        """
        Retorna uma representação textual da unidade de medida.

        Returns:
            str: Nome da unidade de medida
        """
        return self.value