"""
Script de Verificação de Restauração
====================================

Compara o estado dos equipamentos na memória com o log detalhado
para verificar se a restauração foi bem-sucedida.
"""

import sys
from datetime import datetime
from factory.fabrica_equipamentos import equipamentos_disponiveis


def formatar_horario(dt):
    """Formata datetime para HH:MM"""
    return dt.strftime("%H:%M")


def contar_ocupacoes_equipamento(equipamento):
    """Conta ocupações de um equipamento baseado no seu tipo"""
    tipo = type(equipamento).__name__
    total = 0

    if hasattr(equipamento, 'ocupacoes'):
        # Bancada, Batedeira, Balança, etc
        total = len(equipamento.ocupacoes)

    elif hasattr(equipamento, 'ocupacoes_por_boca'):
        # Fogão
        for boca_ocupacoes in equipamento.ocupacoes_por_boca:
            total += len(boca_ocupacoes)

    elif hasattr(equipamento, 'niveis_ocupacoes'):
        # Câmara Refrigerada, Armário
        for nivel_ocupacoes in equipamento.niveis_ocupacoes:
            total += len(nivel_ocupacoes)

    elif hasattr(equipamento, 'caixas_ocupacoes'):
        # Freezer
        for caixa_ocupacoes in equipamento.caixas_ocupacoes:
            total += len(caixa_ocupacoes)

    elif hasattr(equipamento, 'bandejas_ocupacoes'):
        # Forno
        for bandeja_ocupacoes in equipamento.bandejas_ocupacoes:
            total += len(bandeja_ocupacoes)

    elif hasattr(equipamento, 'compartimentos_ocupacoes'):
        # Fritadeira
        for comp_ocupacoes in equipamento.compartimentos_ocupacoes:
            total += len(comp_ocupacoes)

    return total


def listar_ocupacoes_detalhadas(equipamento):
    """Lista ocupações detalhadas de um equipamento"""
    tipo = type(equipamento).__name__
    ocupacoes_info = []

    if hasattr(equipamento, 'ocupacoes'):
        # Bancada, Batedeira, Balança, etc
        for ocupacao in equipamento.ocupacoes:
            if len(ocupacao) >= 7:
                id_ordem = ocupacao[0]
                id_pedido = ocupacao[1]
                id_atividade = ocupacao[2]
                id_item = ocupacao[3]
                inicio = ocupacao[-2]
                fim = ocupacao[-1]

                ocupacoes_info.append({
                    'ordem': id_ordem,
                    'pedido': id_pedido,
                    'atividade': id_atividade,
                    'item': id_item,
                    'inicio': formatar_horario(inicio),
                    'fim': formatar_horario(fim),
                    'local': 'geral'
                })

    elif hasattr(equipamento, 'ocupacoes_por_boca'):
        # Fogão
        for boca_idx, boca_ocupacoes in enumerate(equipamento.ocupacoes_por_boca, 1):
            for ocupacao in boca_ocupacoes:
                if len(ocupacao) >= 9:
                    ocupacoes_info.append({
                        'ordem': ocupacao[0],
                        'pedido': ocupacao[1],
                        'atividade': ocupacao[2],
                        'item': ocupacao[3],
                        'inicio': formatar_horario(ocupacao[-2]),
                        'fim': formatar_horario(ocupacao[-1]),
                        'local': f'Boca {boca_idx}'
                    })

    elif hasattr(equipamento, 'niveis_ocupacoes'):
        # Câmara Refrigerada, Armário
        for nivel_idx, nivel_ocupacoes in enumerate(equipamento.niveis_ocupacoes):
            for ocupacao in nivel_ocupacoes:
                if len(ocupacao) >= 7:
                    ocupacoes_info.append({
                        'ordem': ocupacao[0],
                        'pedido': ocupacao[1],
                        'atividade': ocupacao[2],
                        'item': ocupacao[3],
                        'inicio': formatar_horario(ocupacao[-2]),
                        'fim': formatar_horario(ocupacao[-1]),
                        'local': f'Nível {nivel_idx + 1}'
                    })

    elif hasattr(equipamento, 'caixas_ocupacoes'):
        # Freezer
        for caixa_idx, caixa_ocupacoes in enumerate(equipamento.caixas_ocupacoes, 1):
            for ocupacao in caixa_ocupacoes:
                if len(ocupacao) >= 7:
                    ocupacoes_info.append({
                        'ordem': ocupacao[0],
                        'pedido': ocupacao[1],
                        'atividade': ocupacao[2],
                        'item': ocupacao[3],
                        'inicio': formatar_horario(ocupacao[-2]),
                        'fim': formatar_horario(ocupacao[-1]),
                        'local': f'Caixa {caixa_idx}'
                    })

    return ocupacoes_info


def verificar_estado_equipamentos():
    """Verifica o estado atual dos equipamentos"""
    print("=" * 80)
    print("🔍 VERIFICAÇÃO DE ESTADO DOS EQUIPAMENTOS APÓS RESTAURAÇÃO")
    print("=" * 80)
    print()

    total_equipamentos = len(equipamentos_disponiveis)
    equipamentos_com_ocupacoes = 0
    total_ocupacoes = 0

    equipamentos_detalhes = []

    for equipamento in equipamentos_disponiveis:
        nome = equipamento.nome if hasattr(equipamento, 'nome') else "Sem nome"
        tipo = type(equipamento).__name__

        num_ocupacoes = contar_ocupacoes_equipamento(equipamento)

        if num_ocupacoes > 0:
            equipamentos_com_ocupacoes += 1
            total_ocupacoes += num_ocupacoes
            equipamentos_detalhes.append((equipamento, nome, tipo, num_ocupacoes))

    # Resumo geral
    print(f"📊 RESUMO GERAL:")
    print(f"   Total de equipamentos: {total_equipamentos}")
    print(f"   Equipamentos com ocupações: {equipamentos_com_ocupacoes}")
    print(f"   Total de ocupações: {total_ocupacoes}")
    print()
    print("=" * 80)
    print()

    # Detalhes por equipamento
    if equipamentos_com_ocupacoes > 0:
        print(f"📋 EQUIPAMENTOS COM OCUPAÇÕES ({equipamentos_com_ocupacoes}):")
        print()

        for equipamento, nome, tipo, num_ocupacoes in equipamentos_detalhes:
            print(f"🔧 {nome} ({tipo})")
            print(f"   📊 Total de ocupações: {num_ocupacoes}")

            # Listar ocupações
            ocupacoes = listar_ocupacoes_detalhadas(equipamento)
            if ocupacoes:
                print(f"   📝 Ocupações:")
                for i, ocp in enumerate(ocupacoes[:5], 1):  # Mostrar até 5
                    print(f"      {i}. Ordem {ocp['ordem']} | Pedido {ocp['pedido']} | "
                          f"Atividade {ocp['atividade']} | Item {ocp['item']} | "
                          f"{ocp['inicio']} → {ocp['fim']}")
                    if ocp['local'] != 'geral':
                        print(f"         Local: {ocp['local']}")

                if len(ocupacoes) > 5:
                    print(f"      ... e mais {len(ocupacoes) - 5} ocupações")

            print()

    else:
        print("⚠️  Nenhum equipamento com ocupações encontrado na memória!")
        print()
        print("Possíveis causas:")
        print("   1. A restauração não foi aplicada (modo simulação)")
        print("   2. Os equipamentos foram resetados após a restauração")
        print("   3. Erro durante a restauração")
        print()

    print("=" * 80)

    return total_ocupacoes, equipamentos_com_ocupacoes


if __name__ == "__main__":
    try:
        total_ocp, total_equip = verificar_estado_equipamentos()

        print()
        print("💡 INTERPRETAÇÃO:")
        print()

        if total_ocp > 0:
            print(f"✅ Restauração parece ter funcionado!")
            print(f"   • {total_equip} equipamentos com ocupações restauradas")
            print(f"   • {total_ocp} ocupações totais na memória")
            print()
            print("📝 Compare esses números com o log detalhado para confirmar:")
            print("   logs/equipamentos_detalhados/ocupacoes_detalhadas_ordem_1_pedidos_1_2_20251027_195345.log")
        else:
            print("❌ Nenhuma ocupação encontrada na memória")
            print()
            print("🔄 Para aplicar a restauração:")
            print("   1. Execute o menu principal")
            print("   2. Escolha a opção 'R' (Recuperar Estado)")
            print("   3. Selecione o log desejado")
            print("   4. Responda 's' quando perguntado sobre aplicar restauração")

        print()

    except Exception as e:
        print(f"❌ Erro ao verificar estado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
