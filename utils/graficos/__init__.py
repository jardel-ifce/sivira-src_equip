#!/usr/bin/env python3
"""
📊 MÓDULO DE GERAÇÃO DE GRÁFICOS
================================

Módulo responsável por gerar gráficos de visualização para o sistema.

Classes disponíveis:
    - GeradorGantt: Gera gráficos de Gantt para escalas de funcionários

Funções disponíveis:
    - gerar_gantt_funcionarios: Função utilitária para gerar Gantt
"""

from utils.graficos.gerador_gantt import (
    GeradorGantt,
    gerar_gantt_funcionarios
)

__all__ = [
    'GeradorGantt',
    'gerar_gantt_funcionarios'
]
