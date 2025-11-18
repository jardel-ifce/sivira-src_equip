"""
Teste Simples do Otimizador v2.0
==================================

Teste mínimo usando abordagem existente de carregamento de pedidos.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime
import pandas as pd

# Usar mesma abordagem do menu
from menu.gerenciador_pedidos import GerenciadorPedidos
from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente

# Import do otimizador v2
from otimizador_v2.otimizador_integrado_v2 import criar_otimizador_v2


def testar_v2_com_2_pedidos():
    """Teste com 2 pedidos usando gerenciador de pedidos"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTE OTIMIZADOR v2.0 - 2 PEDIDOS")
    print(f"{'='*80}\n")

    # Configurar ambiente
    configurador = ConfiguradorAmbiente()
    if not configurador.inicializar_ambiente():
        print(f"❌ Erro ao inicializar ambiente")
        return None

    # Carregar 2 pedidos do CSV
    print(f"\n📥 Carregando 2 pedidos do CSV...")
    gerenciador = GerenciadorPedidos(configurador)

    # Carregar apenas 2 linhas do CSV
    df = pd.read_csv('data/csv/exemplo_pedidos.csv')
    df_2_pedidos = df.head(2)  # Pega os 2 primeiros

    # Salvar em arquivo temporário
    csv_temp = 'data/csv/teste_2_pedidos_temp.csv'
    df_2_pedidos.to_csv(csv_temp, index=False)

    # Usar gerenciador para carregar
    pedidos = gerenciador.carregar_pedidos_csv(csv_temp)

    if not pedidos:
        print(f"❌ Nenhum pedido carregado")
        return None

    print(f"✅ {len(pedidos)} pedidos carregados")

    # Criar otimizador v2
    otimizador = criar_otimizador_v2(configurador)

    # Executar otimização
    solucao = otimizador.otimizar(
        pedidos=pedidos,
        timeout_segundos=180,
        resolucao_minutos=60
    )

    # Mostrar resultados
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO")
    print(f"{'='*80}")
    print(f"Status: {solucao.status_solver}")
    print(f"Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
    print(f"Taxa: {(solucao.pedidos_atendidos/len(pedidos)*100):.1f}%")
    print(f"Tempo: {solucao.tempo_resolucao:.2f}s")
    print(f"Makespan: {solucao.makespan_minutos:.0f} min")
    print(f"{'='*80}\n")

    return solucao


def testar_v2_com_13_pedidos():
    """Teste com todos os 13 pedidos"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTE OTIMIZADOR v2.0 - 13 PEDIDOS")
    print(f"{'='*80}\n")

    # Configurar ambiente
    configurador = ConfiguradorAmbiente()
    if not configurador.inicializar_ambiente():
        print(f"❌ Erro ao inicializar ambiente")
        return None

    # Carregar todos os pedidos
    print(f"\n📥 Carregando 13 pedidos do CSV...")
    gerenciador = GerenciadorPedidos(configurador)
    pedidos = gerenciador.carregar_pedidos_csv('data/csv/exemplo_pedidos.csv')

    if not pedidos:
        print(f"❌ Nenhum pedido carregado")
        return None

    print(f"✅ {len(pedidos)} pedidos carregados")

    # Criar otimizador v2
    otimizador = criar_otimizador_v2(configurador)

    # Executar otimização
    solucao = otimizador.otimizar(
        pedidos=pedidos,
        timeout_segundos=600,
        resolucao_minutos=60
    )

    # Mostrar resultados
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO FINAL - 13 PEDIDOS")
    print(f"{'='*80}")
    print(f"Status: {solucao.status_solver}")
    print(f"Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
    print(f"Taxa: {(solucao.pedidos_atendidos/len(pedidos)*100):.1f}%")
    print(f"Tempo: {solucao.tempo_resolucao:.2f}s")
    print(f"Makespan: {solucao.makespan_minutos:.0f} min ({solucao.makespan_minutos/60:.1f}h)")

    # Comparação
    print(f"\n📊 COMPARAÇÃO:")
    print(f"{'-'*80}")
    print(f"{'Método':<25} {'Taxa Sucesso':<15} {'Pedidos':<15}")
    print(f"{'-'*80}")
    print(f"{'Sequencial (v1)':<25} {'84.6%':<15} {'11/13':<15}")
    print(f"{'PL Original (v1)':<25} {'30.8%':<15} {'4/13':<15}")
    print(f"{'PL Completo (v2)':<25} {f'{solucao.pedidos_atendidos/len(pedidos)*100:.1f}%':<15} {f'{solucao.pedidos_atendidos}/{len(pedidos)}':<15}")
    print(f"{'-'*80}")

    if solucao.pedidos_atendidos > 0:
        print(f"\n✅ Pedidos executados:")
        for pedido_id in sorted(solucao.pedidos_selecionados.keys()):
            janela = solucao.janelas_selecionadas[pedido_id]
            print(f"   • Pedido {pedido_id}: {janela.datetime_inicio.strftime('%d/%m %H:%M')} → {janela.datetime_fim.strftime('%d/%m %H:%M')}")

    print(f"\n{'='*80}\n")

    return solucao


if __name__ == '__main__':
    print(f"\n{'#'*80}")
    print(f"# TESTE OTIMIZADOR v2.0 - MODELO PL COMPLETO")
    print(f"{'#'*80}\n")

    # Teste 1: 2 pedidos
    print(f"TESTE 1: Executando com 2 pedidos...")
    solucao_2 = testar_v2_com_2_pedidos()

    if solucao_2 and solucao_2.pedidos_atendidos == 2:
        print(f"✅ TESTE 1 PASSOU")
    else:
        print(f"⚠️ TESTE 1 FALHOU ou parcialmente")

    # Teste 2: 13 pedidos
    print(f"\n\nTESTE 2: Executando com 13 pedidos...")
    solucao_13 = testar_v2_com_13_pedidos()

    # Resumo final
    print(f"\n{'#'*80}")
    print(f"# RESUMO FINAL")
    print(f"{'#'*80}\n")

    if solucao_13:
        taxa_v2 = solucao_13.pedidos_atendidos / 13 * 100

        print(f"Otimizador v2.0 (PL COMPLETO): {taxa_v2:.1f}% ({solucao_13.pedidos_atendidos}/13)")

        if solucao_13.pedidos_atendidos >= 11:
            print(f"✅ SUCESSO: v2 alcançou ou superou o método sequencial!")
        elif solucao_13.pedidos_atendidos > 4:
            print(f"✅ MELHORIA: v2 superou o PL original")
        else:
            print(f"⚠️ v2 ainda não superou o PL original")

    print(f"\n{'#'*80}\n")
