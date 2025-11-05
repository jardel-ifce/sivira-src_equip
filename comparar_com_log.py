"""
Comparador: Estado em Memória vs Log Detalhado
==============================================

Executa uma restauração e compara o resultado com o log original.
"""

import sys
from datetime import datetime
from utils.recuperacao.recuperador_estado import RecuperadorEstado
from factory.fabrica_equipamentos import equipamentos_disponiveis


def formatar_horario(dt):
    """Formata datetime para HH:MM"""
    return dt.strftime("%H:%M")


def contar_ocupacoes_equipamento(equipamento):
    """Conta ocupações de um equipamento baseado no seu tipo"""
    total = 0

    if hasattr(equipamento, 'fracoes_ocupacoes'):
        # Bancada
        for fracao_ocupacoes in equipamento.fracoes_ocupacoes:
            total += len(fracao_ocupacoes)
    elif hasattr(equipamento, 'ocupacoes'):
        total = len(equipamento.ocupacoes)
    elif hasattr(equipamento, 'ocupacoes_por_boca'):
        for boca_ocupacoes in equipamento.ocupacoes_por_boca:
            total += len(boca_ocupacoes)
    elif hasattr(equipamento, 'niveis_ocupacoes'):
        for nivel_ocupacoes in equipamento.niveis_ocupacoes:
            total += len(nivel_ocupacoes)
        # CamaraRefrigerada pode ter AMBOS niveis E caixas
        if hasattr(equipamento, 'caixas_ocupacoes'):
            for caixa_ocupacoes in equipamento.caixas_ocupacoes:
                total += len(caixa_ocupacoes)
    elif hasattr(equipamento, 'caixas_ocupacoes'):
        for caixa_ocupacoes in equipamento.caixas_ocupacoes:
            total += len(caixa_ocupacoes)
    elif hasattr(equipamento, 'bandejas_ocupacoes'):
        for bandeja_ocupacoes in equipamento.bandejas_ocupacoes:
            total += len(bandeja_ocupacoes)
    elif hasattr(equipamento, 'compartimentos_ocupacoes'):
        for comp_ocupacoes in equipamento.compartimentos_ocupacoes:
            total += len(comp_ocupacoes)

    return total


def listar_ocupacoes_simples(equipamento):
    """Lista ocupações de forma simplificada"""
    ocupacoes = []

    if hasattr(equipamento, 'fracoes_ocupacoes'):
        # Bancada
        for fracao_ocupacoes in equipamento.fracoes_ocupacoes:
            for ocupacao in fracao_ocupacoes:
                if len(ocupacao) >= 7:
                    ocupacoes.append({
                        'ordem': ocupacao[0],
                        'pedido': ocupacao[1],
                        'atividade': ocupacao[2],
                        'item': ocupacao[3],
                        'inicio': formatar_horario(ocupacao[-2]),
                        'fim': formatar_horario(ocupacao[-1])
                    })

    elif hasattr(equipamento, 'ocupacoes'):
        for ocupacao in equipamento.ocupacoes:
            if len(ocupacao) >= 7:
                ocupacoes.append({
                    'ordem': ocupacao[0],
                    'pedido': ocupacao[1],
                    'atividade': ocupacao[2],
                    'item': ocupacao[3],
                    'inicio': formatar_horario(ocupacao[-2]),
                    'fim': formatar_horario(ocupacao[-1])
                })

    elif hasattr(equipamento, 'ocupacoes_por_boca'):
        for boca_ocupacoes in equipamento.ocupacoes_por_boca:
            for ocupacao in boca_ocupacoes:
                if len(ocupacao) >= 9:
                    ocupacoes.append({
                        'ordem': ocupacao[0],
                        'pedido': ocupacao[1],
                        'atividade': ocupacao[2],
                        'item': ocupacao[3],
                        'inicio': formatar_horario(ocupacao[-2]),
                        'fim': formatar_horario(ocupacao[-1])
                    })

    elif hasattr(equipamento, 'niveis_ocupacoes'):
        for nivel_ocupacoes in equipamento.niveis_ocupacoes:
            for ocupacao in nivel_ocupacoes:
                if len(ocupacao) >= 7:
                    ocupacoes.append({
                        'ordem': ocupacao[0],
                        'pedido': ocupacao[1],
                        'atividade': ocupacao[2],
                        'item': ocupacao[3],
                        'inicio': formatar_horario(ocupacao[-2]),
                        'fim': formatar_horario(ocupacao[-1])
                    })
        # CamaraRefrigerada pode ter AMBOS niveis E caixas
        if hasattr(equipamento, 'caixas_ocupacoes'):
            for caixa_ocupacoes in equipamento.caixas_ocupacoes:
                for ocupacao in caixa_ocupacoes:
                    if len(ocupacao) >= 7:
                        ocupacoes.append({
                            'ordem': ocupacao[0],
                            'pedido': ocupacao[1],
                            'atividade': ocupacao[2],
                            'item': ocupacao[3],
                            'inicio': formatar_horario(ocupacao[-2]),
                            'fim': formatar_horario(ocupacao[-1])
                        })

    elif hasattr(equipamento, 'caixas_ocupacoes'):
        for caixa_ocupacoes in equipamento.caixas_ocupacoes:
            for ocupacao in caixa_ocupacoes:
                if len(ocupacao) >= 7:
                    ocupacoes.append({
                        'ordem': ocupacao[0],
                        'pedido': ocupacao[1],
                        'atividade': ocupacao[2],
                        'item': ocupacao[3],
                        'inicio': formatar_horario(ocupacao[-2]),
                        'fim': formatar_horario(ocupacao[-1])
                    })

    return ocupacoes


def comparar_com_log():
    """Executa restauração e compara com log"""
    print("=" * 80)
    print("🔍 COMPARAÇÃO: ESTADO RESTAURADO vs LOG DETALHADO")
    print("=" * 80)
    print()

    # 1. Executar restauração
    print("⏳ FASE 1: Executando restauração do log...")
    print()

    caminho_log = "logs/equipamentos_detalhados/ocupacoes_detalhadas_ordem_1_pedidos_1_2_20251027_195345.log"

    recuperador = RecuperadorEstado()
    relatorio = recuperador.recuperar_de_log(
        caminho_log,
        aplicar_restauracao=True  # APLICAR RESTAURAÇÃO
    )

    print(f"✅ Restauração concluída!")
    print(f"   • {relatorio.total_ocupacoes_recuperadas} ocupações recuperadas")
    print(f"   • {relatorio.equipamentos_restaurados}/{relatorio.total_equipamentos} equipamentos restaurados")
    print()

    if relatorio.tem_erros:
        print(f"⚠️  {relatorio.total_erros} erros encontrados")
        if relatorio.erros_globais:
            for erro in relatorio.erros_globais[:3]:
                print(f"   • {erro}")
        print()

    # 2. Verificar estado em memória
    print("=" * 80)
    print("⏳ FASE 2: Verificando estado dos equipamentos em memória...")
    print()

    total_equipamentos = len(equipamentos_disponiveis)
    equipamentos_com_ocupacoes = 0
    total_ocupacoes_memoria = 0

    equipamentos_detalhes = []

    for equipamento in equipamentos_disponiveis:
        nome = equipamento.nome if hasattr(equipamento, 'nome') else "Sem nome"
        tipo = type(equipamento).__name__

        num_ocupacoes = contar_ocupacoes_equipamento(equipamento)

        if num_ocupacoes > 0:
            equipamentos_com_ocupacoes += 1
            total_ocupacoes_memoria += num_ocupacoes
            equipamentos_detalhes.append((equipamento, nome, tipo, num_ocupacoes))

    print(f"✅ Estado verificado!")
    print(f"   • {total_equipamentos} equipamentos totais")
    print(f"   • {equipamentos_com_ocupacoes} com ocupações")
    print(f"   • {total_ocupacoes_memoria} ocupações em memória")
    print()

    # 3. Comparação
    print("=" * 80)
    print("📊 FASE 3: COMPARAÇÃO DOS RESULTADOS")
    print("=" * 80)
    print()

    print(f"📋 COMPARAÇÃO GERAL:")
    print(f"{'Métrica':<40} | {'Log':>10} | {'Memória':>10} | {'Status':>10}")
    print("-" * 80)

    # Ocupações totais
    match_ocupacoes = "✅ OK" if total_ocupacoes_memoria == relatorio.total_ocupacoes_recuperadas else "❌ DIFF"
    print(f"{'Ocupações totais':<40} | {relatorio.total_ocupacoes_recuperadas:>10} | {total_ocupacoes_memoria:>10} | {match_ocupacoes:>10}")

    # Equipamentos
    match_equipamentos = "✅ OK" if equipamentos_com_ocupacoes == relatorio.equipamentos_restaurados else "❌ DIFF"
    print(f"{'Equipamentos com ocupações':<40} | {relatorio.equipamentos_restaurados:>10} | {equipamentos_com_ocupacoes:>10} | {match_equipamentos:>10}")

    print()

    # 4. Detalhamento por equipamento
    if equipamentos_com_ocupacoes > 0:
        print("=" * 80)
        print(f"📋 DETALHAMENTO POR EQUIPAMENTO ({equipamentos_com_ocupacoes} equipamentos):")
        print("=" * 80)
        print()

        for equipamento, nome, tipo, num_ocupacoes in equipamentos_detalhes:
            print(f"🔧 {nome} ({tipo})")
            print(f"   📊 {num_ocupacoes} ocupações")

            # Mostrar primeiras ocupações
            ocupacoes = listar_ocupacoes_simples(equipamento)
            if ocupacoes:
                for i, ocp in enumerate(ocupacoes[:3], 1):
                    print(f"      {i}. Ordem {ocp['ordem']} | Pedido {ocp['pedido']} | "
                          f"Atividade {ocp['atividade']} | Item {ocp['item']} | "
                          f"{ocp['inicio']} → {ocp['fim']}")

                if len(ocupacoes) > 3:
                    print(f"      ... e mais {len(ocupacoes) - 3} ocupações")

            print()

    # 5. Conclusão
    print("=" * 80)
    print("💡 CONCLUSÃO:")
    print("=" * 80)
    print()

    if total_ocupacoes_memoria == relatorio.total_ocupacoes_recuperadas:
        print("🎉 SUCESSO COMPLETO!")
        print()
        print(f"   ✅ Todas as {total_ocupacoes_memoria} ocupações foram restauradas corretamente")
        print(f"   ✅ {equipamentos_com_ocupacoes} equipamentos têm ocupações em memória")
        print()
        print("   📝 A restauração funcionou perfeitamente!")
        print("   📝 Os dados do log foram aplicados aos equipamentos na memória")
        print()

    elif total_ocupacoes_memoria > 0:
        print("⚠️  SUCESSO PARCIAL")
        print()
        print(f"   • {total_ocupacoes_memoria} ocupações em memória (esperado: {relatorio.total_ocupacoes_recuperadas})")
        print(f"   • Diferença: {abs(total_ocupacoes_memoria - relatorio.total_ocupacoes_recuperadas)} ocupações")
        print()

        if total_ocupacoes_memoria < relatorio.total_ocupacoes_recuperadas:
            print("   ⚠️  Algumas ocupações não foram restauradas")
        else:
            print("   ⚠️  Mais ocupações em memória do que no log")

    else:
        print("❌ FALHA NA RESTAURAÇÃO")
        print()
        print("   • Nenhuma ocupação encontrada em memória")
        print("   • A restauração não foi aplicada ou houve erro crítico")
        print()

    print("=" * 80)


if __name__ == "__main__":
    try:
        comparar_com_log()
    except Exception as e:
        print(f"❌ Erro ao executar comparação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
