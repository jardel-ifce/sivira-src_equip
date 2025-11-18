"""
Teste Simplificado do Otimizador v2.0
======================================

Usa as novas interfaces para teste rápido e fácil.
"""

import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

from otimizador_v2 import ExecutorV2


def teste_2_pedidos():
    """Teste rápido com 2 pedidos"""
    print(f"\n{'#'*80}")
    print(f"# TESTE 1: 2 PEDIDOS")
    print(f"{'#'*80}\n")

    executor = ExecutorV2()

    # Inicializar
    if not executor.inicializar():
        print(f"❌ Falha na inicialização")
        return None

    # Otimizar (limita aos 2 primeiros pedidos)
    solucao = executor.otimizar_csv(
        csv_path='data/csv/exemplo_pedidos.csv',
        timeout_segundos=180,
        limitar_pedidos=2
    )

    if not solucao:
        print(f"❌ Falha na otimização")
        return None

    # Carregar pedidos para mostrar resumo
    pedidos = executor.adaptador.carregar_pedidos_do_csv('data/csv/exemplo_pedidos.csv')
    pedidos_teste = pedidos[:2]

    # Mostrar resumo
    executor.imprimir_resumo_solucao(solucao, pedidos_teste)

    # Resultado
    if solucao.pedidos_atendidos == 2:
        print(f"✅ TESTE 1 PASSOU (2/2 pedidos atendidos)")
        return True
    else:
        print(f"⚠️ TESTE 1 PARCIAL ({solucao.pedidos_atendidos}/2 pedidos)")
        return False


def teste_13_pedidos():
    """Teste completo com 13 pedidos"""
    print(f"\n{'#'*80}")
    print(f"# TESTE 2: 13 PEDIDOS COMPLETOS")
    print(f"{'#'*80}\n")

    executor = ExecutorV2()

    # Inicializar
    if not executor.inicializar():
        print(f"❌ Falha na inicialização")
        return None

    # Otimizar (todos os pedidos)
    solucao = executor.otimizar_csv(
        csv_path='data/csv/exemplo_pedidos.csv',
        timeout_segundos=600
    )

    if not solucao:
        print(f"❌ Falha na otimização")
        return None

    # Carregar pedidos para comparação
    pedidos = executor.adaptador.carregar_pedidos_do_csv('data/csv/exemplo_pedidos.csv')

    # Mostrar resumo
    executor.imprimir_resumo_solucao(solucao, pedidos)

    # Comparar com baseline
    executor.comparar_com_baseline(solucao, len(pedidos))

    return solucao


def main():
    """Executa testes"""
    print(f"\n{'#'*80}")
    print(f"# TESTE DO OTIMIZADOR v2.0 - INTERFACE SIMPLIFICADA")
    print(f"{'#'*80}\n")

    # Teste 1: 2 pedidos
    teste1_ok = teste_2_pedidos()

    # Teste 2: 13 pedidos
    solucao_13 = teste_13_pedidos()

    # Resumo final
    print(f"\n{'#'*80}")
    print(f"# RESUMO FINAL")
    print(f"{'#'*80}\n")

    if teste1_ok:
        print(f"✅ Teste 1 (2 pedidos): PASSOU")
    else:
        print(f"⚠️ Teste 1 (2 pedidos): PARCIAL ou FALHOU")

    if solucao_13:
        taxa_v2 = (solucao_13.pedidos_atendidos / 13) * 100
        print(f"\n📊 Teste 2 (13 pedidos):")
        print(f"   Pedidos: {solucao_13.pedidos_atendidos}/13 ({taxa_v2:.1f}%)")
        print(f"   Tempo: {solucao_13.tempo_resolucao:.2f}s")

        # Análise final
        print(f"\n🎯 Análise Final:")
        if solucao_13.pedidos_atendidos >= 11:
            print(f"   ✅ EXCELENTE: Otimizador v2 igualou/superou método sequencial!")
        elif solucao_13.pedidos_atendidos > 4:
            print(f"   ✅ BOM: Otimizador v2 superou PL v1")
            print(f"   Melhoria: +{solucao_13.pedidos_atendidos - 4} pedidos vs PL v1")
        else:
            print(f"   ⚠️ Resultados abaixo do esperado")
    else:
        print(f"❌ Teste 2 (13 pedidos): FALHOU")

    print(f"\n{'#'*80}\n")


if __name__ == '__main__':
    main()
