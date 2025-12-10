#!/usr/bin/env python3
"""
📊 MÓDULO DE EXPORTAÇÃO DE ESCALAS
==================================

Módulo responsável por gerar planilhas Excel com escalas de funcionários
e suas atividades alocadas.

Classes disponíveis:
    - ParserLogsFuncionarios: Lê e processa logs de alocação de funcionários
    - GeradorEscalaExcel: Gera planilhas Excel com escalas formatadas

Funções disponíveis:
    - gerar_escala_funcionarios: Função utilitária para gerar escala
"""

from services.exportacao.escalas.parser_logs_funcionarios import ParserLogsFuncionarios
from services.exportacao.escalas.gerador_escala_excel import (
    GeradorEscalaExcel,
    gerar_escala_funcionarios
)

__all__ = [
    'ParserLogsFuncionarios',
    'GeradorEscalaExcel',
    'gerar_escala_funcionarios'
]
