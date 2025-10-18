#!/usr/bin/env python3
"""
Script de teste para o ExportadorBanco.
Testa a preparação e exportação de pedidos aprovados.
"""

from services.exportacao.exportador_banco import ExportadorBanco
from services.validacao.validador_pedidos import ValidadorPedidos

def testar_exportador():
    print("=" * 80)
    print("🧪 TESTE: ExportadorBanco")
    print("=" * 80)
    print()

    validador = ValidadorPedidos()
    exportador = ExportadorBanco()

    # 1. Listar pedidos aprovados
    print("📋 STEP 1: Listando pedidos aprovados")
    print("-" * 80)
    aprovados = validador.listar_pedidos_aprovados()
    print(f"Total de pedidos aprovados: {len(aprovados)}")

    if not aprovados:
        print("⚠️ Nenhum pedido aprovado encontrado!")
        print("💡 Execute primeiro a alocação e validação de pedidos")
        return

    for pedido in aprovados:
        exportado = "✓ Exportado" if pedido.get('exportado', False) else "○ Pendente"
        print(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']} - {exportado}")
    print()

    # 2. Listar pedidos pendentes de exportação
    print("📋 STEP 2: Listando pedidos pendentes de exportação")
    print("-" * 80)
    pendentes = exportador.listar_pedidos_pendentes_exportacao()
    print(f"Total de pedidos pendentes: {len(pendentes)}")

    if not pendentes:
        print("✅ Nenhum pedido pendente - todos já foram exportados!")
        print()
    else:
        for pedido in pendentes:
            print(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']}")
        print()

        # 3. Preparar lote
        print("📋 STEP 3: Preparando lote de exportação")
        print("-" * 80)
        lote = exportador.preparar_lote_exportacao(pendentes)
        print(f"Lote ID: {lote['lote_id']}")
        print(f"Total de pedidos: {lote['total_pedidos']}")
        print(f"Status: {lote['status']}")
        print()

        # 4. Gerar script SQL
        print("📋 STEP 4: Gerando script SQL")
        print("-" * 80)
        script_sql = exportador.gerar_script_sql(pendentes)
        linhas = script_sql.split('\n')
        print(f"Script gerado com {len(linhas)} linhas")
        print("Primeiras 20 linhas:")
        print("-" * 60)
        for linha in linhas[:20]:
            print(linha)
        print("...")
        print()

        # 5. Exportar lote (sem executar SQL)
        print("📋 STEP 5: Exportando lote (apenas scripts, sem executar)")
        print("-" * 80)
        resultado = exportador.exportar_lote(pendentes, executar_sql=False)

        if resultado['sucesso']:
            print(f"✅ Exportação concluída com sucesso!")
            print(f"   Lote ID: {resultado['lote_id']}")
            print(f"   Total de pedidos: {resultado['total_pedidos']}")
            print(f"   Arquivo SQL: {resultado['arquivo_sql']}")
            print(f"   Relatório: {resultado['arquivo_relatorio']}")
            print(f"   SQL Executado: {resultado['executado']}")
        else:
            print(f"❌ Erro na exportação: {resultado.get('erro', 'Desconhecido')}")
        print()

    # 6. Gerar dashboard
    print("📋 STEP 6: Dashboard de exportação")
    print("-" * 80)
    dashboard = exportador.gerar_dashboard()
    print(dashboard)
    print()

    # 7. Histórico de exportações
    print("📋 STEP 7: Histórico de exportações")
    print("-" * 80)
    historico = exportador.listar_historico_exportacoes()
    if historico:
        print(f"Total de exportações: {len(historico)}")
        for lote in historico:
            print(f"   📦 Lote {lote['lote_id']}")
            print(f"      Data: {lote['data_preparacao']}")
            print(f"      Pedidos: {lote['total_pedidos']}")
            print()
    else:
        print("Nenhuma exportação realizada ainda")
    print()

    print("=" * 80)
    print("✅ Teste concluído!")
    print("=" * 80)


if __name__ == "__main__":
    testar_exportador()
