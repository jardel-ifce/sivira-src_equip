from enum import Enum

class TipoSetor(Enum):
    """
    Enumeração que representa os setores da produção de alimentos.
    """
    PANIFICACAO = "Panificação"
    SALGADOS = "Salgados"
    CONFEITARIA = "Confeitaria"
    ALMOXARIFADO = "Almoxarifado"
    COZINHA = "Cozinha"
