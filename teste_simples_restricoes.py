#!/usr/bin/env python3
"""
Teste Simples da Nova Lógica de Restrições
==========================================

Testa diretamente a funcionalidade de registro de restrições
usando apenas os equipamentos de forma isolada.
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from factory.fabrica_equipamentos import hotmix_1
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from utils.logs.registrador_restricoes import registrador_restricoes

def limpar_ambiente():
    """Limpa ambiente de teste"""
    print("🧹 Limpando ambiente...")

    # Limpar diretório de restrições
    import shutil
    if os.path.exists("logs/restricoes"):
        shutil.rmtree("logs/restricoes")
        print("🗑️ Diretório logs/restricoes removido")

    # Limpar ocupações do HotMix
    hotmix_1.ocupacoes = []
    print("🗑️ Ocupações do HotMix limpas")

    print("✅ Ambiente limpo!")

def testar_restricoes_hotmix():
    """Testa o registro de restrições no HotMix diretamente."""
    print("\n" + "="*80)
    print("🧪 TESTE SIMPLES: REGISTRO DE RESTRIÇÕES NO HOTMIX")
    print("="*80)

    print(f"\n📅 Configuração:")
    print(f"   HotMix 1: Capacidade mínima = {hotmix_1.capacidade_gramas_min}g")
    print(f"   HotMix 1: Capacidade máxima = {hotmix_1.capacidade_gramas_max}g")

    # Configurar janela temporal
    inicio = datetime(2025, 6, 26, 8, 0)
    fim = datetime(2025, 6, 26, 8, 15)

    print(f"\n🎯 Testando Alocações:")

    sucessos = 0
    falhas = 0

    # Teste 1: Quantidade abaixo da capacidade mínima (300g < 1000g)
    print(f"\n{'='*50}")
    print(f"🔄 Teste 1: 300g (abaixo do mínimo)")
    print(f"{'='*50}")

    try:
        resultado = hotmix_1.ocupar(
            id_ordem=1,
            id_pedido=1,
            id_atividade=20031,
            id_item=2003,
            quantidade=300,
            velocidade=TipoVelocidade.BAIXA,
            chama=TipoChama.BAIXA,
            pressao_chamas=[TipoPressaoChama.BAIXA_PRESSAO],
            inicio=inicio,
            fim=fim,
            bypass_capacidade=False
        )

        if resultado:
            sucessos += 1
            print(f"✅ Alocação 300g aceita (com possível restrição)")
        else:
            falhas += 1
            print(f"❌ Alocação 300g rejeitada")

    except Exception as e:
        falhas += 1
        print(f"❌ Erro na alocação 300g: {e}")

    # Teste 2: Quantidade abaixo da capacidade mínima (500g < 1000g)
    print(f"\n{'='*50}")
    print(f"🔄 Teste 2: 500g (abaixo do mínimo)")
    print(f"{'='*50}")

    try:
        inicio2 = datetime(2025, 6, 26, 8, 30)
        fim2 = datetime(2025, 6, 26, 8, 45)

        resultado = hotmix_1.ocupar(
            id_ordem=1,
            id_pedido=2,
            id_atividade=20032,
            id_item=2003,
            quantidade=500,
            velocidade=TipoVelocidade.BAIXA,
            chama=TipoChama.BAIXA,
            pressao_chamas=[TipoPressaoChama.BAIXA_PRESSAO],
            inicio=inicio2,
            fim=fim2,
            bypass_capacidade=False
        )

        if resultado:
            sucessos += 1
            print(f"✅ Alocação 500g aceita (com possível restrição)")
        else:
            falhas += 1
            print(f"❌ Alocação 500g rejeitada")

    except Exception as e:
        falhas += 1
        print(f"❌ Erro na alocação 500g: {e}")

    # Teste 3: Quantidade acima da capacidade mínima (1500g > 1000g)
    print(f"\n{'='*50}")
    print(f"🔄 Teste 3: 1500g (acima do mínimo)")
    print(f"{'='*50}")

    try:
        inicio3 = datetime(2025, 6, 26, 9, 0)
        fim3 = datetime(2025, 6, 26, 9, 15)

        resultado = hotmix_1.ocupar(
            id_ordem=1,
            id_pedido=3,
            id_atividade=20033,
            id_item=2003,
            quantidade=1500,
            velocidade=TipoVelocidade.BAIXA,
            chama=TipoChama.BAIXA,
            pressao_chamas=[TipoPressaoChama.BAIXA_PRESSAO],
            inicio=inicio3,
            fim=fim3,
            bypass_capacidade=False
        )

        if resultado:
            sucessos += 1
            print(f"✅ Alocação 1500g aceita (capacidade normal)")
        else:
            falhas += 1
            print(f"❌ Alocação 1500g rejeitada")

    except Exception as e:
        falhas += 1
        print(f"❌ Erro na alocação 1500g: {e}")

    return sucessos, falhas

def verificar_restricoes_registradas():
    """Verifica e exibe as restrições que foram registradas."""
    print(f"\n🔍 Verificando Restrições Registradas:")

    restricoes = registrador_restricoes.listar_todas_restricoes()

    if not restricoes:
        print(f"   📋 Nenhuma restrição encontrada")
        return 0

    total_restricoes = 0

    for restricao_arquivo in restricoes:
        ordem = restricao_arquivo.get('ordem', 'N/A')
        total = restricao_arquivo.get('total_restricoes', 0)
        total_restricoes += total

        print(f"\n   📄 Ordem {ordem}: {total} restrições registradas")

        for atividade in restricao_arquivo.get('atividades_com_restricao', []):
            print(f"      🔸 Atividade {atividade['id_atividade']} - "
                  f"{atividade['equipamento']} - "
                  f"Atual: {atividade['capacidade_atual']}g < "
                  f"Mín: {atividade['capacidade_minima']}g "
                  f"(Déficit: {atividade['diferenca']}g)")

    return total_restricoes

def main():
    """Execução principal do teste"""
    print("🧪 INICIANDO TESTE SIMPLES DA NOVA LÓGICA DE RESTRIÇÕES")
    print("="*80)

    try:
        # 1. Limpar ambiente
        limpar_ambiente()

        # 2. Executar teste
        sucessos, falhas = testar_restricoes_hotmix()

        # 3. Verificar restrições
        total_restricoes = verificar_restricoes_registradas()

        # 4. Resumo final
        print(f"\n" + "="*80)
        print(f"📋 RESUMO DO TESTE:")
        print(f"="*80)
        print(f"✅ Alocações aceitas: {sucessos}")
        print(f"❌ Alocações rejeitadas: {falhas}")
        print(f"📄 Restrições registradas: {total_restricoes}")

        if total_restricoes > 0:
            print(f"\n🎉 TESTE BEM-SUCEDIDO!")
            print(f"   Sistema registrou restrições para alocações abaixo da capacidade mínima!")
        else:
            if sucessos > 0:
                print(f"\n⚠️ TESTE PARCIALMENTE BEM-SUCEDIDO")
                print(f"   Alocações foram aceitas mas restrições não foram registradas")
            else:
                print(f"\n❌ TESTE FALHOU")
                print(f"   Nenhuma alocação foi aceita")

    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()