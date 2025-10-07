"""
Enumeração de tipos de folga.

Define os padrões de folga para funcionários.
"""

from enum import Enum


class TipoFolga(Enum):
    """
    Tipos de padrões de folga.

    Attributes:
        DIA_FIXO_SEMANA: Folga em dia fixo da semana (ex: toda segunda)
        DIA_FIXO_MES: Folga em dia fixo do mês (ex: todo dia 15)
        N_DIA_SEMANA_DO_MES: Folga no n-ésimo dia da semana do mês (ex: segunda segunda-feira)
    """
    DIA_FIXO_SEMANA = "dia_fixo_semana"
    DIA_FIXO_MES = "dia_fixo_mes"
    N_DIA_SEMANA_DO_MES = "n_dia_semana_do_mes"