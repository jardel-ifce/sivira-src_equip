"""
Script de Teste do Otimizador v2.0 (Modelo PL Completo)
========================================================

Testa o novo otimizador com 2 pedidos simples primeiro,
depois com conjunto completo de 13 pedidos.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime, timedelta
import pandas as pd

# Imports de serviços
from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente
from services.gestores.producao.conversor_pedidos import ConversorPedidos

# Import do otimizador v2
from otimizador_v2.otimizador_integrado_v2 import criar_otimizador_v2


def testar_2_pedidos():
    """Teste com 2 pedidos simples (Pedido 4 e 6)"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTE 1: 2 PEDIDOS SIMPLES (Pedido 4 e 6)")
    print(f"{'='*80}\n")

    # Configurar ambiente
    print(f"📥 Configurando ambiente...")
    configurador = ConfiguradorAmbiente()
    if not configurador.inicializar_ambiente():
        print(f"❌ Erro ao inicializar ambiente")
        return False

    # Carregar apenas pedidos 4 e 6 do CSV
    df = pd.read_csv('data/csv/exemplo_pedidos.csv')
    df_filtrado = df[df['id'].isin([1004, 1055])]  # Pedidos 4 e 6

    print(f"\n📋 Pedidos selecionados para teste:")
    for _, row in df_filtrado.iterrows():
        print(f"   • Pedido {row['id']}: {row['quantidade']}x {row['tipo_produto']} (prazo: {row['fim_jornada']})")

    # Converter para objetos PedidoProducao
    conversor = ConversorPedidos(configurador)
    pedidos = []

    for _, row in df_filtrado.iterrows():
        try:
            pedido = conversor.criar_pedido_de_producao(
                id_pedido=int(row['id']),
                quantidade=int(row['quantidade']),
                prazo_entrega=datetime.strptime(row['fim_jornada'], '%Y-%m-%d %H:%M:%S')
            )
            pedidos.append(pedido)
        except Exception as e:
            print(f"❌ Erro ao criar pedido {row['id']}: {e}")

    if not pedidos:
        print(f"❌ Nenhum pedido válido criado")
        return False

    # Criar otimizador v2
    otimizador = criar_otimizador_v2(configurador)

    # Executar otimização
    solucao = otimizador.otimizar(
        pedidos=pedidos,
        timeout_segundos=300,  # 5 minutos
        resolucao_minutos=60
    )

    # Analisar resultado
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO DO TESTE")
    print(f"{'='*80}")
    print(f"Status: {solucao.status_solver}")
    print(f"Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
    print(f"Taxa de sucesso: {(solucao.pedidos_atendidos/len(pedidos)*100):.1f}%")
    print(f"Tempo de resolução: {solucao.tempo_resolucao:.2f}s")
    print(f"Makespan: {solucao.makespan_minutos:.0f} min ({solucao.makespan_minutos/60:.1f}h)")

    if solucao.pedidos_atendidos > 0:
        print(f"\n✅ Pedidos executados:")
        for pedido_id in solucao.pedidos_selecionados.keys():
            janela = solucao.janelas_selecionadas[pedido_id]
            print(f"   • Pedido {pedido_id}: {janela.datetime_inicio.strftime('%d/%m %H:%M')} → {janela.datetime_fim.strftime('%d/%m %H:%M')}")
    else:
        print(f"\n❌ Nenhum pedido executado")

    print(f"{'='*80}\n")

    sucesso = solucao.pedidos_atendidos == len(pedidos)
    return sucesso


def testar_13_pedidos():
    """Teste com conjunto completo de 13 pedidos"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTE 2: 13 PEDIDOS COMPLETOS")
    print(f"{'='*80}\n")

    # Configurar ambiente
    print(f"📥 Configurando ambiente...")
    configurador = ConfiguradorAmbiente()
    if not configurador.inicializar_ambiente():
        print(f"❌ Erro ao inicializar ambiente")
        return None

    # Carregar TODOS os pedidos do CSV
    df = pd.read_csv('data/csv/exemplo_pedidos.csv')

    print(f"\n📋 {len(df)} pedidos carregados do CSV")

    # Converter para objetos PedidoProducao
    conversor = ConversorPedidos(configurador)
    pedidos = []

    for _, row in df.iterrows():
        try:
            pedido = conversor.criar_pedido_de_producao(
                id_pedido=int(row['id']),
                quantidade=int(row['quantidade']),
                prazo_entrega=datetime.strptime(row['fim_jornada'], '%Y-%m-%d %H:%M:%S')
            )
            pedidos.append(pedido)
        except Exception as e:
            print(f"❌ Erro ao criar pedido {row['id']}: {e}")

    if not pedidos:
        print(f"❌ Nenhum pedido válido criado")
        return None

    print(f"✅ {len(pedidos)} pedidos criados com sucesso")

    # Criar otimizador v2
    otimizador = criar_otimizador_v2(configurador)

    # Executar otimização (com timeout maior)
    solucao = otimizador.otimizar(
        pedidos=pedidos,
        timeout_segundos=600,  # 10 minutos
        resolucao_minutos=60
    )

    # Analisar resultado
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO FINAL - 13 PEDIDOS")
    print(f"{'='*80}")
    print(f"Status: {solucao.status_solver}")
    print(f"Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
    print(f"Taxa de sucesso: {(solucao.pedidos_atendidos/len(pedidos)*100):.1f}%")
    print(f"Tempo de resolução: {solucao.tempo_resolucao:.2f}s")
    print(f"Makespan: {solucao.makespan_minutos:.0f} min ({solucao.makespan_minutos/60:.1f}h)")

    # Comparação com métodos anteriores
    print(f"\n📊 COMPARAÇÃO COM MÉTODOS ANTERIORES:")
    print(f"{'='*80}")
    print(f"{'Método':<25} {'Taxa Sucesso':<15} {'Pedidos':<15}")
    print(f"{'-'*80}")
    print(f"{'Sequencial (v1)':<25} {'84.6%':<15} {'11/13':<15}")
    print(f"{'PL Original (v1)':<25} {'30.8%':<15} {'4/13':<15}")
    print(f"{'PL Completo (v2)':<25} {f'{solucao.pedidos_atendidos/len(pedidos)*100:.1f}%':<15} {f'{solucao.pedidos_atendidos}/{len(pedidos)}':<15}")
    print(f"{'='*80}")

    # Mostrar quais pedidos foram executados
    if solucao.pedidos_atendidos > 0:
        print(f"\n✅ Pedidos executados:")
        pedidos_por_id = {p.id_pedido: p for p in pedidos}
        for pedido_id in sorted(solucao.pedidos_selecionados.keys()):
            janela = solucao.janelas_selecionadas[pedido_id]
            nome = pedidos_por_id[pedido_id].nome_produto
            print(f"   • Pedido {pedido_id} ({nome}): {janela.datetime_inicio.strftime('%d/%m %H:%M')} → {janela.datetime_fim.strftime('%d/%m %H:%M')}")
    else:
        print(f"\n❌ Nenhum pedido executado")

    # Mostrar pedidos que falharam
    pedidos_falharam = [p.id_pedido for p in pedidos if p.id_pedido not in solucao.pedidos_selecionados]
    if pedidos_falharam:
        print(f"\n❌ Pedidos NÃO executados:")
        for pedido_id in sorted(pedidos_falharam):
            nome = pedidos_por_id[pedido_id].nome_produto
            print(f"   • Pedido {pedido_id} ({nome})")

    print(f"\n{'='*80}\n")

    return solucao


if __name__ == '__main__':
    print(f"\n{'#'*80}")
    print(f"# TESTE DO OTIMIZADOR v2.0 - MODELO PL COMPLETO")
    print(f"# Com TODAS as restrições modeladas (tempo_maximo_espera, equipamentos, etc)")
    print(f"{'#'*80}\n")

    # TESTE 1: 2 pedidos simples
    sucesso_teste1 = testar_2_pedidos()

    if not sucesso_teste1:
        print(f"\n⚠️ TESTE 1 (2 pedidos) FALHOU")
        print(f"⚠️ Continuando para teste completo...\n")
    else:
        print(f"\n✅ TESTE 1 (2 pedidos) PASSOU\n")

    # TESTE 2: 13 pedidos completos
    solucao_final = testar_13_pedidos()

    # Resumo final
    print(f"\n{'#'*80}")
    print(f"# RESUMO FINAL")
    print(f"{'#'*80}")

    if solucao_final:
        taxa_v2 = solucao_final.pedidos_atendidos / 13 * 100
        print(f"\n📊 Otimizador v2.0 (PL COMPLETO):")
        print(f"   Taxa de sucesso: {taxa_v2:.1f}%")
        print(f"   Pedidos: {solucao_final.pedidos_atendidos}/13")
        print(f"   Tempo: {solucao_final.tempo_resolucao:.2f}s")

        print(f"\n📊 Comparação:")
        print(f"   • Sequencial v1: 84.6% (11/13)")
        print(f"   • PL Original v1: 30.8% (4/13)")
        print(f"   • PL Completo v2: {taxa_v2:.1f}% ({solucao_final.pedidos_atendidos}/13)")

        # Análise
        if solucao_final.pedidos_atendidos >= 11:
            print(f"\n✅ SUCESSO: v2 alcançou ou superou o método sequencial!")
        elif solucao_final.pedidos_atendidos > 4:
            print(f"\n✅ MELHORIA: v2 superou o PL original, mas ainda abaixo do sequencial")
        else:
            print(f"\n⚠️ ATENÇÃO: v2 ainda não superou o PL original")

    print(f"\n{'#'*80}\n")
