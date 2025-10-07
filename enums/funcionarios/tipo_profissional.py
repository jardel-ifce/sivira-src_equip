"""
Enumeração de tipos profissionais.

Define as qualificações profissionais disponíveis no sistema de produção.
"""

from enum import Enum


class TipoProfissional(Enum):
    """
    Tipos de profissionais na produção de alimentos.

    Attributes:
        PADEIRO: Profissional especializado em panificação
        AUXILIAR_DE_PADEIRO: Assistente de padeiro
        ALMOXARIFE: Responsável pelo almoxarifado e estoque
        COZINHEIRO: Profissional de culinária geral
        CONFEITEIRO: Especialista em confeitaria
        AUXILIAR_DE_CONFEITEIRO: Assistente de confeiteiro
    """
    PADEIRO = "Padeiro"
    AUXILIAR_DE_PADEIRO = "Auxiliar de Padeiro"
    ALMOXARIFE = "Almoxarife"
    COZINHEIRO = "Cozinheiro"
    CONFEITEIRO = "Confeiteiro"
    AUXILIAR_DE_CONFEITEIRO = "Auxiliar de Confeiteiro"

    def __str__(self):
        """
        Retorna a representação textual do tipo profissional.

        Returns:
            str: Nome da profissão
        """
        return self.value