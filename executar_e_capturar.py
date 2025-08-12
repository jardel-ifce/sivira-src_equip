#!/usr/bin/env python3
"""
Script para executar o sistema e capturar logs automaticamente
"""

import subprocess
import sys
import os
from datetime import datetime

def capturar_logs():
    """Executa o sistema e captura todos os logs"""
    
    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs_sistema_{timestamp}.txt"
    
    print("🔍 CAPTURADOR DE LOGS DO SISTEMA")
    print("=" * 50)
    print(f"📝 Arquivo: {log_file}")
    print(f"⏱️  Timestamp: {datetime.now()}")
    print("")
    
    try:
        print("🚀 Executando main_menu.py...")
        print("📋 Todos os logs serão salvos automaticamente")
        print("⚠️  Pressione Ctrl+C para parar")
        print("")
        
        # Executar e capturar
        with open(log_file, 'w', encoding='utf-8') as f:
            # Escrever cabeçalho
            f.write(f"# Logs do Sistema de Produção\n")
            f.write(f"# Capturado em: {datetime.now()}\n")
            f.write(f"# Comando: python main_menu.py\n")
            f.write("=" * 80 + "\n\n")
            
            # Executar processo
            process = subprocess.Popen(
                [sys.executable, 'main_menu.py'],
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
    except FileNotFoundError:
        print("❌ Erro: main_menu.py não encontrado no diretório atual")
    except Exception as e:
        print(f"❌ Erro durante captura: {e}")

def criar_versao_filtrada(log_file, timestamp):
    """Cria versão filtrada dos logs"""
    filtered_file = f"logs_filtrados_{timestamp}.txt"
    
    print(f"\n🔍 Criando versão filtrada...")
    
    # Padrões para filtrar
    padroes_interesse = [
        "🔄 Executando pedido",
        "Fase ",
        "Pedidos atendidos",
        "Taxa de atendimento", 
        "Executados",
        "Falhas",
        "Tempo máximo de espera",
        "já possui",
        "do produto",
        "já alocado no nível",
        "ALOCAÇÃO FALHOU",
        "Rollback concluído",
        "Atividade atual",
        "Atividade sucessora", 
        "Atraso detectado",
        "Máximo permitido",
        "Intervalo tentado",
        "ERROR",
        "WARNING"
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
                        if any(termo in linha for termo in ["ALOCAÇÃO FALHOU", "já possui", "ERROR"]):
                            falhas += 1
        
        print(f"✅ Versão filtrada salva em: {filtered_file}")
        print(f"📊 Linhas filtradas: {linhas_filtradas}")
        print(f"\n📈 ESTATÍSTICAS:")
        print(f"   🔄 Execuções de pedido: {execucoes}")
        print(f"   ❌ Falhas detectadas: {falhas}")
        
        if execucoes > 1:
            print(f"   ⚠️  ATENÇÃO: Múltiplas execuções detectadas!")
        
        print(f"\n📁 Arquivos gerados:")
        print(f"   📄 Completo: {log_file}")
        print(f"   🔍 Filtrado: {filtered_file}")
        
    except Exception as e:
        print(f"❌ Erro ao criar versão filtrada: {e}")

if __name__ == "__main__":
    # Verificar se main_menu.py existe
    if not os.path.exists('main_menu.py'):
        print("❌ Erro: main_menu.py não encontrado no diretório atual")
        print("📁 Certifique-se de estar no diretório correto")
        sys.exit(1)
    
    capturar_logs()
