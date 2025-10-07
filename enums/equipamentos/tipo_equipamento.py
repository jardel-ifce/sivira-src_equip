"""
Enumeração de tipos de equipamentos.

Define as categorias de equipamentos disponíveis no sistema de produção.
"""

from enum import Enum


class TipoEquipamento(Enum):
    """
    Tipos de equipamentos na produção de alimentos.

    Attributes:
        MISTURADORAS: Equipamentos para mistura de ingredientes
        BANCADAS: Superfícies de trabalho
        BALANCAS: Equipamentos de pesagem
        FORNOS: Equipamentos de cocção por calor
        MISTURADORAS_COM_COCCAO: Equipamentos que misturam e cozinham (ex: HotMix)
        FOGOES: Fogões para cocção direta
        REFRIGERACAO_CONGELAMENTO: Equipamentos de refrigeração
        EMBALADORAS: Máquinas de embalagem
        MODELADORAS: Equipamentos para modelagem de massas
        DIVISORAS_BOLEADORAS: Equipamentos para divisão e boleamento
        BATEDEIRAS: Equipamentos para bater e aeração
        FRITADEIRAS: Equipamentos para fritura
        ARMARIOS_PARA_FERMENTACAO: Câmaras de fermentação controlada
    """
    MISTURADORAS = "Misturadoras"
    BANCADAS = "Bancadas"
    BALANCAS = "Balanças"
    FORNOS = "Fornos"
    MISTURADORAS_COM_COCCAO = "Misturadoras com Cocção"
    FOGOES = "Fogões"
    REFRIGERACAO_CONGELAMENTO = "Refrigeração e Congelamento"
    EMBALADORAS = "Embaladoras"
    MODELADORAS = "Modeladoras"
    DIVISORAS_BOLEADORAS = "Divisoras e Boleadoras"
    BATEDEIRAS = "Batedeiras"
    FRITADEIRAS = "Fritadeiras"
    ARMARIOS_PARA_FERMENTACAO = "Armários para Fermentação"
