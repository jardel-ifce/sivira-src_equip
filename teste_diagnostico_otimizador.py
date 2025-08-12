"""
Teste de Diagnóstico do Otimizador PL
=====================================

Script para identificar e corrigir problemas no sistema de otimização.
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o caminho do sistema
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def teste_1_importacoes():
    """Testa se todas as importações estão funcionando"""
    print("🧪 TESTE 1: Verificando importações...")
    
    try:
        # Teste OR-Tools
        from ortools.linear_solver import pywraplp
        print("   ✅ OR-Tools importado com sucesso")
    except ImportError as e:
        print(f"   ❌ OR-Tools não disponível: {e}")
        print("   💡 Execute: pip install ortools")
        return False
    
    try:
        # Teste do extrator
        from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos, DadosPedido, DadosAtividade
        print("   ✅ Extrator importado com sucesso")
    except ImportError as e:
        print(f"   ❌ Extrator não disponível: {e}")
        return False
    
    try:
        # Teste do gerador
        from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais
        print("   ✅ Gerador de janelas importado com sucesso")
    except ImportError as e:
        print(f"   ❌ Gerador não disponível: {e}")
        return False
    
    try:
        # Teste do modelo PL
        from otimizador.modelo_pl_otimizador import ModeloPLOtimizador
        print("   ✅ Modelo PL importado com sucesso")
    except ImportError as e:
        print(f"   ❌ Modelo PL não disponível: {e}")
        return False
    
    try:
        # Teste do otimizador integrado
        from otimizador.otimizador_integrado import OtimizadorIntegrado
        print("   ✅ Otimizador integrado importado com sucesso")
    except ImportError as e:
        print(f"   ❌ Otimizador integrado não disponível: {e}")
        return False
    
    print("   🎉 Todas as importações funcionando!")
    return True


def teste_2_extrator_basico():
    """Testa o extrator com dados mock"""
    print("\n🧪 TESTE 2: Extrator com dados mock...")
    
    from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos, DadosPedido, DadosAtividade
    
    # Cria dados mock para teste
    class MockPedido:
        def __init__(self, id_pedido, id_produto, nome, quantidade):
            self.id_pedido = id_pedido
            self.id_produto = id_produto
            self.quantidade = quantidade
            self.inicio_jornada = datetime(2025, 6, 22, 7, 0)
            self.fim_jornada = datetime(2025, 6, 26, 7, 0)
            self.atividades_modulares = None  # Simula o problema real
            
            class MockFicha:
                def __init__(self, nome):
                    self.nome = nome
            
            self.ficha_tecnica_modular = MockFicha(nome)
    
    # Cria pedidos mock
    pedidos_mock = [
        MockPedido(1, 1001, "pao_frances", 450),
        MockPedido(2, 1002, "pao_hamburguer", 120)
    ]
    
    print(f"   🔧 Testando com {len(pedidos_mock)} pedidos mock...")
    
    # Testa extração
    extrator = ExtratorDadosPedidos()
    dados_extraidos = extrator.extrair_dados(pedidos_mock)
    
    # Verifica resultados
    if dados_extraidos and len(dados_extraidos) > 0:
        print(f"   ✅ Extração bem-sucedida: {len(dados_extraidos)} pedidos")
        
        for dados in dados_extraidos:
            print(f"      • Pedido {dados.id_pedido}: {dados.nome_produto}")
            print(f"        Duração: {dados.duracao_total}")
            print(f"        Atividades: {len(dados.atividades)}")
            
        if all(d.duracao_total > timedelta(0) for d in dados_extraidos):
            print("   ✅ Todas as durações são válidas!")
            return True
        else:
            print("   ⚠️ Algumas durações são zero - verificar estimativas")
            return False
    else:
        print("   ❌ Falha na extração")
        return False


def teste_3_gerador_janelas():
    """Testa o gerador de janelas temporais"""
    print("\n🧪 TESTE 3: Gerador de janelas temporais...")
    
    from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos
    from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais
    
    # Usa dados do teste anterior
    class MockPedido:
        def __init__(self, id_pedido, id_produto, nome, quantidade):
            self.id_pedido = id_pedido
            self.id_produto = id_produto
            self.quantidade = quantidade
            self.inicio_jornada = datetime(2025, 6, 22, 7, 0)
            self.fim_jornada = datetime(2025, 6, 26, 7, 0)
            self.atividades_modulares = None
            
            class MockFicha:
                def __init__(self, nome):
                    self.nome = nome
            
            self.ficha_tecnica_modular = MockFicha(nome)
    
    pedidos_mock = [
        MockPedido(1, 1001, "pao_frances", 450),
        MockPedido(2, 1002, "pao_hamburguer", 120)
    ]
    
    print("   🔧 Extraindo dados...")
    extrator = ExtratorDadosPedidos()
    dados_extraidos = extrator.extrair_dados(pedidos_mock)
    
    print("   🔧 Gerando janelas temporais...")
    gerador = GeradorJanelasTemporais(resolucao_minutos=60)  # 1h para teste rápido
    janelas = gerador.gerar_janelas_todos_pedidos(dados_extraidos)
    
    # Verifica resultados
    total_janelas = sum(len(j) for j in janelas.values())
    print(f"   📊 Total de janelas geradas: {total_janelas}")
    
    if total_janelas > 0:
        print("   ✅ Geração de janelas bem-sucedida!")
        
        for pedido_id, lista_janelas in janelas.items():
            if lista_janelas:
                print(f"      • Pedido {pedido_id}: {len(lista_janelas)} janelas")
                print(f"        Primeira: {lista_janelas[0].datetime_inicio.strftime('%d/%m %H:%M')} → {lista_janelas[0].datetime_fim.strftime('%d/%m %H:%M')}")
        
        return True
    else:
        print("   ❌ Nenhuma janela foi gerada")
        return False


def teste_4_modelo_pl():
    """Testa o modelo de programação linear"""
    print("\n🧪 TESTE 4: Modelo de Programação Linear...")
    
    try:
        from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos
        from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais
        from otimizador.modelo_pl_otimizador import ModeloPLOtimizador
        
        # Dados do teste anterior
        class MockPedido:
            def __init__(self, id_pedido, id_produto, nome, quantidade):
                self.id_pedido = id_pedido
                self.id_produto = id_produto
                self.quantidade = quantidade
                self.inicio_jornada = datetime(2025, 6, 22, 7, 0)
                self.fim_jornada = datetime(2025, 6, 26, 7, 0)
                self.atividades_modulares = None
                
                class MockFicha:
                    def __init__(self, nome):
                        self.nome = nome
                
                self.ficha_tecnica_modular = MockFicha(nome)
        
        pedidos_mock = [MockPedido(1, 1001, "pao_frances", 300)]  # Apenas 1 para teste
        
        print("   🔧 Preparando dados...")
        extrator = ExtratorDadosPedidos()
        dados_extraidos = extrator.extrair_dados(pedidos_mock)
        
        gerador = GeradorJanelasTemporais(resolucao_minutos=120)  # 2h para teste bem rápido
        janelas = gerador.gerar_janelas_todos_pedidos(dados_extraidos)
        
        total_janelas = sum(len(j) for j in janelas.values())
        print(f"   📊 Dados preparados: {len(dados_extraidos)} pedidos, {total_janelas} janelas")
        
        if total_janelas == 0:
            print("   ⚠️ Sem janelas para testar - criando janela manual...")
            return False
        
        print("   🔧 Criando modelo PL...")
        modelo = ModeloPLOtimizador(dados_extraidos, janelas, gerador.configuracao_tempo)
        
        print("   🔧 Resolvendo modelo...")
        solucao = modelo.resolver(timeout_segundos=30)
        
        print(f"   📊 Resultado: {solucao.status_solver}")
        print(f"   📊 Pedidos atendidos: {solucao.pedidos_atendidos}")
        print(f"   📊 Tempo resolução: {solucao.tempo_resolucao:.2f}s")
        
        if solucao.status_solver in ["OPTIMAL", "FEASIBLE"]:
            print("   ✅ Modelo PL funcionando!")
            return True
        else:
            print("   ⚠️ Modelo não encontrou solução ótima")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro no teste PL: {e}")
        import traceback
        traceback.print_exc()
        return False


def teste_5_sistema_real():
    """Testa com dados do sistema real"""
    print("\n🧪 TESTE 5: Sistema real...")
    
    try:
        # Importa sistema real
        from producao_paes_backup import TesteSistemaProducao
        
        print("   🔧 Criando sistema de teste...")
        sistema = TesteSistemaProducao(usar_otimizacao=False)  # Primeiro sem otimização
        
        print("   🔧 Inicializando almoxarifado...")
        sistema.inicializar_almoxarifado()
        
        print("   🔧 Criando pedidos...")
        sistema.criar_pedidos_de_producao()
        
        print(f"   📊 Pedidos criados: {len(sistema.pedidos)}")
        
        # Diagnóstica os pedidos
        pedidos_com_atividades = 0
        for pedido in sistema.pedidos:
            if hasattr(pedido, 'atividades_modulares') and pedido.atividades_modulares:
                pedidos_com_atividades += 1
        
        print(f"   📊 Pedidos com atividades: {pedidos_com_atividades}/{len(sistema.pedidos)}")
        
        # Força criação de atividades nos pedidos
        print("   🔧 Forçando criação de atividades...")
        for pedido in sistema.pedidos:
            try:
                pedido.criar_atividades_modulares_necessarias()
            except Exception as e:
                print(f"      ⚠️ Erro no pedido {pedido.id_pedido}: {e}")
        
        # Re-verifica
        pedidos_com_atividades_apos = 0
        for pedido in sistema.pedidos:
            if hasattr(pedido, 'atividades_modulares') and pedido.atividades_modulares:
                pedidos_com_atividades_apos += 1
        
        print(f"   📊 Pedidos com atividades (após força): {pedidos_com_atividades_apos}/{len(sistema.pedidos)}")
        
        if pedidos_com_atividades_apos > 0:
            print("   ✅ Sistema real com atividades funcionando!")
            return True
        else:
            print("   ⚠️ Sistema real sem atividades - usar estimativas")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro no teste sistema real: {e}")
        import traceback
        traceback.print_exc()
        return False


def teste_6_otimizacao_completa():
    """Teste completo de otimização"""
    print("\n🧪 TESTE 6: Otimização completa...")
    
    try:
        from producao_paes_backup import TesteSistemaProducao
        
        print("   🔧 Criando sistema otimizado...")
        sistema = TesteSistemaProducao(
            usar_otimizacao=True,
            resolucao_minutos=60,  # 1h para teste rápido
            timeout_pl=60  # 1 min timeout
        )
        
        print("   🔧 Executando teste completo...")
        sucesso = sistema.executar_teste_completo()
        
        if sucesso:
            print("   ✅ Otimização completa funcionando!")
            
            # Mostra estatísticas
            stats = sistema.obter_estatisticas()
            print(f"   📊 Estatísticas: {stats}")
            
            return True
        else:
            print("   ❌ Falha na otimização completa")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro no teste completo: {e}")
        import traceback
        traceback.print_exc()
        return False


def executar_todos_os_testes():
    """Executa todos os testes de diagnóstico"""
    print("🔍 DIAGNÓSTICO COMPLETO DO OTIMIZADOR PL")
    print("=" * 60)
    
    testes = [
        ("Importações", teste_1_importacoes),
        ("Extrator Básico", teste_2_extrator_basico),
        ("Gerador de Janelas", teste_3_gerador_janelas),
        ("Modelo PL", teste_4_modelo_pl),
        ("Sistema Real", teste_5_sistema_real),
        ("Otimização Completa", teste_6_otimizacao_completa)
    ]
    
    resultados = []
    
    for nome, funcao_teste in testes:
        try:
            resultado = funcao_teste()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"   ❌ ERRO CRÍTICO no teste {nome}: {e}")
            resultados.append((nome, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DO DIAGNÓSTICO")
    print("=" * 60)
    
    sucessos = 0
    for nome, sucesso in resultados:
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"   {nome}: {status}")
        if sucesso:
            sucessos += 1
    
    print(f"\n📊 Total: {sucessos}/{len(testes)} testes passaram")
    
    if sucessos == len(testes):
        print("🎉 TODOS OS TESTES PASSARAM! Sistema funcionando corretamente.")
    elif sucessos >= len(testes) - 2:
        print("✅ MAIORIA DOS TESTES PASSOU. Sistema provavelmente funcionando.")
    else:
        print("⚠️ VÁRIOS TESTES FALHARAM. Verificar configuração do sistema.")
    
    return sucessos == len(testes)


def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) > 1:
        teste_num = sys.argv[1]
        
        if teste_num == "1":
            teste_1_importacoes()
        elif teste_num == "2":
            teste_2_extrator_basico()
        elif teste_num == "3":
            teste_3_gerador_janelas()
        elif teste_num == "4":
            teste_4_modelo_pl()
        elif teste_num == "5":
            teste_5_sistema_real()
        elif teste_num == "6":
            teste_6_otimizacao_completa()
        else:
            print("❓ Testes disponíveis: 1, 2, 3, 4, 5, 6")
            print("   Ou execute sem argumentos para todos os testes")
    else:
        executar_todos_os_testes()


if __name__ == "__main__":
    main()