"""
Otimizador v2.0 - PL Unificado
===============================

Sistema de otimização PL que funciona para:
- Modo DETERMINISTICO: gaps=0 (otimiza ordem de execução)
- Modo FLEXIVEL: gaps>0 (otimiza ordem e escolha de gaps) - Fase 2

API Principal:
    from otimizador_v2 import executar_pl_v2
    resultado = executar_pl_v2(pedidos, inicio_jornada)

Interface compatível com menu:
    from otimizador_v2 import ExecutorV2
    executor = ExecutorV2()
    executor.inicializar()
    solucao = executor.otimizar_pedidos(pedidos)

Criado em: 18/11/2025
"""

# Fase 1 - Modo Determinístico
from otimizador_v2.detector_modo import (
    DetectorModo,
    ModoOtimizacao,
    detectar_modo_otimizacao
)

from otimizador_v2.calculador_horarios_deterministicos import (
    CalculadorHorariosDeterministicos,
    calcular_horarios_deterministicos
)

from otimizador_v2.modelo_pl_ordenacao import (
    ModeloPLOrdenacao,
    otimizar_ordem_pedidos
)

from otimizador_v2.aplicador_ordenacao import (
    AplicadorOrdenacao,
    executar_pedidos_ordenados
)

from otimizador_v2.executor_unificado import (
    ExecutorUnificadoPL,
    executar_pl_v2
)

# Interface de compatibilidade com menu
from otimizador_v2.executor_v2 import (
    ExecutorV2,
    SolucaoPLCompleta,
    criar_executor_v2
)

__all__ = [
    # Detector de modo
    'DetectorModo',
    'ModoOtimizacao',
    'detectar_modo_otimizacao',

    # Calculador de horários
    'CalculadorHorariosDeterministicos',
    'calcular_horarios_deterministicos',

    # Modelo PL
    'ModeloPLOrdenacao',
    'otimizar_ordem_pedidos',

    # Aplicador
    'AplicadorOrdenacao',
    'executar_pedidos_ordenados',

    # Executor principal (API pública)
    'ExecutorUnificadoPL',
    'executar_pl_v2',

    # Interface de compatibilidade
    'ExecutorV2',
    'SolucaoPLCompleta',
    'criar_executor_v2',
]
