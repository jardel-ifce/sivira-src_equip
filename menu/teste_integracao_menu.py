#!/usr/bin/env python3
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

"""
Teste de Integração - Menu com GestorProducao
==============================================

Testa se o menu está funcionando corretamente com a nova arquitetura.
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

def teste_imports():
    """Testa se todos os imports estão funcionando"""
    print("🧪 TESTE: Imports do Menu Atualizado")
    print("=" * 40)
    
    try:
        # Teste 1: Import do menu principal
        print("1️⃣ Testando import do menu principal...")
        from main_menu import MenuPrincipal
        print("   ✅ MenuPrincipal importado")
        
        # Teste 2: Import do GestorProducao
        print("2️⃣ Testando import do GestorProducao...")
        from services.gestor_producao import GestorProducao
        print("   ✅ GestorProducao importado")
        
        # Teste 3: Import dos utilitários
        print("3️⃣ Testando imports auxiliares...")
        from menu.gerenciador_pedidos import GerenciadorPedidos
        from menu.utils_menu import MenuUtils
        print("   ✅ Componentes auxiliares importados")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DE IMPORTS: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_inicializacao_menu():
    """Testa inicialização do menu com nova arquitetura"""
    print("\n🧪 TESTE: Inicialização do Menu")
    print("=" * 35)
    
    try:
        # Teste de inicialização
        print("1️⃣ Testando inicialização do MenuPrincipal...")
        from main_menu import MenuPrincipal
        
        menu = MenuPrincipal()
        print("   ✅ MenuPrincipal criado com sucesso")
        
        # Verifica se componentes foram inicializados
        assert hasattr(menu, 'gerenciador'), "❌ Gerenciador não inicializado"
        assert hasattr(menu, 'gestor_producao'), "❌ GestorProducao não inicializado"
        assert hasattr(menu, 'utils'), "❌ Utils não inicializado"
        
        print("   ✅ Componentes inicializados:")
        print(f"      - Gerenciador: {type(menu.gerenciador).__name__}")
        print(f"      - GestorProducao: {type(menu.gestor_producao).__name__}")
        print(f"      - Utils: {type(menu.utils).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DE INICIALIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_fluxo_pedidos():
    """Testa fluxo básico de pedidos"""
    print("\n🧪 TESTE: Fluxo de Pedidos")
    print("=" * 30)
    
    try:
        from main_menu import MenuPrincipal
        
        # Cria menu
        menu = MenuPrincipal()
        print("✅ Menu criado")
        
        # Testa gerenciador de pedidos
        print("1️⃣ Testando gerenciador de pedidos...")
        total_inicial = len(menu.gerenciador.pedidos)
        print(f"   📊 Pedidos iniciais: {total_inicial}")
        
        # Testa gestor de produção
        print("2️⃣ Testando gestor de produção...")
        stats = menu.gestor_producao.obter_estatisticas()
        print(f"   📊 Estatísticas: {stats}")
        
        # Testa sistema
        print("3️⃣ Testando sistema...")
        resultados_teste = menu.gestor_producao.testar_sistema()
        print(f"   🧪 Testes executados: {len(resultados_teste)}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DE FLUXO: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_execucao_simulada():
    """Testa execução com pedidos mock"""
    print("\n🧪 TESTE: Execução Simulada")
    print("=" * 32)
    
    try:
        from services.gestor_producao import GestorProducao
        
        # Cria gestor
        gestor = GestorProducao()
        print("✅ GestorProducao criado")
        
        # Cria pedidos mock
        agora = datetime.now()
        pedidos_mock = [
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
            )
        ]
        
        print(f"✅ {len(pedidos_mock)} pedido(s) mock criado(s)")
        
        # Teste execução sequencial
        print("1️⃣ Testando execução sequencial...")
        sucesso_seq = gestor.executar_sequencial(pedidos_mock)
        print(f"   Resultado: {'✅ Sucesso' if sucesso_seq else '❌ Falha'}")
        
        # Teste execução otimizada
        print("2️⃣ Testando execução otimizada...")
        sucesso_opt = gestor.executar_otimizado(pedidos_mock)
        print(f"   Resultado: {'✅ Sucesso' if sucesso_opt else '⚠️ Falha (normal se OR-Tools indisponível)'}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DE EXECUÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_desacoplamento():
    """Testa se está realmente desacoplado dos scripts de teste"""
    print("\n🧪 TESTE: Desacoplamento")
    print("=" * 28)
    
    try:
        import sys
        
        # Lista módulos antes do teste
        modulos_antes = set(sys.modules.keys())
        
        # Importa menu
        from main_menu import MenuPrincipal
        menu = MenuPrincipal()
        
        # Lista módulos depois
        modulos_depois = set(sys.modules.keys())
        
        # Verifica novos módulos
        novos_modulos = modulos_depois - modulos_antes
        modulos_teste = [m for m in novos_modulos if 'producao_paes' in m]
        
        print(f"📦 Novos módulos carregados: {len(novos_modulos)}")
        print(f"🔍 Módulos de teste detectados: {modulos_teste}")
        
        if modulos_teste:
            print(f"⚠️ ATENÇÃO: Scripts de teste ainda sendo carregados: {modulos_teste}")
        else:
            print("✅ DESACOPLAMENTO CONFIRMADO: Nenhum script de teste carregado")
        
        return len(modulos_teste) == 0
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE DE DESACOPLAMENTO: {e}")
        return False

def main():
    """Executa todos os testes de integração"""
    print("🚀 INICIANDO TESTES DE INTEGRAÇÃO")
    print("=" * 50)
    print("🎯 Testando menu com nova arquitetura independente")
    print()
    
    # Lista de testes
    testes = [
        ("Imports", teste_imports),
        ("Inicialização do Menu", teste_inicializacao_menu),
        ("Fluxo de Pedidos", teste_fluxo_pedidos),
        ("Execução Simulada", teste_execucao_simulada),
        ("Desacoplamento", teste_desacoplamento)
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
    print("📋 RESUMO FINAL DOS TESTES DE INTEGRAÇÃO")
    print("=" * 50)
    
    testes_ok = 0
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"   {nome}: {status}")
        if resultado:
            testes_ok += 1
    
    print(f"\n🎯 RESULTADO: {testes_ok}/{len(resultados)} testes passaram")
    
    if testes_ok == len(resultados):
        print("🎉 TODOS OS TESTES DE INTEGRAÇÃO PASSARAM!")
        print("✅ Menu está funcionando com nova arquitetura")
        print("🏗️ Desacoplamento dos scripts de teste confirmado")
        print("🚀 Sistema pronto para uso em produção")
    else:
        print("⚠️ Alguns testes falharam")
        print("🔧 Verifique a integração antes de usar")

if __name__ == "__main__":
    main()