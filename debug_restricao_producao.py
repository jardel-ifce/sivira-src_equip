#!/usr/bin/env python3
"""
Debug: Verificar por que restrições não são salvas durante produção
"""

import sys
import os
import json
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from factory.fabrica_equipamentos import hotmix_1
from models.equipamentos.hot_mix import HotMix

def verificar_estado_hotmix():
    """Verifica estado atual do HotMix"""
    print("🔍 ESTADO ATUAL DO HOTMIX")
    print("=" * 50)
    print(f"   Nome: {hotmix_1.nome}")
    print(f"   Capacidade mínima: {hotmix_1.capacidade_gramas_min}g")
    print(f"   Capacidade máxima: {hotmix_1.capacidade_gramas_max}g")
    print(f"   Ocupações atuais: {len(hotmix_1.ocupacoes)}")

    for i, ocupacao in enumerate(hotmix_1.ocupacoes):
        print(f"      {i+1}. ID {ocupacao.id_item}: {ocupacao.quantidade}g de {ocupacao.inicio.strftime('%H:%M')} a {ocupacao.fim.strftime('%H:%M')}")

def verificar_metodo_validar_capacidade():
    """Testa o método validar_capacidade diretamente"""
    print("\n🧪 TESTE DIRETO DO MÉTODO validar_capacidade")
    print("=" * 50)

    # Contexto de teste
    contexto = {
        'id_ordem': 1,
        'id_pedido': 1,
        'id_atividade': 20031,
        'id_item': 2003,
        'inicio': datetime(2025, 6, 26, 6, 15),
        'fim': datetime(2025, 6, 26, 6, 27),
        'velocidade': 'BAIXA',
        'chama': 'BAIXA',
        'pressao': ['BAIXA_PRESSAO']
    }

    print(f"📋 Contexto de teste:")
    for k, v in contexto.items():
        print(f"   {k}: {v}")

    # Teste 1: 60g (abaixo do mínimo)
    print(f"\n🔬 Teste 1: validar_capacidade(60g)")
    try:
        resultado = hotmix_1.validar_capacidade(
            quantidade=60,
            bypass=False,
            contexto_restricao=contexto
        )
        print(f"   Resultado: {resultado}")

        # Verificar se arquivo foi criado
        arquivo_restricoes = "logs/restricoes/ordem_1_restricoes.json"
        if os.path.exists(arquivo_restricoes):
            print(f"   ✅ Arquivo de restrições criado!")
            with open(arquivo_restricoes, 'r') as f:
                dados = json.load(f)
                print(f"   📊 Total restrições: {dados.get('total_restricoes', 0)}")
        else:
            print(f"   ❌ Arquivo de restrições NÃO criado!")

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    # Teste 2: 1500g (dentro da capacidade)
    print(f"\n🔬 Teste 2: validar_capacidade(1500g)")
    try:
        resultado2 = hotmix_1.validar_capacidade(
            quantidade=1500,
            bypass=False,
            contexto_restricao=contexto
        )
        print(f"   Resultado: {resultado2}")

    except Exception as e:
        print(f"   ❌ Erro: {e}")

def verificar_ocupacao_atual():
    """Verifica se existe ocupação de 60g atual"""
    print("\n🔍 VERIFICAÇÃO DA OCUPAÇÃO DE 60g")
    print("=" * 50)

    ocupacao_60g = None
    for ocupacao in hotmix_1.ocupacoes:
        if ocupacao.quantidade == 60:
            ocupacao_60g = ocupacao
            break

    if ocupacao_60g:
        print(f"✅ Encontrada ocupação de 60g:")
        print(f"   ID Item: {ocupacao_60g.id_item}")
        print(f"   ID Atividade: {ocupacao_60g.id_atividade}")
        print(f"   Quantidade: {ocupacao_60g.quantidade}g")
        print(f"   Período: {ocupacao_60g.inicio.strftime('%H:%M')} - {ocupacao_60g.fim.strftime('%H:%M')}")

        # Verificar se essa ocupação deveria ter gerado restrição
        if ocupacao_60g.quantidade < hotmix_1.capacidade_gramas_min:
            print(f"   ⚠️ Esta ocupação está ABAIXO da capacidade mínima ({hotmix_1.capacidade_gramas_min}g)")
            print(f"   ❓ Por que não foi registrada restrição?")
        else:
            print(f"   ✅ Ocupação dentro da capacidade mínima")
    else:
        print(f"❌ Nenhuma ocupação de 60g encontrada no HotMix")

def analisar_problema():
    """Analisa possíveis causas do problema"""
    print("\n🕵️ ANÁLISE DO PROBLEMA")
    print("=" * 50)

    print("Possíveis causas:")
    print("1. ❓ Bypass está sendo aplicado durante a produção")
    print("2. ❓ Contexto de restrição não está sendo passado")
    print("3. ❓ Quantidade está sendo modificada antes da validação")
    print("4. ❓ Método validar_capacidade não está sendo chamado")
    print("5. ❓ Sistema de produção usa caminho diferente")

    print("\nVerificações necessárias:")
    print("- ✅ HotMix funciona isoladamente (confirmado)")
    print("- ✅ Alocação acontece no HotMix (confirmado)")
    print("- ❓ Quantidade é realmente 60g durante validação")
    print("- ❓ Bypass não está ativo")
    print("- ❓ Contexto é passado corretamente")

def main():
    """Execução principal"""
    print("🚨 DEBUG: POR QUE RESTRIÇÕES NÃO SÃO SALVAS?")
    print("=" * 80)

    try:
        # Limpar logs de restrições
        import shutil
        if os.path.exists("logs/restricoes"):
            shutil.rmtree("logs/restricoes")
            print("🗑️ Logs de restrições limpos")

        # 1. Verificar estado do HotMix
        verificar_estado_hotmix()

        # 2. Verificar ocupação de 60g
        verificar_ocupacao_atual()

        # 3. Testar método diretamente
        verificar_metodo_validar_capacidade()

        # 4. Analisar problema
        analisar_problema()

    except Exception as e:
        print(f"\n❌ ERRO NO DEBUG: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()