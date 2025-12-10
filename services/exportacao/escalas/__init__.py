#!/usr/bin/env python3
"""
📊 MÓDULO DE EXPORTAÇÃO DE ESCALAS
==================================

Módulo responsável por gerar arquivos CSV/Excel com escalas de funcionários
e suas atividades alocadas.

Classes disponíveis:
    - ParserLogsFuncionarios: Lê e processa logs de alocação de funcionários
    - GeradorEscalaCSV: Gera arquivos CSV com escalas formatadas
    - GeradorEscalaExcel: Gera planilhas Excel com escalas formatadas

Funções disponíveis:
    - gerar_escala_funcionarios: Função utilitária para gerar escala CSV
"""

from services.exportacao.escalas.parser_logs_funcionarios import ParserLogsFuncionarios
from services.exportacao.escalas.gerador_escala_csv import (
    GeradorEscalaCSV,
    gerar_escala_funcionarios
)
from services.exportacao.escalas.gerador_escala_excel import GeradorEscalaExcel

__all__ = [
    'ParserLogsFuncionarios',
    'GeradorEscalaCSV',
    'GeradorEscalaExcel',
    'gerar_escala_funcionarios'
]
