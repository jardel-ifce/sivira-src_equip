#!/usr/bin/env python3
"""
Teste da nova limpeza de logs preservando restrições
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logs.gerenciador_logs import limpar_logs_inicializacao

def main():
    print("🧪 TESTANDO NOVA LIMPEZA DE LOGS")
    print("=" * 60)

    print("📋 Estado ANTES da limpeza:")
    print("=" * 40)

    # Verificar estado antes
    logs_antes = {}

    if os.path.exists("logs/restricoes"):
        restricoes = os.listdir("logs/restricoes")
        logs_antes["restricoes"] = len(restricoes)
        print(f"   🔒 logs/restricoes: {len(restricoes)} arquivo(s)")
        for arquivo in restricoes:
            print(f"      📄 {arquivo}")

    if os.path.exists("logs"):
        logs_raiz = [f for f in os.listdir("logs") if f.endswith(".log")]
        logs_antes["raiz"] = len(logs_raiz)
        print(f"   📁 logs/ (raiz): {len(logs_raiz)} log(s)")
        for arquivo in logs_raiz:
            print(f"      📄 {arquivo}")

    if os.path.exists("logs/equipamentos"):
        equipamentos = os.listdir("logs/equipamentos")
        logs_antes["equipamentos"] = len(equipamentos)
        print(f"   🔧 logs/equipamentos: {len(equipamentos)} arquivo(s)")
        for arquivo in equipamentos:
            print(f"      📄 {arquivo}")

    if os.path.exists("logs/nova_pasta"):
        nova_pasta = os.listdir("logs/nova_pasta")
        logs_antes["nova_pasta"] = len(nova_pasta)
        print(f"   📂 logs/nova_pasta: {len(nova_pasta)} arquivo(s)")
        for arquivo in nova_pasta:
            print(f"      📄 {arquivo}")

    print("\n🧹 EXECUTANDO LIMPEZA...")
    print("=" * 40)

    # Executar limpeza
    resultado = limpar_logs_inicializacao()

    print("\n📋 Estado DEPOIS da limpeza:")
    print("=" * 40)

    # Verificar estado depois
    logs_depois = {}

    if os.path.exists("logs/restricoes"):
        restricoes = os.listdir("logs/restricoes")
        logs_depois["restricoes"] = len(restricoes)
        print(f"   🔒 logs/restricoes: {len(restricoes)} arquivo(s)")
        for arquivo in restricoes:
            print(f"      📄 {arquivo}")
    else:
        logs_depois["restricoes"] = 0
        print(f"   🔒 logs/restricoes: DIRETÓRIO REMOVIDO!")

    if os.path.exists("logs"):
        logs_raiz = [f for f in os.listdir("logs") if f.endswith(".log")]
        logs_depois["raiz"] = len(logs_raiz)
        print(f"   📁 logs/ (raiz): {len(logs_raiz)} log(s)")
        for arquivo in logs_raiz:
            print(f"      📄 {arquivo}")
    else:
        logs_depois["raiz"] = 0

    if os.path.exists("logs/equipamentos"):
        equipamentos = os.listdir("logs/equipamentos")
        logs_depois["equipamentos"] = len(equipamentos)
        print(f"   🔧 logs/equipamentos: {len(equipamentos)} arquivo(s)")
        for arquivo in equipamentos:
            print(f"      📄 {arquivo}")
    else:
        logs_depois["equipamentos"] = 0

    if os.path.exists("logs/nova_pasta"):
        nova_pasta = os.listdir("logs/nova_pasta")
        logs_depois["nova_pasta"] = len(nova_pasta)
        print(f"   📂 logs/nova_pasta: {len(nova_pasta)} arquivo(s)")
        for arquivo in nova_pasta:
            print(f"      📄 {arquivo}")
    else:
        logs_depois["nova_pasta"] = 0

    print("\n🎯 RESULTADOS:")
    print("=" * 40)

    # Verificar se restrições foram preservadas
    if logs_antes.get("restricoes", 0) > 0 and logs_depois.get("restricoes", 0) > 0:
        if logs_antes["restricoes"] == logs_depois["restricoes"]:
            print("✅ RESTRIÇÕES PRESERVADAS!")
        else:
            print("⚠️ Algumas restrições foram perdidas")
    elif logs_antes.get("restricoes", 0) > 0 and logs_depois.get("restricoes", 0) == 0:
        print("❌ RESTRIÇÕES PERDIDAS!")
    else:
        print("ℹ️ Não havia restrições para preservar")

    # Verificar se outros logs foram limpos
    logs_limpos = []
    if logs_antes.get("raiz", 0) > logs_depois.get("raiz", 0):
        logs_limpos.append(f"logs/ (raiz): {logs_antes.get('raiz', 0)} → {logs_depois.get('raiz', 0)}")

    if logs_antes.get("equipamentos", 0) > logs_depois.get("equipamentos", 0):
        logs_limpos.append(f"equipamentos: {logs_antes.get('equipamentos', 0)} → {logs_depois.get('equipamentos', 0)}")

    if logs_antes.get("nova_pasta", 0) > logs_depois.get("nova_pasta", 0):
        logs_limpos.append(f"nova_pasta: {logs_antes.get('nova_pasta', 0)} → {logs_depois.get('nova_pasta', 0)}")

    if logs_limpos:
        print("✅ LOGS LIMPOS:")
        for log in logs_limpos:
            print(f"   📊 {log}")
    else:
        print("ℹ️ Nenhum log foi limpo")

    print("\n📖 RELATÓRIO DA LIMPEZA:")
    print("=" * 40)
    print(resultado)

if __name__ == "__main__":
    main()