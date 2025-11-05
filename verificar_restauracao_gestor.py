"""
Script de Verificação de Restauração via Gestor
===============================================

Compara o estado dos equipamentos via GestorProducao (mesma estrutura do menu)
com o log detalhado para verificar se a restauração foi bem-sucedida.
"""

import sys
from datetime import datetime


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


def obter_todos_equipamentos_gestor(gestor_producao):
    """Coleta todos os equipamentos dos gestores"""
    equipamentos = []

    # Obter referência ao gestor_equipamentos
    gestor_equipamentos = gestor_producao.gestor_equipamentos

    # Coletar de todos os gestores específicos
    gestores = [
        ('Bancadas', gestor_equipamentos.gestor_bancadas.bancadas),
        ('Balanças', gestor_equipamentos.gestor_balancas.balancas),
        ('Batedeiras', gestor_equipamentos.gestor_batedeiras.batedeiras),
        ('Câmaras Refrigeradas', gestor_equipamentos.gestor_refrigeracao_congelamento.camaras_refrigeradas),
        ('Freezers', gestor_equipamentos.gestor_refrigeracao_congelamento.freezers),
        ('Armários Fermentadores', gestor_equipamentos.gestor_armarios_para_fermentacao.armarios_fermentadores),
        ('Armários Esqueleto', gestor_equipamentos.gestor_armarios_para_fermentacao.armarios_esqueleto),
        ('Masseiras', gestor_equipamentos.gestor_misturadoras.masseiras),
        ('Divisoras', gestor_equipamentos.gestor_divisoras_boleadoras.divisoras),
        ('Fogões', gestor_equipamentos.gestor_fogoes.fogoes),
        ('Fornos', gestor_equipamentos.gestor_fornos.fornos),
        ('Fritadeiras', gestor_equipamentos.gestor_fritadeiras.fritadeiras),
        ('Modeladoras de Pães', gestor_equipamentos.gestor_modeladoras.modeladoras_de_paes),
        ('Modeladoras de Salgados', gestor_equipamentos.gestor_modeladoras.modeladoras_de_salgados),
        ('Hot Mix', gestor_equipamentos.gestor_misturadoras_com_coccao.hot_mix),
        ('Embaladoras', gestor_equipamentos.gestor_embaladoras.embaladoras),
    ]

    for categoria, lista_equipamentos in gestores:
        for equipamento in lista_equipamentos:
            equipamentos.append((categoria, equipamento))

    return equipamentos


def verificar_estado_equipamentos_gestor():
    """Verifica o estado atual dos equipamentos via GestorProducao"""
    print("=" * 80)
    print("🔍 VERIFICAÇÃO DE ESTADO DOS EQUIPAMENTOS VIA GESTOR DE PRODUÇÃO")
    print("=" * 80)
    print()

    # Inicializar gestor de produção
    print("⏳ Inicializando Gestor de Produção...")
    from services.gestores.producao.gestor_producao import GestorProducao
    gestor_producao = GestorProducao()
    print("✅ Gestor inicializado\n")

    # Coletar todos os equipamentos
    print("⏳ Coletando equipamentos dos gestores...")
    equipamentos_lista = obter_todos_equipamentos_gestor(gestor_producao)
    print(f"✅ {len(equipamentos_lista)} equipamentos encontrados\n")

    equipamentos_com_ocupacoes = 0
    total_ocupacoes = 0
    equipamentos_detalhes = []

    for categoria, equipamento in equipamentos_lista:
        nome = equipamento.nome if hasattr(equipamento, 'nome') else "Sem nome"
        tipo = type(equipamento).__name__

        num_ocupacoes = contar_ocupacoes_equipamento(equipamento)

        if num_ocupacoes > 0:
            equipamentos_com_ocupacoes += 1
            total_ocupacoes += num_ocupacoes
            equipamentos_detalhes.append((categoria, equipamento, nome, tipo, num_ocupacoes))

    # Resumo geral
    print("=" * 80)
    print(f"📊 RESUMO GERAL:")
    print(f"   Total de equipamentos: {len(equipamentos_lista)}")
    print(f"   Equipamentos com ocupações: {equipamentos_com_ocupacoes}")
    print(f"   Total de ocupações: {total_ocupacoes}")
    print("=" * 80)
    print()

    # Detalhes por equipamento
    if equipamentos_com_ocupacoes > 0:
        print(f"📋 EQUIPAMENTOS COM OCUPAÇÕES ({equipamentos_com_ocupacoes}):")
        print()

        for categoria, equipamento, nome, tipo, num_ocupacoes in equipamentos_detalhes:
            print(f"🔧 {nome} ({tipo}) - [{categoria}]")
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
        print("⚠️  Nenhum equipamento com ocupações encontrado!")
        print()
        print("📝 Isso indica que:")
        print("   • A restauração não foi aplicada ainda, OU")
        print("   • Foi usada apenas a simulação (modo dry-run)")
        print()

    print("=" * 80)

    return total_ocupacoes, equipamentos_com_ocupacoes


if __name__ == "__main__":
    try:
        total_ocp, total_equip = verificar_estado_equipamentos_gestor()

        print()
        print("💡 INTERPRETAÇÃO:")
        print()

        if total_ocp > 0:
            print(f"✅ Restauração CONFIRMADA!")
            print(f"   • {total_equip} equipamentos com ocupações restauradas")
            print(f"   • {total_ocp} ocupações totais na memória")
            print()
            print("📝 Comparação com log:")
            print("   Log esperado: 36 ocupações em 13 equipamentos")
            print(f"   Estado atual: {total_ocp} ocupações em {total_equip} equipamentos")
            print()

            if total_ocp == 36 and total_equip >= 13:
                print("🎉 SUCESSO COMPLETO! Os números batem com o log!")
            elif total_ocp == 36:
                print("✅ Número de ocupações correto!")
                print("⚠️  Diferença no número de equipamentos (pode ser variação normal)")
            else:
                print("⚠️  Números diferentes do log - verificar possíveis perdas")

        else:
            print("❌ Nenhuma ocupação encontrada na memória")
            print()
            print("🔄 Para aplicar a restauração:")
            print("   1. Execute o menu principal: python3 menu/main_menu.py")
            print("   2. Escolha a opção 'R' (Recuperar Estado)")
            print("   3. Selecione o log desejado")
            print("   4. Responda 's' quando perguntado sobre aplicar restauração")

        print()

    except Exception as e:
        print(f"❌ Erro ao verificar estado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
