"""
Módulo de DTOs para Recuperação de Estado
==========================================

Data Transfer Objects para transportar dados entre parsers e restauradores.
"""

from .ocupacao_dto import OcupacaoDTO
from .estado_equipamento_dto import EstadoEquipamentoDTO
from .relatorio_recuperacao_dto import RelatorioRecuperacaoDTO

__all__ = [
    'OcupacaoDTO',
    'EstadoEquipamentoDTO',
    'RelatorioRecuperacaoDTO'
]
