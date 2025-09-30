#!/usr/bin/env python3
"""
Teste do ExecutorPedidos - VERIFICAÇÃO DE LOGS
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona paths necessários  
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip") 
from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente
from services.gestores.producao.conversor_pedidos import ConversorPedidos
from services.gestores.producao.executor_pedidos import ExecutorPedidos
from menu.gerenciador_pedidos import DadosPedidoMenu

def criar_pedido_teste():
    """Cria pedido simples para teste de logs"""
    fim_jornada = datetime.now() + timedelta(days=1)
    fim_jornada = fim_jornada.replace(hour=7, minute=0, second=0, microsecond=0)
    inicio_jornada = fim_jornada - timedelta(days=3)
    
    return DadosPedidoMenu(
        id_pedido=1,
        id_item=1005,  # Pão Trança de Queijo Finos
        tipo_item="PRODUTO",
        quantidade=70,
        fim_jornada=fim_jornada,
        inicio_jornada=inicio_jornada,
        arquivo_atividades="/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/produtos/atividades/1005_pao_tranca_de_queijo_finos.json",
        nome_item="Pão Trança de Queijo Finos",
        registrado_em=datetime.now()
    )

def verificar_logs_gerados():
    """Verifica se logs foram realmente gerados"""
    print("\n🔍 VERIFICANDO LOGS GERADOS:")
    
    pasta_logs = "logs/equipamentos"
    if not os.path.exists(pasta_logs):
        print(f"   ❌ Pasta não existe: {pasta_logs}")
        return False
    
    arquivos_log = [f for f in os.listdir(pasta_logs) if f.endswith(".log")]
    
    if not arquivos_log:
        print(f"   ❌ Nenhum log encontrado em {pasta_logs}")
        return False
    
    print(f"   ✅ {len(arquivos_log)} arquivo(s) de log encontrado(s):")
    
    for arquivo in arquivos_log:
        caminho = os.path.join(pasta_logs, arquivo)
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            print(f"      📄 {arquivo} ({len(linhas)} linhas)")
            
            # Mostra primeiras 3 linhas como exemplo
            if linhas:
                print(f"         Exemplo de linha:")
                print(f"         {linhas[0].strip()}")
                
        except Exception as e:
            print(f"      ❌ Erro ao ler {arquivo}: {e}")
    
    return True

def testar_executor_logs():
    print("🧪 TESTE DO EXECUTOR - GERAÇÃO DE LOGS")
    print("=" * 60)
    
    try:
        # 1. Inicializar ambiente
        print("\n1️⃣ Inicializando ambiente...")
        configurador = ConfiguradorAmbiente()
        if not configurador.inicializar_ambiente():
            print("❌ Falha na inicialização!")
            return False
        
        # 2. Converter pedido
        print("\n2️⃣ Convertendo pedido...")
        conversor = ConversorPedidos(configurador.gestor_almoxarifado)
        pedido_teste = criar_pedido_teste()
        pedidos_convertidos = conversor.converter_pedidos([pedido_teste])
        
        if not pedidos_convertidos:
            print("❌ Falha na conversão!")
            return False
        
        # 3. Verificar logs antes da execução
        print("\n3️⃣ Verificando logs ANTES da execução...")
        executor = ExecutorPedidos()
        logs_antes = executor.verificar_logs_existentes()
        print(f"   📊 Logs equipamentos antes: {logs_antes.get('logs/equipamentos', {}).get('total_arquivos', 0)} arquivos")
        
        # 4. Executar pedidos (AQUI OS LOGS SÃO GERADOS!)
        print("\n4️⃣ Executando pedidos...")
        print("🎯 ATENÇÃO: Logs devem ser gerados agora!")
        
        sucesso = executor.executar_sequencial(pedidos_convertidos)
        
        # 5. Verificar logs APÓS execução
        print("\n5️⃣ Verificando logs APÓS execução...")
        logs_apos = executor.verificar_logs_existentes()
        print(f"   📊 Logs equipamentos após: {logs_apos.get('logs/equipamentos', {}).get('total_arquivos', 0)} arquivos")
        
        # 6. Análise detalhada dos logs
        logs_funcionaram = verificar_logs_gerados()
        
        # 7. Resultado final
        print(f"\n📋 RESULTADO DO TESTE:")
        print(f"   Execução: {'✅ Sucesso' if sucesso else '❌ Falha'}")
        print(f"   Logs gerados: {'✅ Sim' if logs_funcionaram else '❌ Não'}")
        
        return sucesso and logs_funcionaram
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    testar_executor_logs()