#!/usr/bin/env python3
"""
Debug Menu Específico
====================

Simula exatamente o que o menu faz para encontrar a diferença
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona paths necessários  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

from menu.gerenciador_pedidos import GerenciadorPedidos
from services.gestor_producao.gestor_producao import GestorProducao

def simular_menu_exato():
    """Simula EXATAMENTE o que o menu faz"""
    import os  # ✅ CORREÇÃO: Import local
    
    print("🎭 SIMULANDO MENU INTERATIVO EXATO")
    print("=" * 60)
    
    try:
        # PASSO 1: Simular inicialização do menu (como main_menu.py)
        print("\n1️⃣ Simulando inicialização do menu...")
        print("📋 Inicializando GerenciadorPedidos...")
        gerenciador = GerenciadorPedidos()
        print(f"   ✅ GerenciadorPedidos criado")
        
        print("🏭 Inicializando GestorProducao...")
        gestor_producao = GestorProducao()
        print(f"   ✅ GestorProducao criado")
        
        # PASSO 2: Simular registro de pedido (como menu faz)
        print("\n2️⃣ Simulando registro de pedido...")
        
        # Dados que o menu coletaria
        fim_jornada = datetime.now() + timedelta(days=1)
        fim_jornada = fim_jornada.replace(hour=7, minute=0, second=0, microsecond=0)
        
        sucesso, mensagem = gerenciador.registrar_pedido(
            id_item=1001,
            tipo_item="PRODUTO", 
            quantidade=450,
            fim_jornada=fim_jornada
        )
        
        print(f"   Registro: {sucesso} - {mensagem}")
        
        if not sucesso:
            print("❌ Falha no registro!")
            return False
        
        print(f"   ✅ {len(gerenciador.pedidos)} pedido(s) registrado(s)")
        
        # PASSO 3: Simular execução (como menu faz)
        print("\n3️⃣ Simulando execução via menu...")
        
        # Debug: Verificar pedidos antes da execução
        print("🔍 DEBUG DOS PEDIDOS ANTES DA EXECUÇÃO:")
        for i, pedido in enumerate(gerenciador.pedidos):
            print(f"   Pedido {i+1}:")
            print(f"      ID: {pedido.id_pedido}")
            print(f"      Item: {pedido.id_item} ({pedido.nome_item})")
            print(f"      Tipo: {pedido.tipo_item}")
            print(f"      Quantidade: {pedido.quantidade}")
            print(f"      Arquivo: {pedido.arquivo_atividades}")
            arquivo_existe = os.path.exists(pedido.arquivo_atividades) if hasattr(os, 'path') else "N/A"
            print(f"      Arquivo existe: {arquivo_existe}")
            print(f"      Início: {pedido.inicio_jornada}")
            print(f"      Fim: {pedido.fim_jornada}")
        
        # Execução EXATA como o menu faz
        print(f"\n   ⚡ Executando pedidos via gestor_producao...")
        
        try:
            # ESTA É A CHAMADA EXATA QUE O MENU FAZ!
            sucesso_exec = gestor_producao.executar_sequencial(gerenciador.pedidos)
            print(f"   Execução: {sucesso_exec}")
            
            if sucesso_exec:
                print(f"   ✅ Menu simulation: SUCESSO!")
                
                # Verificar logs gerados
                print(f"\n🔍 Verificando logs gerados...")
                try:
                    import os
                    pasta_logs = "logs/equipamentos"
                    if os.path.exists(pasta_logs):
                        arquivos = [f for f in os.listdir(pasta_logs) if f.endswith('.log')]
                        print(f"   📁 {len(arquivos)} arquivo(s) de log encontrado(s)")
                        for arquivo in arquivos:
                            print(f"      📄 {arquivo}")
                    else:
                        print(f"   📁 Pasta de logs não existe")
                except Exception as log_err:
                    print(f"   ⚠️ Erro ao verificar logs: {log_err}")
                
                return True
            else:
                print(f"   ❌ Menu simulation: FALHA na execução!")
                return False
                
        except Exception as e:
            print(f"   ❌ ERRO NA EXECUÇÃO DO MENU: {e}")
            print(f"   ❌ Tipo: {type(e)}")
            
            # Stack trace completo
            import traceback
            print(f"\n📋 STACK TRACE COMPLETO:")
            traceback.print_exc()
            
            # Debug adicional do estado
            print(f"\n🔍 DEBUG ESTADO DO GESTOR:")
            print(f"   gestor_producao.sistema_inicializado: {gestor_producao.sistema_inicializado}")
            print(f"   gestor_producao.configurador_ambiente: {gestor_producao.configurador_ambiente}")
            print(f"   gestor_producao.conversor_pedidos: {gestor_producao.conversor_pedidos}")
            print(f"   gestor_producao.executor_pedidos: {gestor_producao.executor_pedidos}")
            
            if gestor_producao.configurador_ambiente:
                print(f"   configurador.inicializado: {gestor_producao.configurador_ambiente.inicializado}")
                print(f"   configurador.gestor_almoxarifado: {gestor_producao.configurador_ambiente.gestor_almoxarifado}")
            
            if gestor_producao.conversor_pedidos:
                print(f"   conversor.gestor_almoxarifado: {gestor_producao.conversor_pedidos.gestor_almoxarifado}")
            
            return False
        
    except Exception as e:
        print(f"\n❌ Erro durante simulação do menu: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_diferenca_pedidos():
    """Compara pedidos criados pelo menu vs teste direto"""
    print("\n🔍 DEBUG: DIFERENÇA NOS PEDIDOS")
    print("-" * 40)
    
    # Pedido do menu
    print("📋 Criando pedido via GerenciadorPedidos (como menu)...")
    gerenciador = GerenciadorPedidos()
    
    fim_jornada = datetime.now() + timedelta(days=1)
    fim_jornada = fim_jornada.replace(hour=7, minute=0, second=0, microsecond=0)
    
    gerenciador.registrar_pedido(
        id_item=1001,
        tipo_item="PRODUTO",
        quantidade=450, 
        fim_jornada=fim_jornada
    )
    
    pedido_menu = gerenciador.pedidos[0]
    
    # Pedido direto (que funciona)
    print("📋 Criando pedido direto (que funciona)...")
    from menu.gerenciador_pedidos import DadosPedidoMenu
    
    pedido_direto = DadosPedidoMenu(
        id_pedido=1,
        id_item=1001,
        tipo_item="PRODUTO",
        quantidade=450,
        fim_jornada=fim_jornada,
        inicio_jornada=fim_jornada - timedelta(days=3),
        arquivo_atividades="/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/produtos/atividades/1001_pao_frances.json",
        nome_item="Pão Francês",
        registrado_em=datetime.now()
    )
    
    # Comparar
    print("\n🔍 COMPARAÇÃO:")
    print(f"   Menu - ID: {pedido_menu.id_pedido} | Direto - ID: {pedido_direto.id_pedido}")
    print(f"   Menu - Item: {pedido_menu.id_item} | Direto - Item: {pedido_direto.id_item}")
    print(f"   Menu - Tipo: {pedido_menu.tipo_item} | Direto - Tipo: {pedido_direto.tipo_item}")
    print(f"   Menu - Qtd: {pedido_menu.quantidade} | Direto - Qtd: {pedido_direto.quantidade}")
    print(f"   Menu - Arquivo: {pedido_menu.arquivo_atividades}")
    print(f"   Direto - Arquivo: {pedido_direto.arquivo_atividades}")
    print(f"   Menu - Arquivo existe: {os.path.exists(pedido_menu.arquivo_atividades)}")
    print(f"   Direto - Arquivo existe: {os.path.exists(pedido_direto.arquivo_atividades)}")

if __name__ == "__main__":
    # Debug da diferença nos pedidos
    debug_diferenca_pedidos()
    
    # Simulação exata do menu
    resultado = simular_menu_exato()
    
    print(f"\n📊 RESULTADO:")
    print(f"   Simulação do menu: {'✅ Funciona' if resultado else '❌ Falha'}")