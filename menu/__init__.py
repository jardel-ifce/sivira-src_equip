"""
Módulo Menu - Sistema de Produção
=================================

Sistema de menu interativo para registro e execução de pedidos
com suporte a otimização por Programação Linear.

Estrutura:
- main_menu.py: Menu principal e interface do usuário
- gerenciador_pedidos.py: Gerenciamento de pedidos (registrar, listar, converter)
- executor_producao.py: Execução sequencial e otimizada
- utils_menu.py: Utilitários e validações

Uso:
    python main_menu.py
    
    ou
    
    from menu.main_menu import MenuPrincipal
    menu = MenuPrincipal()
    menu.executar()
"""

__version__ = "1.0.0"
__author__ = "Sistema de Produção"

# Importações principais
from .main_menu import MenuPrincipal
from .gerenciador_pedidos import GerenciadorPedidos, DadosPedidoMenu
from .executor_producao import ExecutorProducao
from .utils_menu import MenuUtils

__all__ = [
    'MenuPrincipal',
    'GerenciadorPedidos', 
    'DadosPedidoMenu',
    'ExecutorProducao',
    'MenuUtils'
]