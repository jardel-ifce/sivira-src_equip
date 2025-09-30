#!/usr/bin/env python3
"""
🔍 ANÁLISE DE CONFLITOS DE FUNCIONÁRIOS
======================================

Script para analisar conflitos específicos de alocação de funcionários
e demonstrar a estratégia de análise implementada.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import List, Dict
from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios
from utils.analise.analisador_conflitos import AnalisadorConflitos
from enums.funcionarios.tipo_profissional import TipoProfissional

def analisar_conflitos_ordem_1_pedido_6():
    """
    Analisa os conflitos específicos da Ordem 1, Pedido 6
    baseado nos logs existentes.
    """
    print("=" * 80)
    print("🔍 ANÁLISE DETALHADA DE CONFLITOS - ORDEM 1 | PEDIDO 6")
    print("=" * 80)

    # Inicializar gestor
    gestor = GestorFuncionarios()
    analisador = AnalisadorConflitos(gestor.funcionarios_disponiveis)

    # Conflitos identificados nos logs
    conflitos_identificados = [
        {
            'id_atividade': 20091,
            'nome': 'preparo_para_coccao_de_frango_cozido_pronto',
            'inicio': datetime(2024, 6, 26, 5, 46),
            'fim': datetime(2024, 6, 26, 5, 54),
            'tipos_necessarios': [TipoProfissional.COZINHEIRO],
            'quantidade': 1
        },
        {
            'id_atividade': 20092,
            'nome': 'coccao_de_frango_cozido_pronto',
            'inicio': datetime(2024, 6, 26, 5, 54),
            'fim': datetime(2024, 6, 26, 6, 4),
            'tipos_necessarios': [TipoProfissional.COZINHEIRO],
            'quantidade': 1
        },
        {
            'id_atividade': 20093,
            'nome': 'preparo_para_armazenamento_de_frango_refogado',
            'inicio': datetime(2024, 6, 26, 6, 4),
            'fim': datetime(2024, 6, 26, 6, 24),
            'tipos_necessarios': [TipoProfissional.COZINHEIRO],
            'quantidade': 1
        },
        {
            'id_atividade': 20031,
            'nome': 'mistura_de_massas_para_frituras',
            'inicio': datetime(2024, 6, 26, 6, 15),
            'fim': datetime(2024, 6, 26, 6, 27),
            'tipos_necessarios': [TipoProfissional.AUXILIAR_DE_CONFEITEIRO, TipoProfissional.CONFEITEIRO],
            'quantidade': 1
        },
        {
            'id_atividade': 10551,
            'nome': 'modelagem_e_recheio_de_coxinhas_de_frango',
            'inicio': datetime(2024, 6, 26, 6, 27),
            'fim': datetime(2024, 6, 26, 6, 47),
            'tipos_necessarios': [TipoProfissional.AUXILIAR_DE_CONFEITEIRO, TipoProfissional.CONFEITEIRO],
            'quantidade': 2
        },
        {
            'id_atividade': 10556,
            'nome': 'fritura_de_coxinhas_de_frango',
            'inicio': datetime(2024, 6, 26, 7, 56),
            'fim': datetime(2024, 6, 26, 8, 0),
            'tipos_necessarios': [TipoProfissional.CONFEITEIRO],
            'quantidade': 1
        }
    ]

    print(f"📋 Total de conflitos para análise: {len(conflitos_identificados)}")
    print()

    # Analisar cada conflito
    for i, conflito in enumerate(conflitos_identificados, 1):
        print(f"\n{'='*60}")
        print(f"🔍 ANÁLISE {i}/{len(conflitos_identificados)}")
        print(f"{'='*60}")

        analise = analisador.analisar_falha_alocacao(
            conflito['id_atividade'],
            conflito['nome'],
            conflito['tipos_necessarios'],
            conflito['quantidade'],
            conflito['inicio'],
            conflito['fim']
        )

        # Gerar relatório detalhado
        relatorio = analisador.gerar_relatorio_conflito(analise)
        print(relatorio)

        # Análise específica dos funcionários ocupados
        print("\n🔎 ANÁLISE ESPECÍFICA DE OCUPAÇÕES:")
        print("-" * 40)

        funcionarios_ocupados = []
        for funcionario in gestor.funcionarios_disponiveis:
            # Verificar se o funcionário tem qualificação necessária
            tipos_funcionario = set(funcionario.tipo_profissional)
            tipos_requeridos = set(conflito['tipos_necessarios'])

            if tipos_funcionario.intersection(tipos_requeridos):
                # Verificar ocupações no período
                for ocupacao in funcionario.ocupacoes:
                    ordem_oc, pedido_oc, ativ_oc, nome_oc, inicio_oc, fim_oc = ocupacao

                    # Verificar sobreposição temporal
                    if not (conflito['fim'] <= inicio_oc or conflito['inicio'] >= fim_oc):
                        funcionarios_ocupados.append({
                            'funcionario': funcionario,
                            'ocupacao': ocupacao,
                            'sobreposicao_inicio': max(conflito['inicio'], inicio_oc),
                            'sobreposicao_fim': min(conflito['fim'], fim_oc)
                        })

        if funcionarios_ocupados:
            print("❌ Funcionários qualificados ocupados:")
            for ocupado in funcionarios_ocupados:
                func = ocupado['funcionario']
                ocupacao = ocupado['ocupacao']
                ordem_oc, pedido_oc, ativ_oc, nome_oc, inicio_oc, fim_oc = ocupacao

                tipos_str = ', '.join([t.name for t in func.tipo_profissional])
                print(f"   • Funcionário {func.id} ({tipos_str}):")
                print(f"     📍 Ocupado: {inicio_oc.strftime('%H:%M')} - {fim_oc.strftime('%H:%M')}")
                print(f"     🎯 Atividade: {nome_oc} (Ordem {ordem_oc}, Pedido {pedido_oc})")
                print(f"     ⚠️  Conflito: {ocupado['sobreposicao_inicio'].strftime('%H:%M')} - {ocupado['sobreposicao_fim'].strftime('%H:%M')}")
                print()
        else:
            print("ℹ️  Nenhum funcionário qualificado encontrado para este tipo de atividade")

    print("\n" + "="*80)
    print("📊 RESUMO GERAL DOS CONFLITOS")
    print("="*80)

    # Mapear ocupações por funcionário e pedido
    ocupacoes_por_pedido = {}
    for funcionario in gestor.funcionarios_disponiveis:
        for ocupacao in funcionario.ocupacoes:
            ordem_oc, pedido_oc, ativ_oc, nome_oc, inicio_oc, fim_oc = ocupacao
            chave = f"Ordem {ordem_oc} | Pedido {pedido_oc}"
            if chave not in ocupacoes_por_pedido:
                ocupacoes_por_pedido[chave] = []
            ocupacoes_por_pedido[chave].append({
                'funcionario_id': funcionario.id,
                'atividade': nome_oc,
                'inicio': inicio_oc,
                'fim': fim_oc
            })

    print("🗂️  Ocupações concorrentes identificadas:")
    for pedido, ocupacoes in ocupacoes_por_pedido.items():
        if "Pedido 6" not in pedido:  # Mostrar apenas outros pedidos
            print(f"\n📋 {pedido}:")
            ocupacoes.sort(key=lambda x: x['inicio'])
            for ocupacao in ocupacoes:
                print(f"   • Funcionário {ocupacao['funcionario_id']}: {ocupacao['atividade']}")
                print(f"     ⏰ {ocupacao['inicio'].strftime('%H:%M')} - {ocupacao['fim'].strftime('%H:%M')}")

    print(f"\n💡 ESTRATÉGIA DE REAGENDAMENTO:")
    print("   1. Reorganizar sequência de pedidos por prioridade")
    print("   2. Identificar janelas livres para atividades críticas")
    print("   3. Considerar contratação de funcionários especializados")
    print("   4. Implementar paralelização de atividades quando possível")

def main():
    """Função principal do analisador."""
    print("🚀 Iniciando análise de conflitos de funcionários...")

    try:
        analisar_conflitos_ordem_1_pedido_6()
        print("\n✅ Análise concluída com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())