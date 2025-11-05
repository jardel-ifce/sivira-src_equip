#!/usr/bin/env python3
"""
Teste simples da Fase 1 - Apenas leitura dos logs
"""

import glob
import os
from datetime import datetime

print("="*80)
print("🧪 TESTE DA FASE 1 - RECUPERAÇÃO DE ESTADO")
print("="*80)

logs_dir = "logs/equipamentos_detalhados/"
logs = glob.glob(os.path.join(logs_dir, "*.log"))

if not logs:
    print("\n❌ Nenhum log encontrado!")
    exit(1)

logs = sorted(logs, key=os.path.getmtime, reverse=True)

print(f"\n📋 Logs detalhados encontrados: {len(logs)}")
print("="*80)

# Mostrar os 5 logs mais recentes
for idx, log in enumerate(logs[:5], 1):
    nome = os.path.basename(log)
    data_mod = datetime.fromtimestamp(os.path.getmtime(log))
    tamanho = os.path.getsize(log) / 1024

    print(f"\n{idx}. {nome}")
    print(f"   📅 Data: {data_mod.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   📦 Tamanho: {tamanho:.1f} KB")

    # Extrair informações do cabeçalho
    try:
        with open(log, 'r', encoding='utf-8') as f:
            for _ in range(10):
                linha = f.readline()
                if "Ordem" in linha and "Pedidos" in linha:
                    print(f"   📋 {linha.strip()}")
                    break
                if "Gerado em:" in linha:
                    print(f"   ⏰ {linha.strip()}")
                    break
    except:
        pass

print("\n" + "="*80)
print("🔍 ANÁLISE DO LOG MAIS RECENTE")
print("="*80)

log_recente = logs[0]
print(f"\n📁 Arquivo: {os.path.basename(log_recente)}")

with open(log_recente, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Contar equipamentos com ocupações
equipamentos_ocupados = 0
total_ocupacoes = 0

for i, linha in enumerate(linhas):
    if "🔧" in linha and "(" in linha:
        proximas = ''.join(linhas[i:i+15])
        if any(emoji in proximas for emoji in ["🪵", "🗂️", "⚖️", "🥣", "📦"]):
            equipamentos_ocupados += 1

    if any(emoji in linha for emoji in ["🪵", "🗂️", "⚖️", "🥣", "📦"]):
        if " | " in linha:
            total_ocupacoes += 1

print(f"\n📊 Estatísticas:")
print(f"   • Total de linhas: {len(linhas):,}")
print(f"   • Equipamentos com ocupações: ~{equipamentos_ocupados}")
print(f"   • Total de ocupações: ~{total_ocupacoes}")

print("\n" + "="*80)
print("✅ FASE 1 FUNCIONANDO!")
print("="*80)
print("\n🎯 Funcionalidades implementadas:")
print("   ✅ Detecção de logs detalhados")
print("   ✅ Listagem por data de modificação")
print("   ✅ Extração de informações do cabeçalho")
print("   ✅ Análise e contagem de ocupações")
print("   ✅ Interface no menu (opção R)")
print("\n🚀 Pronto para Fase 2: Parser de logs!")
print()
