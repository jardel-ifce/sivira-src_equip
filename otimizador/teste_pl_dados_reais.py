"""
Teste do Modelo PL com Dados Reais da Padaria
============================================
"""

import sys
import os

# Ajusta path para seu projeto
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

from otimizador.teste_extrator_real import criar_pedidos_teste
from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos
from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais
from otimizador.modelo_pl_otimizador import ModeloPLOtimizador


def testar_pl_dados_reais():
    """
    Testa o modelo PL completo com os 4 pedidos reais da padaria
    """
    print("🚀 TESTANDO MODELO PL COM DADOS REAIS DA PADARIA")
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
        
        # 3. Gera janelas temporais (resolução MAIOR para reduzir espaço)
        print("\n⏰ Gerando janelas temporais...")
        print("⚠️ Usando resolução de 30 minutos para reduzir espaço de busca...")
        
        gerador = GeradorJanelasTemporais(resolucao_minutos=30)  # 30min em vez de 1min
        janelas = gerador.gerar_janelas_todos_pedidos(dados_extraidos)
        
        # 4. Mostra estatísticas das janelas
        gerador.imprimir_resumo()
        
        # Calcula espaço de busca reduzido
        total_combinacoes = 1
        for pedido_id, janelas_pedido in janelas.items():
            janelas_viaveis = sum(1 for j in janelas_pedido if j.viavel)
            total_combinacoes *= janelas_viaveis
        
        print(f"\n📈 ESPAÇO DE BUSCA COM RESOLUÇÃO 30min:")
        print(f"   Total de combinações: {total_combinacoes:,}")
        
        if total_combinacoes > 1e9:
            print("   ⚠️ Ainda muito grande. Testando com resolução 60min...")
            gerador = GeradorJanelasTemporais(resolucao_minutos=60)
            janelas = gerador.gerar_janelas_todos_pedidos(dados_extraidos)
            
            total_combinacoes = 1
            for pedido_id, janelas_pedido in janelas.items():
                janelas_viaveis = sum(1 for j in janelas_pedido if j.viavel)
                total_combinacoes *= janelas_viaveis
            
            print(f"   Combinações com 60min: {total_combinacoes:,}")
        
        # 5. Cria modelo PL
        print(f"\n🔧 Criando modelo PL...")
        modelo = ModeloPLOtimizador(dados_extraidos, janelas, gerador.configuracao_tempo)
        
        # 6. Mostra estatísticas do modelo
        modelo.imprimir_estatisticas_modelo()
        
        # 7. Resolve o modelo
        print(f"\n🚀 Resolvendo modelo PL...")
        print(f"⏱️ Isso pode levar alguns minutos com dados reais...")
        
        solucao = modelo.resolver(timeout_segundos=300)  # 5 minutos timeout
        
        # 8. Analisa resultado
        print(f"\n" + "="*60)
        print(f"🎉 RESULTADO FINAL")
        print("="*60)
        
        print(f"📊 Status: {solucao.status_solver}")
        print(f"📊 Pedidos atendidos: {solucao.pedidos_atendidos}/{len(dados_extraidos)}")
        print(f"📊 Taxa de atendimento: {solucao.estatisticas['taxa_atendimento']:.1%}")
        print(f"⏱️ Tempo de resolução: {solucao.tempo_resolucao:.2f}s")
        
        if solucao.pedidos_atendidos > 0:
            print(f"\n📅 CRONOGRAMA OTIMIZADO:")
            for pedido_id, janela in solucao.janelas_selecionadas.items():
                nome_produto = dados_extraidos[pedido_id-1].nome_produto  # Assume IDs sequenciais
                inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
                fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
                duracao = janela.datetime_fim - janela.datetime_inicio
                
                print(f"   🎯 Pedido {pedido_id} ({nome_produto}):")
                print(f"      ⏰ {inicio_str} → {fim_str} (duração: {duracao})")
        
        # 9. Comparação com sistema atual
        print(f"\n📊 COMPARAÇÃO COM SISTEMA ATUAL:")
        print(f"   Sistema atual: 4/4 pedidos (execução sequencial)")
        print(f"   Sistema otimizado: {solucao.pedidos_atendidos}/4 pedidos")
        
        if solucao.pedidos_atendidos == 4:
            print(f"   ✅ MESMA CAPACIDADE mas com execução otimizada!")
            print(f"   💡 Horários podem permitir pedidos adicionais futuros")
        elif solucao.pedidos_atendidos > 4:
            print(f"   🚀 MELHORIA: +{solucao.pedidos_atendidos - 4} pedidos adicionais!")
        else:
            print(f"   ⚠️ Menos pedidos que sistema atual. Verificar restrições.")
        
        print("="*60)
        
        return solucao
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return None


def testar_resolucoes_diferentes():
    """
    Testa diferentes resoluções temporais para encontrar o melhor equilíbrio
    """
    print("🔍 TESTANDO DIFERENTES RESOLUÇÕES TEMPORAIS")
    print("="*50)
    
    resolucoes = [60, 30, 15, 10, 5]  # minutos
    
    # Cria dados base
    pedidos = criar_pedidos_teste()
    extrator = ExtratorDadosPedidos()
    dados_extraidos = extrator.extrair_dados(pedidos)
    
    resultados = []
    
    for resolucao in resolucoes:
        print(f"\n🔧 Testando resolução: {resolucao} minutos...")
        
        try:
            # Gera janelas
            gerador = GeradorJanelasTemporais(resolucao_minutos=resolucao)
            janelas = gerador.gerar_janelas_todos_pedidos(dados_extraidos)
            
            # Calcula espaço
            total_combinacoes = 1
            total_janelas = 0
            for pedido_id, janelas_pedido in janelas.items():
                janelas_viaveis = sum(1 for j in janelas_pedido if j.viavel)
                total_combinacoes *= janelas_viaveis
                total_janelas += janelas_viaveis
            
            resultado = {
                'resolucao': resolucao,
                'total_janelas': total_janelas,
                'combinacoes': total_combinacoes,
                'viavel_pl': total_combinacoes < 1e8  # Limite prático para PL
            }
            
            print(f"   Janelas totais: {total_janelas:,}")
            print(f"   Combinações: {total_combinacoes:,}")
            print(f"   Viável para PL: {'✅' if resultado['viavel_pl'] else '❌'}")
            
            resultados.append(resultado)
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    # Recomendação
    print(f"\n💡 RECOMENDAÇÃO:")
    for resultado in resultados:
        if resultado['viavel_pl']:
            print(f"   Use resolução {resultado['resolucao']} minutos para melhor performance")
            break
    else:
        print(f"   Todas as resoluções geram espaços muito grandes")
        print(f"   Recomenda-se resolução 60 minutos para teste inicial")


if __name__ == "__main__":
    # Primeiro testa resoluções
    testar_resolucoes_diferentes()
    
    print("\n" + "="*80)
    
    # Depois testa PL completo
    solucao = testar_pl_dados_reais()