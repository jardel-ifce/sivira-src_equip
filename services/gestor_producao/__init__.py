"""
Gestor de Produção
==================

Módulo independente para gerenciar execução de pedidos de produção.
Desacoplado dos scripts de teste (producao_paes*).

Exemplo de uso:
    from services.gestor_producao import GestorProducao
    
    gestor = GestorProducao()
    sucesso = gestor.executar_sequencial(pedidos)
"""

from .gestor_producao import GestorProducao
from .configurador_ambiente import ConfiguradorAmbiente
from .conversor_pedidos import ConversorPedidos
from .executor_pedidos import ExecutorPedidos

__all__ = [
    'GestorProducao',
    'ConfiguradorAmbiente', 
    'ConversorPedidos',
    'ExecutorPedidos'
]

__version__ = '1.0.0'
__author__ = 'Sistema de Produção'
__description__ = 'Gestor independente de produção desacoplado dos scripts de teste'