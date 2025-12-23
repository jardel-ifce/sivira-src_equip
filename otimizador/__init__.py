"""
Otimizador PL - Otimizador Unificado
====================================

Versao unificada que suporta ambos os modos:
- DETERMINISTICO: tempo_maximo_de_espera = 0 (atividades contiguas)
- FLEXIVEL: tempo_maximo_de_espera > 0 (janelas flexiveis)

Fluxo de Execucao:
1. FASE 0: Criar atividades modulares
2. FASE 1: Detectar modo (DETERMINISTICO ou FLEXIVEL)
3. FASE 2: Calcular horarios/janelas
4. FASE 3: Otimizar ordem via PL
5. FASE 4: Executar pedidos
"""

from otimizador.executor import Executor, Solucao, criar_executor
from otimizador.detector_modo import DetectorModo, ModoOtimizacao, detectar_modo_otimizacao
from otimizador.calculador_horarios_deterministicos import CalculadorHorariosDeterministicos
from otimizador.modelo_pl_ordenacao import ModeloPLOrdenacao
from otimizador.aplicador_ordenacao import AplicadorOrdenacao
from otimizador.calculador_janelas import CalculadorJanelas, JanelaFlexivel
from otimizador.aplicador_flexivel import AplicadorFlexivel

# Aliases para compatibilidade com codigo legado
ExecutorV3 = Executor
SolucaoV3 = Solucao
criar_executor_v3 = criar_executor
ExecutorUnificadoPL = Executor

__all__ = [
    'Executor',
    'Solucao',
    'criar_executor',
    'DetectorModo',
    'ModoOtimizacao',
    'detectar_modo_otimizacao',
    'CalculadorHorariosDeterministicos',
    'ModeloPLOrdenacao',
    'AplicadorOrdenacao',
    'CalculadorJanelas',
    'JanelaFlexivel',
    'AplicadorFlexivel',
    # Aliases para compatibilidade
    'ExecutorV3',
    'SolucaoV3',
    'criar_executor_v3',
    'ExecutorUnificadoPL',
]
