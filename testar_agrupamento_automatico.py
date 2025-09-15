#!/usr/bin/env python3
"""
Teste do Sistema de Agrupamento Automático
==========================================

Testa o novo sistema que detecta automaticamente oportunidades de agrupamento
durante a alocação de equipamentos, resolvendo o problema de capacidade mínima.
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.atividades.pedido_de_producao import PedidoDeProducao
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from parser.parser_almoxarifado import carregar_itens_almoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from enums.producao.tipo_item import TipoItem
from utils.logs.gerenciador_logs import limpar_todos_os_logs
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from utils.agrupamento.cache_atividades_intervalo import cache_atividades_intervalo

def limpar_ambiente():
    """Limpa logs e comandas anteriores"""
    print("🧹 Limpando ambiente de teste...")
    limpar_todos_os_logs()
    apagar_todas_as_comandas()
    cache_atividades_intervalo.limpar_cache()
    print("✅ Ambiente limpo!")

def criar_cenario_teste():
    """
    Cria cenário de teste onde dois pedidos pequenos individualmente
    falhariam por capacidade mínima, mas juntos devem ser agrupados automaticamente.
    """
    print("\n" + "="*80)
    print("🧪 TESTE: AGRUPAMENTO AUTOMÁTICO POR CAPACIDADE MÍNIMA")
    print("="*80)

    # Configurar almoxarifado
    itens_almoxarifado = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
    gestor_almoxarifado = GestorAlmoxarifado(itens_almoxarifado)

    # Obter funcionários disponíveis
    funcionarios = funcionarios_disponiveis

    # Configurar janela temporal idêntica para forçar agrupamento
    inicio_jornada = datetime(2025, 6, 26, 8, 0)
    fim_jornada = datetime(2025, 6, 26, 8, 0)  # Mesmo horário para forçar backward scheduling

    print(f"\n📅 Cenário de Teste:")
    print(f"   Horário alvo: {fim_jornada.strftime('%d/%m/%Y %H:%M')}")
    print(f"   Estratégia: Backward scheduling - ambos pedidos terão mesmo intervalo")

    # Criar dois pedidos pequenos que individualmente falhariam por capacidade mínima
    pedidos = []

    print(f"\n🥟 Criando Pedidos de Teste:")

    # Pedido 1: 5 coxinhas (quantidade pequena)
    print(f"   📦 Pedido 1: 5 Coxinhas de Frango")
    pedido1 = PedidoDeProducao(
        id_ordem=1,
        id_pedido=1,
        id_produto=1055,  # ID da coxinha de frango
        tipo_item=TipoItem.PRODUTO,
        quantidade=5,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada,
        todos_funcionarios=funcionarios,
        gestor_almoxarifado=gestor_almoxarifado
    )
    pedido1.montar_estrutura()
    pedido1.criar_atividades_modulares_necessarias()
    pedidos.append(pedido1)

    # Pedido 2: 7 coxinhas (quantidade pequena)
    print(f"   📦 Pedido 2: 7 Coxinhas de Frango")
    pedido2 = PedidoDeProducao(
        id_ordem=1,
        id_pedido=2,
        id_produto=1055,  # ID da coxinha de frango
        tipo_item=TipoItem.PRODUTO,
        quantidade=7,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada,
        todos_funcionarios=funcionarios,
        gestor_almoxarifado=gestor_almoxarifado
    )
    pedido2.montar_estrutura()
    pedido2.criar_atividades_modulares_necessarias()
    pedidos.append(pedido2)

    return pedidos

def executar_teste_agrupamento(pedidos):
    """
    Executa os pedidos e verifica se o agrupamento automático funcionou.
    """
    print(f"\n🚀 Executando Teste de Agrupamento Automático:")
    print(f"   Total de pedidos: {len(pedidos)}")

    # Estatísticas antes da execução
    stats_antes = cache_atividades_intervalo.obter_estatisticas()
    print(f"\n📊 Estatísticas do Cache (ANTES):")
    print(f"   Grupos ativos: {stats_antes['grupos_ativos']}")
    print(f"   Atividades pendentes: {stats_antes['atividades_pendentes_total']}")

    sucessos = 0
    falhas = 0

    for i, pedido in enumerate(pedidos, 1):
        print(f"\n{'='*50}")
        print(f"🔄 Executando Pedido {i}/{len(pedidos)} (ID: {pedido.id_pedido})")
        print(f"{'='*50}")

        try:
            pedido.executar_atividades_em_ordem()
            sucessos += 1
            print(f"✅ Pedido {pedido.id_pedido} executado com sucesso!")

        except Exception as e:
            falhas += 1
            print(f"❌ Pedido {pedido.id_pedido} falhou: {e}")

    # Estatísticas após a execução
    stats_depois = cache_atividades_intervalo.obter_estatisticas()
    print(f"\n📊 Estatísticas do Cache (DEPOIS):")
    print(f"   Total atividades processadas: {stats_depois['total_atividades_adicionadas']}")
    print(f"   Total grupos criados: {stats_depois['total_grupos_criados']}")
    print(f"   Consolidações realizadas: {stats_depois['total_consolidacoes_realizadas']}")
    print(f"   Economia de equipamentos: {stats_depois['economia_capacidade_total']}")

    return sucessos, falhas, stats_depois

def verificar_resultados():
    """
    Verifica se os logs de agrupamento foram gerados corretamente.
    """
    print(f"\n🔍 Verificando Resultados:")

    # Verificar logs de equipamentos normais
    import glob
    logs_normais = glob.glob("logs/equipamentos/ordem*.log")
    logs_agrupados = glob.glob("logs/equipamentos/agrupado*.log")

    print(f"   📄 Logs normais gerados: {len(logs_normais)}")
    for log in logs_normais:
        print(f"      - {os.path.basename(log)}")

    print(f"   🔗 Logs agrupados gerados: {len(logs_agrupados)}")
    for log in logs_agrupados:
        print(f"      - {os.path.basename(log)}")

        # Mostrar conteúdo do log agrupado
        if os.path.exists(log):
            print(f"\n📋 Conteúdo do log agrupado:")
            with open(log, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            print("   " + "\n   ".join(conteudo.split('\n')[:20]))  # Primeiras 20 linhas

    return len(logs_agrupados) > 0

def main():
    """Execução principal do teste"""
    print("🧪 INICIANDO TESTE DO SISTEMA DE AGRUPAMENTO AUTOMÁTICO")
    print("="*80)

    try:
        # 1. Limpar ambiente
        limpar_ambiente()

        # 2. Criar cenário de teste
        pedidos = criar_cenario_teste()

        # 3. Executar teste
        sucessos, falhas, stats = executar_teste_agrupamento(pedidos)

        # 4. Verificar resultados
        logs_agrupados_criados = verificar_resultados()

        # 5. Resumo final
        print(f"\n" + "="*80)
        print(f"📋 RESUMO DO TESTE:")
        print(f"="*80)
        print(f"✅ Pedidos executados com sucesso: {sucessos}")
        print(f"❌ Pedidos que falharam: {falhas}")
        print(f"🔗 Consolidações automáticas: {stats['total_consolidacoes_realizadas']}")
        print(f"💾 Logs agrupados criados: {'SIM' if logs_agrupados_criados else 'NÃO'}")

        if stats['total_consolidacoes_realizadas'] > 0 and logs_agrupados_criados:
            print(f"\n🎉 TESTE BEM-SUCEDIDO!")
            print(f"   O sistema detectou automaticamente oportunidades de agrupamento")
            print(f"   e resolveu o problema de capacidade mínima sem intervenção manual!")
        else:
            print(f"\n⚠️ TESTE PARCIALMENTE BEM-SUCEDIDO")
            print(f"   Verifique os logs para identificar possíveis melhorias")

    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()