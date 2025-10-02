#!/usr/bin/env python3
"""
🔍 ANÁLISE GENÉRICA DE CONFLITOS DE FUNCIONÁRIOS
===============================================

Script para analisar automaticamente TODOS os conflitos encontrados nos logs
de funcionários, sem necessidade de hardcoding de casos específicos.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from typing import List, Dict
from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios
from utils.analise.analisador_conflitos import AnalisadorConflitos


def analisar_todos_conflitos():
    """
    Analisa automaticamente todos os conflitos encontrados nos logs.
    """
    print("=" * 80)
    print("🔍 ANÁLISE GENÉRICA DE CONFLITOS - TODOS OS LOGS")
    print("=" * 80)

    # Inicializar gestor
    gestor = GestorFuncionarios()

    # Carregar alocações bem-sucedidas dos logs
    print("📋 Carregando alocações bem-sucedidas...")
    gestor.carregar_alocacoes_dos_logs()

    # Extrair conflitos automaticamente dos logs
    print("🔍 Extraindo conflitos dos logs...")
    conflitos = gestor.extrair_conflitos_dos_logs()

    if not conflitos:
        print("✅ Nenhum conflito encontrado nos logs!")
        return

    print(f"📋 Total de conflitos encontrados: {len(conflitos)}")
    print()

    # Inicializar analisador
    analisador = AnalisadorConflitos(gestor.funcionarios_disponiveis)

    # Agrupar conflitos por ordem|pedido para melhor organização
    conflitos_por_pedido = {}
    for conflito in conflitos:
        chave = f"Ordem {conflito['id_ordem']} | Pedido {conflito['id_pedido']}"
        if chave not in conflitos_por_pedido:
            conflitos_por_pedido[chave] = []
        conflitos_por_pedido[chave].append(conflito)

    # Analisar conflitos agrupados por pedido
    total_conflitos = 0
    for pedido, conflitos_pedido in conflitos_por_pedido.items():
        print(f"\n{'='*80}")
        print(f"📦 {pedido}")
        print(f"{'='*80}")
        print(f"📋 Conflitos encontrados: {len(conflitos_pedido)}")
        print()

        for i, conflito in enumerate(conflitos_pedido, 1):
            print(f"\n{'-'*60}")
            print(f"🔍 CONFLITO {i}/{len(conflitos_pedido)}")
            print(f"{'-'*60}")

            # Executar análise
            analise = analisador.analisar_falha_alocacao(
                conflito['id_atividade'],
                conflito['nome_atividade'],
                conflito['tipos_necessarios'],
                conflito['quantidade'],
                conflito['inicio'],
                conflito['fim']
            )

            # Gerar relatório
            relatorio = analisador.gerar_relatorio_conflito(analise)
            print(relatorio)

            # Adicionar informações específicas do log
            print(f"📄 Origem: {conflito['arquivo_origem']}")
            print(f"📅 Data/Hora: {conflito['inicio'].strftime('%d/%m/%Y %H:%M')} - {conflito['fim'].strftime('%H:%M')}")

            total_conflitos += 1

    # Resumo final
    print(f"\n{'='*80}")
    print("📊 RESUMO GERAL DA ANÁLISE")
    print(f"{'='*80}")
    print(f"📦 Pedidos com conflitos: {len(conflitos_por_pedido)}")
    print(f"⚠️ Total de conflitos analisados: {total_conflitos}")
    print()

    # Estatísticas por tipo de conflito
    analisar_estatisticas_conflitos(conflitos, analisador)

    # Sugestões gerais
    gerar_sugestoes_gerais(conflitos_por_pedido)


def analisar_estatisticas_conflitos(conflitos: List[Dict], analisador: AnalisadorConflitos):
    """
    Analisa estatísticas dos tipos de conflitos mais comuns.
    """
    print("📈 ESTATÍSTICAS DE CONFLITOS:")
    print("-" * 40)

    # Mapear conflitos por tipo profissional
    conflitos_por_tipo = {}
    conflitos_por_horario = {}

    for conflito in conflitos:
        # Por tipo profissional
        for tipo in conflito['tipos_necessarios']:
            tipo_nome = tipo.name
            if tipo_nome not in conflitos_por_tipo:
                conflitos_por_tipo[tipo_nome] = 0
            conflitos_por_tipo[tipo_nome] += 1

        # Por faixa horária
        hora = conflito['inicio'].hour
        faixa = f"{hora:02d}:00-{(hora+1):02d}:00"
        if faixa not in conflitos_por_horario:
            conflitos_por_horario[faixa] = 0
        conflitos_por_horario[faixa] += 1

    # Mostrar estatísticas
    print("🏷️ Conflitos por tipo profissional:")
    for tipo, count in sorted(conflitos_por_tipo.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {tipo}: {count} conflitos")

    print("\n⏰ Conflitos por faixa horária:")
    for faixa, count in sorted(conflitos_por_horario.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {faixa}: {count} conflitos")

    print()


def gerar_sugestoes_gerais(conflitos_por_pedido: Dict[str, List[Dict]]):
    """
    Gera sugestões gerais baseadas nos padrões de conflitos encontrados.
    """
    print("💡 SUGESTÕES GERAIS DE OTIMIZAÇÃO:")
    print("-" * 40)

    total_pedidos = len(conflitos_por_pedido)
    total_conflitos = sum(len(conflitos) for conflitos in conflitos_por_pedido.values())

    if total_conflitos > 5:
        print("🔄 Alta incidência de conflitos detectada. Considere:")
        print("   • Reorganizar sequenciamento de pedidos")
        print("   • Implementar sistema de prioridades mais flexível")
        print("   • Avaliar contratação de funcionários especializados")

    if total_pedidos > 3:
        print("📅 Múltiplos pedidos com conflitos. Considere:")
        print("   • Distribuir atividades ao longo de mais dias")
        print("   • Implementar processamento paralelo quando possível")
        print("   • Revisar capacidade de produção diária")

    # Identificar horários mais problemáticos
    horarios_conflito = []
    for conflitos in conflitos_por_pedido.values():
        for conflito in conflitos:
            horarios_conflito.append(conflito['inicio'].hour)

    if horarios_conflito:
        from collections import Counter
        horarios_mais_problematicos = Counter(horarios_conflito).most_common(3)

        print("⏰ Horários mais problemáticos:")
        for hora, count in horarios_mais_problematicos:
            print(f"   • {hora:02d}:00-{(hora+1):02d}:00: {count} conflitos")

        print("   💡 Considere redistribuir atividades desses horários")

    print()


def main():
    """Função principal do analisador genérico."""
    print("🚀 Iniciando análise genérica de conflitos...")

    try:
        analisar_todos_conflitos()
        print("✅ Análise genérica concluída com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())