"""
Enumeração de funções profissionais.

Define as funções hierárquicas disponíveis no sistema de produção.
"""

from enum import Enum


class TipoFuncao(Enum):
    """
    Funções profissionais hierárquicas.

    Attributes:
        CHEFE_SALGADEIRO: Responsável pelo setor de salgados
        SALGADEIRO: Profissional de produção de salgados
        AJUDANTE_DE_COZINHA: Assistente de cozinha
        CHEFE_CONFEITEIRO: Responsável pelo setor de confeitaria
        CONFEITEIRO: Profissional de confeitaria
        AJUDANTE_DE_CONFEITARIA: Assistente de confeitaria
        AJUDANTE_DE_SALGADOS: Assistente do setor de salgados
    """
    CHEFE_SALGADEIRO = "Chefe Salgadeiro"
    SALGADEIRO = "Salgadeiro"
    AJUDANTE_DE_COZINHA = "Ajudante de Cozinha"
    CHEFE_CONFEITEIRO = "Chefe Confeiteiro"
    CONFEITEIRO = "Confeiteiro"
    AJUDANTE_DE_CONFEITARIA = "Ajudante de Confeitaria"
    AJUDANTE_DE_SALGADOS = "Ajudante de Salgados"