"""
Teste do Gerador de Janelas Temporais com Dados Reais
====================================================
"""

import sys
import os

# Ajusta path para seu projeto
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

from otimizador.teste_extrator_real import criar_pedidos_teste
from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos
from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais


def testar_gerador_dados_reais():
    """
    Testa o gerador de janelas temporais com os 4 pedidos reais da padaria
    """
    print("🚀 TESTANDO GERADOR DE JANELAS COM DADOS REAIS")
    print("="*60)
    
    try:
        # 1. Cria pedidos reais
        print("📋 Criando pedidos reais...")
        pedidos = criar_pedidos_teste()
        
        if not pedidos:
            print("❌ Falha ao criar pedidos")
            return
        
        # 2. Extrai dados
        print("\n📊 Extraindo dados...")
        extrator = ExtratorDadosPedidos()
        dados_extraidos = extrator.extrair_dados(pedidos)
        
        # 3. Gera janelas temporais
        print("\n⏰ Gerando janelas temporais...")
        gerador = GeradorJanelasTemporais(resolucao_minutos=1)
        janelas = gerador.gerar_janelas_todos_pedidos(dados_extraidos)
        
        # 4. Mostra resultados
        gerador.imprimir_resumo()
        
        # 5. Análise específica para PL
        print("\n🔧 PREPARAÇÃO PARA PROGRAMAÇÃO LINEAR:")
        print("-"*50)
        
        periodos_inicio, periodos_fim = gerador.obter_janelas_para_pl()
        
        total_combinacoes = 1
        for pedido_id in periodos_inicio:
            num_janelas = len(periodos_inicio[pedido_id])
            total_combinacoes *= num_janelas
            print(f"   Pedido {pedido_id}: {num_janelas:,} janelas temporais")
        
        print(f"\n📈 ESPAÇO DE BUSCA:")
        print(f"   Total de combinações teóricas: {total_combinacoes:,}")
        
        if total_combinacoes > 1e12:
            print("   ⚠️ Espaço muito grande - PL será essencial!")
        elif total_combinacoes > 1e6:
            print("   ✅ Espaço grande mas gerenciável para PL")
        else:
            print("   ✅ Espaço pequeno - PL será muito rápido")
        
        # 6. Exemplo de janelas para um pedido
        pedido_exemplo = list(periodos_inicio.keys())[0]
        janelas_exemplo = janelas[pedido_exemplo][:5]  # Primeiras 5 janelas
        
        print(f"\n📋 Exemplo - Primeiras 5 janelas do Pedido {pedido_exemplo}:")
        for i, janela in enumerate(janelas_exemplo):
            inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
            fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
            print(f"   {i+1}. {inicio_str} → {fim_str} (períodos {janela.periodo_inicio}-{janela.periodo_fim})")
        
        print(f"\n✅ GERADOR FUNCIONANDO CORRETAMENTE!")
        print(f"   Pronto para integração com modelo PL")
        
        return janelas
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    janelas = testar_gerador_dados_reais()