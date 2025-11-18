"""
Teste Final do Otimizador v2.0 - Modelo PL Completo
=====================================================

Teste completo com os 13 pedidos usando a abordagem correta de criação.
"""

import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

from datetime import datetime, timedelta
import pandas as pd

# Imports básicos
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestores.almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from enums.producao.tipo_item import TipoItem
from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente

# Otimizador v2
from otimizador_v2.otimizador_integrado_v2 import criar_otimizador_v2


def criar_pedidos_from_csv(csv_path: str, gestor_almoxarifado):
    """Cria pedidos a partir do CSV"""
    print(f"\n📥 Carregando pedidos de {csv_path}...")

    df = pd.read_csv(csv_path)
    print(f"✅ {len(df)} linhas carregadas do CSV")

    pedidos = []

    for idx, row in df.iterrows():
        try:
            # Dados do CSV
            id_produto = int(row['id'])
            quantidade = int(row['quantidade'])
            fim_jornada = datetime.strptime(row['fim_jornada'], '%Y-%m-%d %H:%M:%S')
            inicio_jornada = fim_jornada - timedelta(days=3)  # 3 dias antes

            # Criar pedido
            pedido = PedidoDeProducao(
                id_ordem=1,
                id_pedido=idx + 1,
                id_produto=id_produto,
                tipo_item=TipoItem.PRODUTO,
                quantidade=quantidade,
                inicio_jornada=inicio_jornada,
                fim_jornada=fim_jornada,
                gestor_almoxarifado=gestor_almoxarifado
            )

            # Montar estrutura (carrega atividades)
            pedido.montar_estrutura()
            pedido.criar_atividades_modulares_necessarias()

            pedidos.append(pedido)
            print(f"✅ Pedido {idx+1} ({id_produto}): {quantidade} uni, prazo {fim_jornada.strftime('%d/%m %H:%M')}")

        except Exception as e:
            print(f"❌ Erro ao criar pedido {idx+1}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n📊 Total de pedidos criados: {len(pedidos)}/{len(df)}")
    return pedidos


def testar_otimizador_v2(num_pedidos=None):
    """
    Testa otimizador v2 com pedidos do CSV

    Args:
        num_pedidos: Número de pedidos a testar (None = todos)
    """
    print(f"\n{'='*80}")
    if num_pedidos:
        print(f"🧪 TESTE OTIMIZADOR v2.0 - {num_pedidos} PEDIDOS")
    else:
        print(f"🧪 TESTE OTIMIZADOR v2.0 - TODOS OS PEDIDOS")
    print(f"{'='*80}\n")

    # 1. Configurar ambiente
    print(f"📥 Configurando ambiente...")
    configurador = ConfiguradorAmbiente()
    if not configurador.inicializar_ambiente():
        print(f"❌ Erro ao inicializar ambiente")
        return None

    # 2. Criar pedidos
    pedidos = criar_pedidos_from_csv(
        'data/csv/exemplo_pedidos.csv',
        configurador.gestor_almoxarifado
    )

    if not pedidos:
        print(f"❌ Nenhum pedido criado")
        return None

    # Limitar número se solicitado
    if num_pedidos and num_pedidos < len(pedidos):
        print(f"\n📊 Limitando a {num_pedidos} primeiros pedidos...")
        pedidos = pedidos[:num_pedidos]

    # 3. Criar otimizador v2
    print(f"\n🚀 Criando otimizador v2...")
    otimizador = criar_otimizador_v2(configurador)

    # 4. Executar otimização
    solucao = otimizador.otimizar(
        pedidos=pedidos,
        timeout_segundos=600,
        resolucao_minutos=60
    )

    # 5. Mostrar resultados
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO")
    print(f"{'='*80}")
    print(f"Status Solver: {solucao.status_solver}")
    print(f"Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
    print(f"Taxa de sucesso: {(solucao.pedidos_atendidos/len(pedidos)*100):.1f}%")
    print(f"Tempo de resolução: {solucao.tempo_resolucao:.2f}s")
    print(f"Makespan: {solucao.makespan_minutos:.0f} min ({solucao.makespan_minutos/60:.1f}h)")

    if 'total_variaveis' in solucao.estatisticas:
        print(f"\n📊 Estatísticas do Modelo:")
        print(f"   Variáveis: {solucao.estatisticas['total_variaveis']:,}")
        print(f"   Restrições: {solucao.estatisticas['total_restricoes']:,}")

    # Comparação com métodos anteriores
    if len(pedidos) == 13:
        print(f"\n📊 COMPARAÇÃO COM MÉTODOS ANTERIORES:")
        print(f"{'-'*80}")
        print(f"{'Método':<30} {'Taxa Sucesso':<15} {'Pedidos':<15} {'Tempo':<15}")
        print(f"{'-'*80}")
        print(f"{'Sequencial (v1)':<30} {'84.6%':<15} {'11/13':<15} {'0.42s':<15}")
        print(f"{'PL Original (v1)':<30} {'30.8%':<15} {'4/13':<15} {'0.51s':<15}")
        taxa_v2 = solucao.pedidos_atendidos/13*100
        print(f"{'PL Completo (v2) ✨':<30} {f'{taxa_v2:.1f}%':<15} {f'{solucao.pedidos_atendidos}/13':<15} {f'{solucao.tempo_resolucao:.2f}s':<15}")
        print(f"{'-'*80}")

    # Pedidos executados
    if solucao.pedidos_atendidos > 0:
        print(f"\n✅ Pedidos EXECUTADOS:")
        for pedido_id in sorted(solucao.pedidos_selecionados.keys()):
            janela = solucao.janelas_selecionadas[pedido_id]
            pedido_obj = next((p for p in pedidos if p.id_pedido == pedido_id), None)
            nome = pedido_obj.nome_produto if pedido_obj else f"Pedido {pedido_id}"
            print(f"   • {nome}: {janela.datetime_inicio.strftime('%d/%m %H:%M')} → {janela.datetime_fim.strftime('%d/%m %H:%M')}")

    # Pedidos NÃO executados
    pedidos_falharam = [p for p in pedidos if p.id_pedido not in solucao.pedidos_selecionados]
    if pedidos_falharam:
        print(f"\n❌ Pedidos NÃO executados ({len(pedidos_falharam)}):")
        for pedido in pedidos_falharam[:10]:  # Mostrar no máximo 10
            print(f"   • Pedido {pedido.id_pedido} ({pedido.nome_produto})")
        if len(pedidos_falharam) > 10:
            print(f"   ... e mais {len(pedidos_falharam)-10}")

    print(f"\n{'='*80}\n")

    return solucao


if __name__ == '__main__':
    print(f"\n{'#'*80}")
    print(f"# TESTE FINAL DO OTIMIZADOR v2.0")
    print(f"# Modelo PL COMPLETO com TODAS as restrições")
    print(f"{'#'*80}\n")

    # TESTE 1: 2 pedidos (rápido)
    print(f"\n📋 TESTE 1: Testando com 2 pedidos...")
    solucao_2 = testar_otimizador_v2(num_pedidos=2)

    if solucao_2:
        if solucao_2.pedidos_atendidos == 2:
            print(f"✅ TESTE 1 PASSOU (2/2 pedidos)")
        else:
            print(f"⚠️ TESTE 1 PARCIAL ({solucao_2.pedidos_atendidos}/2 pedidos)")
    else:
        print(f"❌ TESTE 1 FALHOU")

    # TESTE 2: Todos os 13 pedidos
    print(f"\n\n📋 TESTE 2: Testando com TODOS os 13 pedidos...")
    solucao_13 = testar_otimizador_v2(num_pedidos=None)

    # RESUMO FINAL
    print(f"\n{'#'*80}")
    print(f"# RESUMO FINAL")
    print(f"{'#'*80}\n")

    if solucao_13:
        taxa_v2 = solucao_13.pedidos_atendidos / 13 * 100

        print(f"📊 Otimizador v2.0 (PL COMPLETO):")
        print(f"   Pedidos: {solucao_13.pedidos_atendidos}/13 ({taxa_v2:.1f}%)")
        print(f"   Tempo: {solucao_13.tempo_resolucao:.2f}s")
        print(f"   Makespan: {solucao_13.makespan_minutos:.0f} min")

        print(f"\n📊 Comparação Final:")
        print(f"   • Sequencial v1: 84.6% (11/13) ← Baseline")
        print(f"   • PL Original v1: 30.8% (4/13) ← Com deficiências")
        print(f"   • PL Completo v2: {taxa_v2:.1f}% ({solucao_13.pedidos_atendidos}/13) ← CORRIGIDO")

        # Análise de melhoria
        print(f"\n🎯 Análise de Melhoria:")
        if solucao_13.pedidos_atendidos >= 11:
            print(f"   ✅ EXCELENTE: v2 alcançou/superou o método sequencial!")
            print(f"   ✅ Ganho vs PL v1: +{solucao_13.pedidos_atendidos - 4} pedidos ({taxa_v2 - 30.8:.1f}%)")
        elif solucao_13.pedidos_atendidos > 4:
            print(f"   ✅ BOM: v2 superou o PL original")
            print(f"   ✅ Ganho vs PL v1: +{solucao_13.pedidos_atendidos - 4} pedidos ({taxa_v2 - 30.8:.1f}%)")
            print(f"   ⚠️ Gap vs Sequencial: {11 - solucao_13.pedidos_atendidos} pedidos")
        else:
            print(f"   ⚠️ v2 não superou o PL original")
            print(f"   💡 Possíveis causas: timeout, infactibilidade, bugs")
    else:
        print(f"❌ Teste com 13 pedidos falhou")

    print(f"\n{'#'*80}\n")
