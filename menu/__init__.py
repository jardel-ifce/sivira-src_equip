"""
Menu do Sistema de Produção - DESACOPLADO
==========================================

Módulo do menu interativo para registro e execução de pedidos.
Agora usa a nova arquitetura services/gestor_producao.

✅ NOVIDADES:
- Desacoplado dos scripts de teste (producao_paes*)
- Usa services/gestor_producao
- Arquitetura independente e limpa
"""

from .gerenciador_pedidos import GerenciadorPedidos, DadosPedidoMenu
from .utils_menu import MenuUtils

# ❌ REMOVIDO: ExecutorProducao (substituído por services/gestor_producao)
# from .executor_producao import ExecutorProducao

__all__ = [
    'GerenciadorPedidos',
    'DadosPedidoMenu', 
    'MenuUtils'
]

__version__ = '2.0.0'
__author__ = 'Sistema de Produção'
__description__ = 'Menu interativo desacoplado com nova arquitetura independente'