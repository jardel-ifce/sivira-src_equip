#!/usr/bin/env python3
"""
Script para executar o sistema e capturar logs - VERSÃO CORRIGIDA
Procura o arquivo main_menu.py automaticamente
"""

import subprocess
import sys
import os
from datetime import datetime
import glob

def encontrar_main_menu():
    """Procura o arquivo main_menu.py no sistema"""
    locais_possiveis = [
        # Caminho específico do usuário
        "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/menu/main_menu.py",
        # Diretório atual
        "./main_menu.py",
        # Diretório menu
        "./menu/main_menu.py", 
        # Diretório pai
        "../main_menu.py",
        # Busca recursiva limitada
    ]
    
    # Verificar locais específicos primeiro
    for local in locais_possiveis:
        if os.path.exists(local):
            return os.path.abspath(local)
    
    # Busca recursiva nos diretórios próximos
    for root, dirs, files in os.walk("."):
        if "main_menu.py" in files:
            caminho = os.path.join(root, "main_menu.py")
            return os.path.abspath(caminho)
    
    # Busca no diretório pai
    for root, dirs, files in os.walk(".."):
        if "main_menu.py" in files:
            caminho = os.path.join(root, "main_menu.py")
            return os.path.abspath(caminho)
    
    return None

def capturar_logs():
    """Executa o sistema e captura todos os logs"""
    
    # Encontrar main_menu.py
    main_menu_path = encontrar_main_menu()
    
    if not main_menu_path:
        print("❌ ERRO: main_menu.py não encontrado!")
        print("\n🔍 Lugares procurados:")
        print("   ./main_menu.py")
        print("   ./menu/main_menu.py") 
        print("   ../main_menu.py")
        print("   (busca recursiva)")
        print("\n📁 Diretório atual:", os.getcwd())
        print("📋 Arquivos no diretório atual:")
        for arquivo in os.listdir("."):
            if arquivo.endswith(".py"):
                print(f"   📄 {arquivo}")
        return
    
    print("✅ Encontrado:", main_menu_path)
    
    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs_sistema_{timestamp}.txt"
    
    print("\n🔍 CAPTURADOR DE LOGS DO SISTEMA")
    print("=" * 50)
    print(f"📝 Arquivo: {log_file}")
    print(f"📁 Script: {main_menu_path}")
    print(f"⏱️  Timestamp: {datetime.now()}")
    print("")
    
    try:
        print("🚀 Executando sistema...")
        print("📋 Todos os logs serão salvos automaticamente")
        print("⚠️  Pressione Ctrl+C para parar")
        print("🎯 Execute opção 6 (OTIMIZADO) para reproduzir o erro")
        print("")
        
        # Mudar para o diretório do script
        script_dir = os.path.dirname(main_menu_path)
        if script_dir:
            os.chdir(script_dir)
            print(f"📂 Mudando para diretório: {script_dir}")
        
        # Executar e capturar
        with open(log_file, 'w', encoding='utf-8') as f:
            # Escrever cabeçalho
            f.write(f"# Logs do Sistema de Produção\n")
            f.write(f"# Capturado em: {datetime.now()}\n")
            f.write(f"# Script: {main_menu_path}\n")
            f.write(f"# Diretório: {os.getcwd()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Executar processo
            process = subprocess.Popen(
                [sys.executable, os.path.basename(main_menu_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Capturar saída linha por linha
            linha_count = 0
            for linha in process.stdout:
                # Mostrar no terminal
                print(linha, end='')
                # Salvar no arquivo
                f.write(linha)
                linha_count += 1
                
                # Flush para garantir que escreve imediatamente
                f.flush()
            
            # Aguardar processo terminar
            process.wait()
        
        print(f"\n✅ Logs salvos em: {log_file}")
        print(f"📊 Linhas capturadas: {linha_count}")
        
        # Criar versão filtrada
        criar_versao_filtrada(log_file, timestamp)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Captura interrompida pelo usuário")
        print(f"📄 Logs parciais salvos em: {log_file}")
    except Exception as e:
        print(f"❌ Erro durante captura: {e}")

def criar_versao_filtrada(log_file, timestamp):
    """Cria versão filtrada dos logs"""
    filtered_file = f"logs_filtrados_{timestamp}.txt"
    
    print(f"\n🔍 Criando versão filtrada...")
    
    # Padrões para filtrar - MAIS ESPECÍFICOS
    padroes_interesse = [
        "🔄 Executando pedido",
        "Fase ",
        "Pedidos atendidos",
        "Taxa de atendimento", 
        "Executados:",
        "❌ Falhas:",
        "Tempo máximo de espera excedido",
        "já possui",
        "do produto id",
        "já alocado no nível",
        "ALOCAÇÃO FALHOU",
        "Rollback concluído",
        "Atividade atual:",
        "Atividade sucessora:", 
        "Atraso detectado:",
        "Máximo permitido:",
        "Intervalo tentado:",
        "Limite da jornada atingido",
        "Nenhum forno conseguiu atender",
        "[ERROR]",
        "[WARNING]",
        "❌ Falha no pedido",
        "RuntimeError",
        "Exception"
    ]
    
    try:
        linhas_filtradas = 0
        execucoes = 0
        falhas = 0
        
        with open(log_file, 'r', encoding='utf-8') as input_f:
            with open(filtered_file, 'w', encoding='utf-8') as output_f:
                # Cabeçalho
                output_f.write(f"# Logs Filtrados - {datetime.now()}\n")
                output_f.write(f"# Fonte: {log_file}\n")
                output_f.write("=" * 80 + "\n\n")
                
                for linha in input_f:
                    # Verificar se linha contém algum padrão de interesse
                    if any(padrao in linha for padrao in padroes_interesse):
                        output_f.write(linha)
                        linhas_filtradas += 1
                        
                        # Contar estatísticas
                        if "🔄 Executando pedido" in linha:
                            execucoes += 1
                        if any(termo in linha for termo in ["ALOCAÇÃO FALHOU", "já possui", "[ERROR]", "❌ Falha"]):
                            falhas += 1
        
        print(f"✅ Versão filtrada salva em: {filtered_file}")
        print(f"📊 Linhas filtradas: {linhas_filtradas}")
        
        if linhas_filtradas > 0:
            print(f"\n📈 ESTATÍSTICAS:")
            print(f"   🔄 Execuções de pedido: {execucoes}")
            print(f"   ❌ Falhas detectadas: {falhas}")
            
            if execucoes > 1:
                print(f"   ⚠️  ATENÇÃO: Múltiplas execuções detectadas!")
            
            print(f"\n📁 Arquivos gerados:")
            print(f"   📄 Completo: {log_file}")
            print(f"   🔍 Filtrado: {filtered_file}")
            
            print(f"\n🎯 PRÓXIMOS PASSOS:")
            print(f"   1. Copie o conteúdo de {filtered_file}")
            print(f"   2. Cole para análise do problema")
        else:
            print("⚠️ Nenhuma linha relevante encontrada nos logs")
        
    except Exception as e:
        print(f"❌ Erro ao criar versão filtrada: {e}")

def mostrar_uso():
    """Mostra como usar o script"""
    print("🔧 COMO USAR:")
    print("1. Execute este script no terminal")
    print("2. O menu do sistema será aberto")
    print("3. Registre um pedido (opção 1)")
    print("4. Execute modo otimizado (opção 6)")
    print("5. Reproduza o erro")
    print("6. Os logs serão salvos automaticamente")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        mostrar_uso()
    else:
        capturar_logs()
