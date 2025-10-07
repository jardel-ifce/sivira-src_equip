"""
Enumeração de dias da semana.

Define os dias da semana para agendamento e controle de jornada.
"""

from enum import Enum


class DiaSemana(Enum):
    """
    Dias da semana.

    Attributes:
        SEGUNDA: Segunda-feira
        TERCA: Terça-feira
        QUARTA: Quarta-feira
        QUINTA: Quinta-feira
        SEXTA: Sexta-feira
        SABADO: Sábado
        DOMINGO: Domingo
    """
    SEGUNDA = "Segunda-feira"
    TERCA = "Terça-feira"
    QUARTA = "Quarta-feira"
    QUINTA = "Quinta-feira"
    SEXTA = "Sexta-feira"
    SABADO = "Sábado"
    DOMINGO = "Domingo"