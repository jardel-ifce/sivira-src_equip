#!/usr/bin/env python3
"""
Teste específico para verificar se restrições são registradas durante produção
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def limpar_ambiente():
    """Limpa ambiente de teste"""
    print("🧹 Limpando ambiente...")

    # Limpar diretório de restrições
    import shutil
    if os.path.exists("logs/restricoes"):
        shutil.rmtree("logs/restricoes")
        print("🗑️ Diretório logs/restricoes removido")

    print("✅ Ambiente limpo!")

def executar_producao_simples():
    """Executa uma produção simples de 1 coxinha"""
    print("\n🧪 TESTANDO REGISTRO DE RESTRIÇÕES NA PRODUÇÃO")
    print("=" * 60)

    # Importar e executar o script de produção
    try:
        print("🚀 Executando producao_coxinhas_sequencial.py...")

        # Executar como subprocess para capturar output
        import subprocess
        result = subprocess.run(
            [sys.executable, "producao_coxinhas_sequencial.py"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutos timeout
        )

        print(f"📤 Return code: {result.returncode}")

        if result.stdout:
            print("📋 STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("⚠️ STDERR:")
            print(result.stderr)

    except subprocess.TimeoutExpired:
        print("❌ Script demorou mais que 2 minutos - cancelado")
    except Exception as e:
        print(f"❌ Erro ao executar script: {e}")

def verificar_restricoes():
    """Verifica se restrições foram registradas"""
    print("\n🔍 VERIFICANDO RESTRIÇÕES REGISTRADAS")
    print("=" * 60)

    restricoes_dir = "logs/restricoes"

    if not os.path.exists(restricoes_dir):
        print(f"❌ Diretório {restricoes_dir} não existe")
        return False

    arquivos = os.listdir(restricoes_dir)

    if not arquivos:
        print(f"❌ Nenhum arquivo encontrado em {restricoes_dir}")
        return False

    print(f"✅ Encontrados {len(arquivos)} arquivo(s):")

    for arquivo in arquivos:
        print(f"   📄 {arquivo}")

        # Ler e mostrar conteúdo
        caminho = os.path.join(restricoes_dir, arquivo)
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                import json
                dados = json.load(f)

                print(f"      🔸 Ordem: {dados.get('ordem')}")
                print(f"      🔸 Total restrições: {dados.get('total_restricoes', 0)}")

                for restricao in dados.get('atividades_com_restricao', []):
                    print(f"      🔸 Atividade {restricao['id_atividade']}: {restricao['capacidade_atual']}g < {restricao['capacidade_minima']}g")
                    print(f"          Equipamento: {restricao['equipamento']}")
                    print(f"          Status: {restricao['status']}")

        except Exception as e:
            print(f"      ❌ Erro ao ler arquivo: {e}")

    return True

def main():
    """Execução principal"""
    print("🧪 TESTE DE REGISTRO DE RESTRIÇÕES")
    print("=" * 60)

    try:
        # 1. Limpar ambiente
        limpar_ambiente()

        # 2. Executar produção
        executar_producao_simples()

        # 3. Verificar restrições
        sucesso = verificar_restricoes()

        # 4. Resultado
        print("\n" + "=" * 60)
        print("📋 RESULTADO:")
        print("=" * 60)

        if sucesso:
            print("🎉 SUCESSO! Restrições foram registradas")
        else:
            print("❌ FALHA! Nenhuma restrição foi registrada")

    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()