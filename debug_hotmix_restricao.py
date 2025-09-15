#!/usr/bin/env python3
"""
Debug: Verificar se HotMix está registrando restrições corretamente
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from factory.fabrica_equipamentos import hotmix_1
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama

def testar_registro_restricao():
    """Testa registro de restrição direto no HotMix"""
    print("🧪 TESTE DIRETO - REGISTRO DE RESTRIÇÃO NO HOTMIX")
    print("=" * 60)

    # Limpar logs
    import shutil
    if os.path.exists("logs/restricoes"):
        shutil.rmtree("logs/restricoes")
        print("🗑️ Diretório logs/restricoes limpo")

    # Limpar ocupações
    hotmix_1.ocupacoes = []
    print("🗑️ Ocupações do HotMix limpas")

    print(f"\n📊 Configuração do HotMix:")
    print(f"   Nome: {hotmix_1.nome}")
    print(f"   Capacidade mínima: {hotmix_1.capacidade_gramas_min}g")
    print(f"   Capacidade máxima: {hotmix_1.capacidade_gramas_max}g")

    # Testar com 60g (abaixo do mínimo)
    print(f"\n🧪 Teste 1: 60g (muito abaixo do mínimo)")
    inicio = datetime(2025, 6, 26, 6, 15)
    fim = datetime(2025, 6, 26, 6, 27)

    try:
        resultado = hotmix_1.ocupar_janelas_simultaneas(
            id_ordem=1,
            id_pedido=1,
            id_atividade=20031,
            id_item=2003,
            quantidade=60,  # 60g - abaixo do mínimo
            velocidade=TipoVelocidade.BAIXA,
            chama=TipoChama.BAIXA,
            pressao_chamas=[TipoPressaoChama.BAIXA_PRESSAO],
            inicio=inicio,
            fim=fim,
            bypass_capacidade=False
        )

        print(f"📤 Resultado da alocação: {resultado}")

        if resultado:
            print(f"✅ Alocação de 60g foi aceita!")

            # Verificar se arquivo de restrições foi criado
            restricoes_path = "logs/restricoes/ordem_1_restricoes.json"
            if os.path.exists(restricoes_path):
                print(f"✅ Arquivo de restrições criado!")

                with open(restricoes_path, 'r', encoding='utf-8') as f:
                    import json
                    dados = json.load(f)
                    print(f"📋 Conteúdo:")
                    print(f"   Total restrições: {dados.get('total_restricoes', 0)}")

                    for restricao in dados.get('atividades_com_restricao', []):
                        print(f"   🔸 Atividade {restricao['id_atividade']}: {restricao['capacidade_atual']}g < {restricao['capacidade_minima']}g")
                        print(f"      Equipamento: {restricao['equipamento']}")
                        print(f"      Déficit: {restricao['diferenca']}g")
            else:
                print(f"❌ Arquivo de restrições NÃO foi criado!")
                print(f"   Caminho esperado: {restricoes_path}")

        else:
            print(f"❌ Alocação de 60g foi rejeitada!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    # Testar com quantidade dentro da capacidade
    print(f"\n🧪 Teste 2: 1500g (dentro da capacidade)")
    hotmix_1.ocupacoes = []  # Limpar

    try:
        resultado2 = hotmix_1.ocupar_janelas_simultaneas(
            id_ordem=2,
            id_pedido=2,
            id_atividade=20032,
            id_item=2004,
            quantidade=1500,  # 1500g - dentro da capacidade
            velocidade=TipoVelocidade.BAIXA,
            chama=TipoChama.BAIXA,
            pressao_chamas=[TipoPressaoChama.BAIXA_PRESSAO],
            inicio=inicio,
            fim=fim,
            bypass_capacidade=False
        )

        print(f"📤 Resultado da alocação 1500g: {resultado2}")

        if resultado2:
            print(f"✅ Alocação de 1500g foi aceita (esperado)!")
        else:
            print(f"❌ Alocação de 1500g foi rejeitada (inesperado)!")

    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    """Execução principal"""
    try:
        testar_registro_restricao()
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()