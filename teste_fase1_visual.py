#!/usr/bin/env python3
"""
Teste visual da Fase 1 - Recuperação de Estado
Simula a execução da opção R do menu
"""

import sys
import os

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from menu.main_menu import MenuPrincipal

print("="*80)
print("🧪 TESTE DA FASE 1 - RECUPERAÇÃO DE ESTADO")
print("="*80)
print("\nSimulando execução da opção 'R' do menu...")
print("\n" + "-"*80 + "\n")

try:
    menu = MenuPrincipal()

    # Chamar diretamente o método de recuperação
    menu.recuperar_estado_logs()

except Exception as e:
    print(f"\n❌ Erro durante teste: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-"*80)
print("\n✅ Teste da Fase 1 concluído!")
print("\n💡 Se você viu a lista de logs e as estatísticas, a Fase 1 está funcionando!")
print()