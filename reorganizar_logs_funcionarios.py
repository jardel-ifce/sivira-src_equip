#!/usr/bin/env python3
"""
🔧 REORGANIZADOR DE LOGS DE FUNCIONÁRIOS
========================================

Move logs de funcionários da pasta raiz /logs/funcionarios/ para as subpastas:
- /logs/funcionarios/sucesso - quando todos os funcionários foram alocados
- /logs/funcionarios/erro - quando há "Funcionário Indisponível"

Útil para reorganizar logs antigos após mudança de estrutura.
"""

import os
import shutil


def reorganizar_logs_funcionarios():
    """
    Reorganiza logs de funcionários da pasta raiz para sucesso/erro.
    """
    pasta_funcionarios = "logs/funcionarios"
    pasta_sucesso = "logs/funcionarios/sucesso"
    pasta_erro = "logs/funcionarios/erro"

    # Criar pastas se não existirem
    os.makedirs(pasta_sucesso, exist_ok=True)
    os.makedirs(pasta_erro, exist_ok=True)

    # Listar arquivos .log na pasta raiz de funcionários
    arquivos = [
        f for f in os.listdir(pasta_funcionarios)
        if f.endswith('.log') and os.path.isfile(os.path.join(pasta_funcionarios, f))
    ]

    if not arquivos:
        print("✅ Nenhum log para reorganizar na pasta raiz")
        return

    print(f"📋 Encontrados {len(arquivos)} logs na pasta raiz")
    print("=" * 80)

    movidos_sucesso = 0
    movidos_erro = 0

    for arquivo in arquivos:
        caminho_origem = os.path.join(pasta_funcionarios, arquivo)

        # Ler o arquivo e verificar se tem "Funcionário Indisponível"
        try:
            with open(caminho_origem, 'r', encoding='utf-8') as f:
                conteudo = f.read()

            tem_indisponivel = 'Funcionário Indisponível' in conteudo or 'Funcionário indisponível' in conteudo

            if tem_indisponivel:
                # Mover para pasta de erro
                caminho_destino = os.path.join(pasta_erro, arquivo)
                shutil.move(caminho_origem, caminho_destino)
                print(f"❌ {arquivo} → /erro")
                movidos_erro += 1
            else:
                # Mover para pasta de sucesso
                caminho_destino = os.path.join(pasta_sucesso, arquivo)
                shutil.move(caminho_origem, caminho_destino)
                print(f"✅ {arquivo} → /sucesso")
                movidos_sucesso += 1

        except Exception as e:
            print(f"⚠️ Erro ao processar {arquivo}: {e}")

    print("=" * 80)
    print(f"📊 Reorganização concluída:")
    print(f"   ✅ Movidos para /sucesso: {movidos_sucesso}")
    print(f"   ❌ Movidos para /erro: {movidos_erro}")
    print(f"   📁 Total: {movidos_sucesso + movidos_erro}")


if __name__ == "__main__":
    reorganizar_logs_funcionarios()
