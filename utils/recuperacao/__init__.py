"""
Módulo de Recuperação de Estado de Equipamentos
================================================

Sistema completo para recuperar estado de equipamentos a partir de logs detalhados.

Componentes principais:
- RecuperadorEstado: Orquestrador principal
- DetectorLogs: Detecta e valida logs disponíveis
- Parsers: Extraem ocupações dos logs (um por tipo de equipamento)
- Restauradores: Aplicam ocupações nos objetos (um por tipo de equipamento)
- Validadores: Validam integridade da recuperação
- DTOs: Modelos de dados para transferência de informações

Uso básico:
    from utils.recuperacao import RecuperadorEstado

    recuperador = RecuperadorEstado()
    relatorio = recuperador.recuperar_de_log("caminho/para/log.log")

    if relatorio.sucesso:
        print(f"Recuperados {relatorio.total_ocupacoes_recuperadas} ocupações")
    else:
        print("Falha na recuperação")
        for erro in relatorio.erros_globais:
            print(f"  - {erro}")

Estrutura do módulo:
    utils/recuperacao/
    ├── __init__.py                  # Este arquivo
    ├── recuperador_estado.py        # Orquestrador principal
    ├── detector_logs.py             # Detector de logs
    ├── modelos/                     # DTOs
    │   ├── ocupacao_dto.py
    │   ├── estado_equipamento_dto.py
    │   └── relatorio_recuperacao_dto.py
    ├── parsers/                     # Parsers por tipo
    │   ├── parser_base.py
    │   ├── parser_bancada.py
    │   ├── parser_camara_refrigerada.py
    │   └── ...
    ├── restauradores/               # Restauradores por tipo
    │   ├── restaurador_base.py
    │   ├── restaurador_bancada.py
    │   ├── restaurador_camara_refrigerada.py
    │   └── ...
    └── validadores/                 # Validadores
        ├── validador_ocupacoes.py
        └── validador_consistencia.py

Autor: Sistema SIVIRA
Data: Outubro 2025
"""

from .recuperador_estado import RecuperadorEstado
from .detector_logs import DetectorLogs

# Exportar DTOs principais
from .modelos import (
    OcupacaoDTO,
    EstadoEquipamentoDTO,
    RelatorioRecuperacaoDTO
)

# Exportar validadores
from .validadores import (
    ValidadorOcupacoes,
    ValidadorConsistencia
)

__all__ = [
    # Principal
    'RecuperadorEstado',
    'DetectorLogs',

    # DTOs
    'OcupacaoDTO',
    'EstadoEquipamentoDTO',
    'RelatorioRecuperacaoDTO',

    # Validadores
    'ValidadorOcupacoes',
    'ValidadorConsistencia'
]

__version__ = '1.0.0'
__author__ = 'Sistema SIVIRA'
