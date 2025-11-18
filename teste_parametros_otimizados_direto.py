"""
Teste Direto dos Parâmetros Otimizados
=======================================

Testa os parâmetros otimizados usando estrutura do menu
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from menu.gerenciador_pedidos import GerenciadorPedidos
from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente
from otimizador_v2.executor_v2 import ExecutorV2
from services.gestores.producao.conversor_pedidos import ConversorPedidos

def main():
    print("=" * 80)
    print("🧪 TESTE PARÂMETROS OTIMIZADOS - Execução Direta")
    print("=" * 80)
    print()
    print("📋 Configuração OTIMIZADA:")
    print("   - Janelas por pedido: 15 (antes 8)")
    print("   - Pontos estratégicos: 9 (antes 5)")
    print("   - Resolução temporal: 30min (antes 60min)")
    print()
    print("=" * 80)
    print()

    # 1. Criar gerenciador de pedidos
    print("📥 [1/5] Carregando pedidos da ordem 1...")
    gerenciador = GerenciadorPedidos()

    # Carregar pedidos da ordem 1
    pedidos_ordem = gerenciador.obter_pedidos_por_ordem(1)

    if not pedidos_ordem:
        print("❌ Nenhum pedido carregado para ordem 1")
        return

    print(f"✅ {len(pedidos_ordem)} pedidos carregados")

    # 2. Criar executor v2
    print(f"\n📥 [2/5] Criando ExecutorV2...")
    executor = ExecutorV2()

    if not executor.inicializar():
        print("❌ Falha ao inicializar executor")
        return

    print("✅ Executor inicializado")

    # 3. Converter pedidos
    print(f"\n🔄 [3/5] Convertendo pedidos...")
    conversor = ConversorPedidos(
        gestor_almoxarifado=executor.configurador.gestor_almoxarifado
    )

    pedidos_convertidos = conversor.converter_pedidos(pedidos_ordem)

    if not pedidos_convertidos:
        print("❌ Erro ao converter pedidos")
        return

    print(f"✅ {len(pedidos_convertidos)} pedidos convertidos")

    # 4. Executar otimização com parâmetros OTIMIZADOS
    print(f"\n🚀 [4/5] Executando otimização...")
    print("   (Usando resolução 30min, 15 janelas/pedido, 9 pontos)")
    print()

    solucao = executor.otimizar_pedidos(
        pedidos=pedidos_convertidos,
        timeout_segundos=600
        # resolucao_minutos usa default 30min (otimizado)
    )

    if not solucao:
        print("\n❌ Otimização falhou")
        return

    # 5. Mostrar resultados e comparação
    print("\n" + "=" * 80)
    print("📊 [5/5] COMPARAÇÃO DE RESULTADOS")
    print("=" * 80)
    print()
    print(f"{'Método':<25} {'Pedidos':<15} {'Taxa':<12} {'Tempo':<15} {'Makespan':<15}")
    print("-" * 80)
    print(f"{'Sequencial':<25} {'11/13':<15} {'84.6%':<12} {'0.42s':<15} {'29h':<15}")
    print(f"{'PL v2.0 (ANTIGO)':<25} {'5/13':<15} {'38.5%':<12} {'0.04s':<15} {'72h':<15}")
    print(f"{'PL v2.0 (OTIMIZADO)':<25} {f'{solucao.pedidos_atendidos}/13':<15} {f'{(solucao.pedidos_atendidos/13*100):.1f}%':<12} {f'{solucao.tempo_resolucao:.2f}s':<15} {f'{solucao.makespan_minutos/60:.1f}h':<15}")
    print("-" * 80)
    print()

    # Calcular melhoria
    taxa_anterior = 5/13 * 100  # 38.5%
    taxa_nova = solucao.pedidos_atendidos/13 * 100
    melhoria_pedidos = solucao.pedidos_atendidos - 5
    melhoria_percentual = taxa_nova - taxa_anterior

    print("📈 MELHORIA vs PL v2.0 ANTIGO:")
    print(f"   Pedidos adicionais: {melhoria_pedidos:+d}")
    print(f"   Melhoria percentual: {melhoria_percentual:+.1f} p.p.")
    print()

    if solucao.pedidos_atendidos >= 11:
        print("🎉 SUCESSO! Atingiu ou superou o método sequencial!")
        print(f"   Gap até sequencial: {11 - solucao.pedidos_atendidos} pedidos")
    elif solucao.pedidos_atendidos > 5:
        print("✅ MELHORIA! Mais pedidos atendidos que versão anterior")
        print(f"   Gap até sequencial: {11 - solucao.pedidos_atendidos} pedidos")
    else:
        print("⚠️ Sem melhoria significativa nos pedidos atendidos")
        print("   Pode ser necessário ajustar outros parâmetros")

    print()

    # Mostrar estatísticas do modelo
    if 'total_variaveis' in solucao.estatisticas:
        print("📊 ESTATÍSTICAS DO MODELO PL:")
        print(f"   Variáveis: {solucao.estatisticas['total_variaveis']:,}")
        print(f"   Restrições: {solucao.estatisticas['total_restricoes']:,}")
        print(f"   Status solver: {solucao.status_solver}")
        print()

    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
