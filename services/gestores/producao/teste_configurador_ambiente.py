#!/usr/bin/env python3
"""
Teste do ConfiguradorAmbiente implementado
"""
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip") 
import sys
import os

# Adiciona paths necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gestores.producao.configurador_ambiente import ConfiguradorAmbiente

def testar_configurador():
    print("🧪 TESTE DO CONFIGURADOR AMBIENTE")
    print("=" * 50)
    
    # Teste 1: Criação
    print("\n1️⃣ Testando criação...")
    configurador = ConfiguradorAmbiente()
    status = configurador.obter_status()
    print(f"   Status inicial: {status}")
    
    # Teste 2: Inicialização
    print("\n2️⃣ Testando inicialização...")
    sucesso = configurador.inicializar_ambiente()
    print(f"   Sucesso: {sucesso}")
    
    if sucesso:
        status = configurador.obter_status()
        print(f"   Status após init: {status}")
    
    # Teste 3: Limpeza
    print("\n3️⃣ Testando limpeza...")
    sucesso_limpeza = configurador.limpar_ambiente()
    print(f"   Limpeza: {sucesso_limpeza}")
    
    return sucesso

if __name__ == "__main__":
    testar_configurador()