#!/usr/bin/env python3
"""
Script para demonstrar o funcionamento do sistema de logs de subprodutos agrupados.
"""
import os
from utils.logs.log_subprodutos_agrupados import (
    registrar_log_subproduto_agrupado,
    obter_logs_subprodutos_agrupados,
    gerar_relatorio_consolidacao,
    ler_detalhes_log_agrupado
)
from datetime import datetime

def main():
    print("=" * 80)
    print("DEMONSTRAÇÃO - SISTEMA DE LOGS DE SUBPRODUTOS AGRUPADOS")
    print("=" * 80)
    print()

    # 1. Limpar logs anteriores
    print("🧹 Limpando logs de equipamentos anteriores...")
    from utils.logs.gerenciador_logs import limpar_logs_equipamentos
    limpar_logs_equipamentos()
    print()

    # 2. Simular execução de atividade consolidada
    print("🔧 Simulando execução de atividade consolidada...")

    # Dados da consolidação (simulando AgrupadorSubprodutos)
    ordens_e_pedidos = [
        {'id_ordem': 1, 'id_pedido': 1},
        {'id_ordem': 1, 'id_pedido': 2}
    ]

    # Simular alocação de equipamentos (formato da AtividadeModular)
    equipamentos_alocados = [
        (True, MockEquipamento("Hot Mix 1"), datetime(2025, 6, 26, 5, 30), datetime(2025, 6, 26, 5, 42))
    ]

    # Registrar log de subproduto agrupado
    registrar_log_subproduto_agrupado(
        ordens_e_pedidos=ordens_e_pedidos,
        id_atividade=20031,
        nome_item="massa_para_frituras",
        nome_atividade="mistura_de_massas_para_frituras",
        equipamentos_alocados=equipamentos_alocados,
        quantidade_total=1500.08,
        detalhes_consolidacao={
            'economia_equipamentos': 1,
            'tipo_consolidacao': 'SUBPRODUTO_AGRUPADO',
            'motivo': 'Consolidação de 2 atividades entre pedidos'
        }
    )
    print("✅ Log de subproduto agrupado criado com sucesso!")
    print()

    # 3. Mostrar logs criados
    print("📂 Verificando logs criados...")
    logs_agrupados = obter_logs_subprodutos_agrupados()

    if logs_agrupados:
        print(f"✅ Encontrado(s) {len(logs_agrupados)} log(s) de subprodutos agrupados:")
        for log_path in logs_agrupados:
            nome_arquivo = os.path.basename(log_path)
            print(f"   📄 {nome_arquivo}")
        print()

        # 4. Mostrar conteúdo do log
        print("📋 Conteúdo do log criado:")
        print("-" * 50)

        with open(logs_agrupados[0], 'r', encoding='utf-8') as f:
            conteudo = f.read()
        print(conteudo)
        print("-" * 50)
        print()

        # 5. Mostrar detalhes estruturados
        print("📊 Detalhes estruturados do log:")
        detalhes = ler_detalhes_log_agrupado(logs_agrupados[0])
        if detalhes:
            print(f"   🔗 Pedidos consolidados: {len(detalhes['pedidos_consolidados'])}")
            print(f"   ⚖️ Quantidade total: {detalhes['quantidade_total']}g")
            print(f"   🔧 Equipamentos utilizados: {', '.join(detalhes['equipamentos_utilizados'])}")
            print(f"   📅 Data de execução: {detalhes['data_execucao']}")
            print(f"   🎯 Atividades registradas: {len(detalhes['atividades'])}")
        print()

        # 6. Gerar relatório
        print("📈 Relatório de consolidações:")
        relatorio = gerar_relatorio_consolidacao()
        print(relatorio)

    else:
        print("❌ Nenhum log de subproduto agrupado encontrado!")

    print()
    print("=" * 80)
    print("✅ DEMONSTRAÇÃO CONCLUÍDA!")
    print("=" * 80)

class MockEquipamento:
    """Classe simulada para representar um equipamento"""
    def __init__(self, nome):
        self.nome = nome

if __name__ == "__main__":
    main()