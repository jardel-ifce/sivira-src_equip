"""
Enumeração de setores de produção.

Define os setores operacionais do sistema de produção de alimentos.
"""

from enum import Enum


class TipoSetor(Enum):
    """
    Setores da produção de alimentos.

    Attributes:
        PANIFICACAO: Setor de panificação
        SALGADOS: Setor de produção de salgados
        CONFEITARIA: Setor de confeitaria
        ALMOXARIFADO: Setor de armazenamento e controle de estoque
        COZINHA: Setor de cozinha geral
    """
    PANIFICACAO = "Panificação"
    SALGADOS = "Salgados"
    CONFEITARIA = "Confeitaria"
    ALMOXARIFADO = "Almoxarifado"
    COZINHA = "Cozinha"