from enum import Enum

class TipoProfissional(Enum):
    """
    Enumeração que representa os tipos de profissionais existentes na produção de alimentos.
    """
    PADEIRO = "Padeiro"
    AUXILIAR_DE_PADEIRO = "Auxiliar de Padeiro"
    ALMOXARIFE = "Almoxarife"
    COZINHEIRO = "Cozinheiro"
    CONFEITEIRO = "Confeiteiro"
    AUXILIAR_DE_CONFEITEIRO = "Auxiliar de Confeiteiro"
    def __str__(self):
        return self.value