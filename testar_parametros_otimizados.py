"""
Teste dos Parâmetros Otimizados do PL v2.0
==========================================

Testa configuração otimizada:
- Janelas por pedido: 15 (antes 8)
- Pontos estratégicos: 9 (antes 5)
- Resolução temporal: 30min (antes 60min)

Objetivo: Maximizar pedidos atendidos
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from otimizador_v2.executor_v2 import ExecutorV2

def main():
    print("=" * 80)
    print("🧪 TESTE - PARÂMETROS OTIMIZADOS PL v2.0")
    print("=" * 80)
    print()
    print("📋 Configuração OTIMIZADA:")
    print("   - Janelas por pedido: 15 (antes 8)")
    print("   - Pontos estratégicos: 9 (antes 5)")
    print("   - Resolução temporal: 30min (antes 60min)")
    print()
    print("=" * 80)
    print()

    # Criar executor
    executor = ExecutorV2()

    # Inicializar
    if not executor.inicializar():
        print("❌ Falha ao inicializar executor")
        return

    # CSV de teste (mesmos 13 pedidos)
    csv_path = "data/comandas/pedidos_ordem_1.csv"

    print(f"\n📂 Arquivo: {csv_path}")
    print()

    # Executar otimização com parâmetros otimizados
    # (os valores padrão já foram atualizados no executor)
    print("🚀 Executando otimização com parâmetros OTIMIZADOS...")
    print()

    solucao = executor.otimizar_csv(
        csv_path=csv_path,
        timeout_segundos=600
        # resolucao_minutos usa default 30min (otimizado)
    )

    if solucao:
        print("\n" + "=" * 80)
        print("✅ OTIMIZAÇÃO CONCLUÍDA COM SUCESSO")
        print("=" * 80)

        # Comparar com baseline anterior
        print("\n📊 COMPARAÇÃO COM RESULTADOS ANTERIORES:")
        print("-" * 80)
        print(f"{'Método':<20} {'Pedidos':<15} {'Taxa':<10} {'Tempo':<15}")
        print("-" * 80)
        print(f"{'Sequencial':<20} {'11/13':<15} {'84.6%':<10} {'0.42s':<15}")
        print(f"{'PL v2.0 (ANTIGO)':<20} {'5/13':<15} {'38.5%':<10} {'0.04s':<15}")
        print(f"{'PL v2.0 (OTIMIZADO)':<20} {f'{solucao.pedidos_atendidos}/13':<15} {f'{(solucao.pedidos_atendidos/13*100):.1f}%':<10} {f'{solucao.tempo_resolucao:.2f}s':<15}")
        print("-" * 80)

        # Calcular melhoria
        melhoria_pedidos = solucao.pedidos_atendidos - 5
        melhoria_percentual = ((solucao.pedidos_atendidos/13) - (5/13)) * 100

        print(f"\n📈 MELHORIA:")
        print(f"   Pedidos adicionais: {melhoria_pedidos:+d}")
        print(f"   Melhoria percentual: {melhoria_percentual:+.1f} p.p.")

        if solucao.pedidos_atendidos >= 11:
            print(f"\n🎉 SUCESSO! Atingiu ou superou o método sequencial!")
        elif solucao.pedidos_atendidos > 5:
            print(f"\n✅ MELHORIA! Mais pedidos atendidos que a versão anterior")
        else:
            print(f"\n⚠️ Sem melhoria nos pedidos atendidos")

        print()

    else:
        print("\n❌ Otimização falhou")

if __name__ == "__main__":
    main()
