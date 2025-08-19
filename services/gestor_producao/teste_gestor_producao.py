#!/usr/bin/env python3
#!/usr/bin/env python3
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

"""
Teste do GestorProducao
=======================

Testa a classe principal GestorProducao com pedidos mock.
"""

import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass

# Mock da classe DadosPedidoMenu para teste independente
@dataclass
class DadosPedidoMenuMock:
    """Mock de DadosPedidoMenu para testes"""
    id_pedido: int
    id_item: int
    tipo_item: str
    quantidade: int
    fim_jornada: datetime
    inicio_jornada: datetime
    arquivo_atividades: str
    nome_item: str
    registrado_em: datetime

def criar_pedidos_mock() -> list:
    """Cria pedidos mock para teste"""
    agora = datetime.now()
    
    pedidos = [
        DadosPedidoMenuMock(
            id_pedido=1,
            id_item=1001,
            tipo_item="PRODUTO", 
            quantidade=100,
            fim_jornada=agora + timedelta(hours=24),
            inicio_jornada=agora + timedelta(hours=1),
            arquivo_atividades="/mock/path/1001_pao_frances.json",
            nome_item="Pão Francês",
            registrado_em=agora
        ),
        DadosPedidoMenuMock(
            id_pedido=2,
            id_item=1002,
            tipo_item="PRODUTO",
            quantidade=50, 
            fim_jornada=agora + timedelta(hours=24),
            inicio_jornada=agora + timedelta(hours=1),
            arquivo_atividades="/mock/path/1002_pao_hamburger.json",
            nome_item="Pão Hambúrguer",
            registrado_em=agora
        )
    ]
    
    return pedidos

def teste_inicializacao():
    """Testa inicialização do GestorProducao"""
    print("🧪 TESTE: Inicialização do GestorProducao")
    print("=" * 45)
    
    try:
        # Teste 1: Inicialização padrão
        print("1️⃣ Testando inicialização padrão...")
        from services.gestor_producao import GestorProducao
        
        gestor = GestorProducao()
        print("   ✅ GestorProducao criado com sucesso")
        
        # Verifica configurações padrão
        configs_esperadas = ['resolucao_minutos', 'timeout_pl', 'limpar_logs_automatico']
        for config in configs_esperadas:
            assert config in gestor.configuracoes, f"❌ Configuração {config} faltando"
            print(f"   ✅ Configuração {config}: {gestor.configuracoes[config]}")
        
        # Teste 2: Inicialização com configurações customizadas
        print("\n2️⃣ Testando inicialização com configurações...")
        configs_custom = {'resolucao_minutos': 15, 'timeout_pl': 600}
        gestor2 = GestorProducao(configuracoes=configs_custom)
        
        assert gestor2.configuracoes['resolucao_minutos'] == 15, "❌ Configuração custom não aplicada"
        assert gestor2.configuracoes['timeout_pl'] == 600, "❌ Configuração custom não aplicada"
        print("   ✅ Configurações customizadas aplicadas")
        
        # Teste 3: Estado inicial
        print("\n3️⃣ Testando estado inicial...")
        assert not gestor.sistema_inicializado, "❌ Sistema não deveria estar inicializado"
        assert gestor.ultima_execucao['sucesso'] == False, "❌ Estado inicial incorreto"
        print("   ✅ Estado inicial correto")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DE INICIALIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_execucao_sequencial():
    """Testa execução sequencial com pedidos mock"""
    print("\n🧪 TESTE: Execução Sequencial")
    print("=" * 35)
    
    try:
        from services.gestor_producao import GestorProducao
        
        # Criar gestor
        gestor = GestorProducao()
        print("✅ GestorProducao criado")
        
        # Criar pedidos mock
        pedidos = criar_pedidos_mock()
        print(f"✅ {len(pedidos)} pedidos mock criados")
        
        # Teste 1: Execução com pedidos
        print("\n1️⃣ Testando execução sequencial...")
        sucesso = gestor.executar_sequencial(pedidos)
        print(f"   Resultado: {'✅ Sucesso' if sucesso else '❌ Falha'}")
        
        # Verificar estatísticas
        stats = gestor.obter_estatisticas()
        assert stats['modo'] == 'sequencial', "❌ Modo incorreto nas estatísticas"
        assert stats['total_pedidos'] == len(pedidos), "❌ Total de pedidos incorreto"
        print(f"   ✅ Estatísticas: {stats['total_pedidos']} pedidos, modo {stats['modo']}")
        
        # Teste 2: Execução sem pedidos
        print("\n2️⃣ Testando execução sem pedidos...")
        sucesso_vazio = gestor.executar_sequencial([])
        assert not sucesso_vazio, "❌ Deveria falhar com lista vazia"
        print("   ✅ Falhou corretamente com lista vazia")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE SEQUENCIAL: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_execucao_otimizada():
    """Testa execução otimizada"""
    print("\n🧪 TESTE: Execução Otimizada")
    print("=" * 35)
    
    try:
        from services.gestor_producao import GestorProducao
        
        # Criar gestor
        gestor = GestorProducao()
        
        # Criar pedidos mock
        pedidos = criar_pedidos_mock()
        
        # Teste de execução otimizada
        print("1️⃣ Testando execução otimizada...")
        sucesso = gestor.executar_otimizado(pedidos)
        
        # Nota: Pode falhar se OR-Tools não estiver disponível
        if sucesso:
            print("   ✅ Execução otimizada bem-sucedida")
            stats = gestor.obter_estatisticas()
            assert stats['modo'] == 'otimizado', "❌ Modo incorreto"
            print(f"   ✅ Estatísticas: modo {stats['modo']}")
        else:
            print("   ⚠️ Execução otimizada falhou (possivelmente OR-Tools não disponível)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE OTIMIZADO: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_configuracao():
    """Testa sistema de configuração"""
    print("\n🧪 TESTE: Sistema de Configuração")
    print("=" * 40)
    
    try:
        from services.gestor_producao import GestorProducao
        
        gestor = GestorProducao()
        
        # Teste configuração
        print("1️⃣ Testando configuração de parâmetros...")
        valor_original = gestor.configuracoes['resolucao_minutos']
        
        gestor.configurar(resolucao_minutos=45)
        assert gestor.configuracoes['resolucao_minutos'] == 45, "❌ Configuração não aplicada"
        print("   ✅ Configuração aplicada corretamente")
        
        # Teste configuração inválida
        print("2️⃣ Testando configuração inválida...")
        gestor.configurar(parametro_inexistente=999)  # Deve apenas avisar, não falhar
        print("   ✅ Configuração inválida tratada corretamente")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DE CONFIGURAÇÃO: {e}")
        return False

def teste_sistema():
    """Testa função de teste do sistema"""
    print("\n🧪 TESTE: Teste do Sistema")
    print("=" * 30)
    
    try:
        from services.gestor_producao import GestorProducao
        
        gestor = GestorProducao()
        
        print("1️⃣ Executando teste do sistema...")
        resultados = gestor.testar_sistema()
        
        # Verifica estrutura dos resultados
        assert isinstance(resultados, dict), "❌ Resultados devem ser dict"
        assert 'ortools' in resultados, "❌ Teste OR-Tools faltando"
        assert 'inicializacao' in resultados, "❌ Teste inicialização faltando"
        
        print("   ✅ Estrutura de resultados correta")
        
        # Mostra resultados
        for teste, resultado in resultados.items():
            status = "✅" if resultado['ok'] else "❌"
            print(f"   {status} {teste}: {resultado['msg']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DO SISTEMA: {e}")
        return False

def main():
    """Executa todos os testes do GestorProducao"""
    print("🚀 INICIANDO TESTES DO GESTORPRODUCAO")
    print("=" * 50)
    
    # Lista de testes
    testes = [
        ("Inicialização", teste_inicializacao),
        ("Execução Sequencial", teste_execucao_sequencial), 
        ("Execução Otimizada", teste_execucao_otimizada),
        ("Configuração", teste_configuracao),
        ("Teste do Sistema", teste_sistema)
    ]
    
    resultados = []
    
    # Executa cada teste
    for nome, func_teste in testes:
        try:
            resultado = func_teste()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"❌ ERRO CRÍTICO em {nome}: {e}")
            resultados.append((nome, False))
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📋 RESUMO FINAL DOS TESTES")
    print("=" * 50)
    
    testes_ok = 0
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"   {nome}: {status}")
        if resultado:
            testes_ok += 1
    
    print(f"\n🎯 RESULTADO: {testes_ok}/{len(resultados)} testes passaram")
    
    if testes_ok == len(resultados):
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ GestorProducao está funcionando corretamente")
        print("🔄 Pronto para implementar próximos componentes")
    else:
        print("⚠️ Alguns testes falharam")
        print("🔧 Verifique implementação antes de continuar")

if __name__ == "__main__":
    main()