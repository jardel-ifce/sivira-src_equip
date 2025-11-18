"""
Otimizador v2.0 - Modelo PL Completo
=====================================

Módulo de otimização corrigido que modela TODAS as restrições:
- tempo_maximo_de_espera entre atividades
- Equipamentos como recursos limitados
- Conflitos temporais SEM orçamento arbitrário

Correções às 3 deficiências identificadas na análise comparativa.

Uso rápido:
    from otimizador_v2 import executar_otimizacao_rapida
    solucao = executar_otimizacao_rapida('data/csv/exemplo_pedidos.csv')

Uso avançado:
    from otimizador_v2 import ExecutorV2
    executor = ExecutorV2()
    executor.inicializar()
    solucao = executor.otimizar_csv('data/csv/exemplo_pedidos.csv')
"""

# Modelo PL
from otimizador_v2.modelo_pl_completo import ModeloPLCompleto, SolucaoPLCompleta

# Otimizador integrado
from otimizador_v2.otimizador_integrado_v2 import OtimizadorIntegradoV2, criar_otimizador_v2

# Adaptadores e interfaces
from otimizador_v2.adaptador_dados import (
    AdaptadorDados,
    FabricaAdaptador,
    carregar_pedidos_csv,
    extrair_dados_pedidos
)

# Executor de alto nível
from otimizador_v2.executor_v2 import ExecutorV2, executar_otimizacao_rapida

__all__ = [
    # Modelo PL
    'ModeloPLCompleto',
    'SolucaoPLCompleta',

    # Otimizador
    'OtimizadorIntegradoV2',
    'criar_otimizador_v2',

    # Adaptadores
    'AdaptadorDados',
    'FabricaAdaptador',
    'carregar_pedidos_csv',
    'extrair_dados_pedidos',

    # Executor (Interface principal)
    'ExecutorV2',
    'executar_otimizacao_rapida',
]
