#!/usr/bin/env python3
"""
Teste específico para 60g no HotMix
==================================

Verifica se a atividade de 60g (massa para frituras) consegue ser alocada
diretamente no HotMix com a nova lógica de restrições.
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

def testar_60g_massa_frituras():
    """Testa especificamente 60g de massa para frituras."""
    print("\n" + "="*80)
    print("🧪 TESTE ESPECÍFICO: 60g MASSA PARA FRITURAS NO HOTMIX")
    print("="*80)

    print(f"\n📅 Configuração:")
    print(f"   HotMix 1: Capacidade mínima = {hotmix_1.capacidade_gramas_min}g")
    print(f"   HotMix 1: Capacidade máxima = {hotmix_1.capacidade_gramas_max}g")
    print(f"   Teste: 60g (muito abaixo do mínimo)")

    # Configurar janela temporal idêntica ao sistema de produção
    inicio = datetime(2025, 6, 26, 6, 15)
    fim = datetime(2025, 6, 26, 6, 27)

    print(f"   Período: {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}")

    try:
        resultado = hotmix_1.ocupar_janelas_simultaneas(
            id_ordem=1,
            id_pedido=1,
            id_atividade=20031,
            id_item=2003,
            quantidade=60,  # 60g como no sistema de produção
            velocidade=TipoVelocidade.BAIXA,
            chama=TipoChama.BAIXA,
            pressao_chamas=[TipoPressaoChama.BAIXA_PRESSAO],
            inicio=inicio,
            fim=fim,
            bypass_capacidade=False
        )

        if resultado:
            print(f"✅ Alocação 60g aceita!")
            print(f"   Status: Com restrição registrada")

            # Verificar se restrição foi registrada
            restricoes = registrador_restricoes.obter_restricoes_ordem(1)
            if restricoes.get('total_restricoes', 0) > 0:
                print(f"   📄 Restrições registradas: {restricoes['total_restricoes']}")
                for r in restricoes.get('atividades_com_restricao', []):
                    if r['id_atividade'] == 20031:
                        print(f"      🔸 Atividade 20031: {r['capacidade_atual']}g < {r['capacidade_minima']}g")
                        print(f"      🔸 Déficit: {r['diferenca']}g")
            else:
                print(f"   ⚠️ Nenhuma restrição registrada (inesperado)")

            return True
        else:
            print(f"❌ Alocação 60g rejeitada")
            return False

    except Exception as e:
        print(f"❌ Erro na alocação 60g: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Execução principal do teste"""
    print("🧪 TESTE ESPECÍFICO: 60g NO HOTMIX")
    print("="*80)

    try:
        # 1. Limpar ambiente
        limpar_ambiente()

        # 2. Executar teste
        sucesso = testar_60g_massa_frituras()

        # 3. Resultado
        print(f"\n" + "="*80)
        print(f"📋 RESULTADO:")
        print(f"="*80)

        if sucesso:
            print(f"🎉 SUCESSO! HotMix aceita 60g com restrição registrada")
            print(f"   O problema no sistema de produção não está no HotMix")
            print(f"   O problema deve estar no gestor de misturadoras")
        else:
            print(f"❌ FALHA! HotMix rejeitou 60g")
            print(f"   A nova lógica de restrições não está funcionando")

    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()