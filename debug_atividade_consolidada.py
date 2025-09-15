#!/usr/bin/env python3
"""
Script de debug para verificar o estado de atividades consolidadas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from enums.producao.tipo_item import TipoItem
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.atividades.agrupador_subprodutos import AgrupadorSubprodutos
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado

def debug_atividades_consolidadas():
    """Debug das atividades consolidadas"""

    print("=" * 80)
    print("DEBUG: INVESTIGAÇÃO DE ATIVIDADES CONSOLIDADAS")
    print("=" * 80)

    try:
        # Carregar almoxarifado
        print("🔄 Carregando almoxarifado...")
        from parser.parser_almoxarifado import carregar_itens_almoxarifado
        from models.almoxarifado.almoxarifado import Almoxarifado
        itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
        almoxarifado = Almoxarifado()
        for item in itens:
            almoxarifado.adicionar_item(item)
        gestor_almoxarifado = GestorAlmoxarifado(almoxarifado)

        # Criar pedidos similares ao log
        inicio_base = datetime(2025, 6, 23, 8, 0, 0)
        fim_base = datetime(2025, 6, 26, 8, 0, 0)

        print("\n📋 Criando pedidos...")

        # Pedido 1: Coxinha de Frango
        pedido1 = PedidoDeProducao(
            id_ordem=1,
            id_pedido=1,
            id_produto=1055,  # Coxinha de Frango
            tipo_item=TipoItem.PRODUTO,
            quantidade=15,
            inicio_jornada=inicio_base,
            fim_jornada=fim_base,
            gestor_almoxarifado=gestor_almoxarifado
        )

        # Pedido 2: Coxinha de Carne de Sol
        pedido2 = PedidoDeProducao(
            id_ordem=1,
            id_pedido=2,
            id_produto=1069,  # Coxinha de Carne de Sol
            tipo_item=TipoItem.PRODUTO,
            quantidade=10,
            inicio_jornada=inicio_base,
            fim_jornada=fim_base,
            gestor_almoxarifado=gestor_almoxarifado
        )

        print("\n🔧 Montando estruturas...")
        pedido1.montar_estrutura()
        pedido1.criar_atividades_modulares_necessarias()

        pedido2.montar_estrutura()
        pedido2.criar_atividades_modulares_necessarias()

        print(f"\n📊 Estado inicial:")
        print(f"   Pedido 1: {len(pedido1.atividades_modulares)} atividades")
        for i, ativ in enumerate(pedido1.atividades_modulares):
            print(f"     {i+1}. ID {ativ.id_atividade}: {ativ.nome_item} ({ativ.quantidade}g) - {ativ.tipo_item.name}")

        print(f"   Pedido 2: {len(pedido2.atividades_modulares)} atividades")
        for i, ativ in enumerate(pedido2.atividades_modulares):
            print(f"     {i+1}. ID {ativ.id_atividade}: {ativ.nome_item} ({ativ.quantidade}g) - {ativ.tipo_item.name}")

        # Localizar atividades massa_para_frituras (ID 20031)
        massa_p1 = [a for a in pedido1.atividades_modulares if a.id_atividade == 20031]
        massa_p2 = [a for a in pedido2.atividades_modulares if a.id_atividade == 20031]

        print(f"\n🔍 Atividades 20031 (massa_para_frituras):")
        print(f"   Pedido 1: {len(massa_p1)} atividade(s)")
        if massa_p1:
            print(f"     - Quantidade: {massa_p1[0].quantidade}g")
            print(f"     - Nome: {massa_p1[0].nome_item}")

        print(f"   Pedido 2: {len(massa_p2)} atividade(s)")
        if massa_p2:
            print(f"     - Quantidade: {massa_p2[0].quantidade}g")
            print(f"     - Nome: {massa_p2[0].nome_item}")

        print("\n🔄 Executando consolidação...")
        agrupador = AgrupadorSubprodutos(tolerancia_temporal=timedelta(minutes=30))
        resultado = agrupador.executar_agrupamento_automatico([pedido1, pedido2])

        print(f"\n📊 Resultado da consolidação:")
        print(f"   Consolidações: {resultado.get('consolidacoes_realizadas', 0)}")
        if resultado.get('consolidacoes_realizadas', 0) > 0:
            print(f"   Economia: {resultado.get('economia_equipamentos', 0)} equipamentos")
            print(f"   Pedidos afetados: {resultado.get('pedidos_afetados', [])}")

        print(f"\n📊 Estado pós-consolidação:")
        print(f"   Pedido 1: {len(pedido1.atividades_modulares)} atividades")
        for i, ativ in enumerate(pedido1.atividades_modulares):
            consolidada = getattr(ativ, '_is_consolidated', False)
            print(f"     {i+1}. ID {ativ.id_atividade}: {ativ.nome_item} ({ativ.quantidade}g) - {ativ.tipo_item.name} {'[CONSOLIDADA]' if consolidada else ''}")

        print(f"   Pedido 2: {len(pedido2.atividades_modulares)} atividades")
        for i, ativ in enumerate(pedido2.atividades_modulares):
            consolidada = getattr(ativ, '_is_consolidated', False)
            print(f"     {i+1}. ID {ativ.id_atividade}: {ativ.nome_item} ({ativ.quantidade}g) - {ativ.tipo_item.name} {'[CONSOLIDADA]' if consolidada else ''}")

        # Verificar se atividade 20031 ainda existe
        massa_p1_pos = [a for a in pedido1.atividades_modulares if a.id_atividade == 20031]
        massa_p2_pos = [a for a in pedido2.atividades_modulares if a.id_atividade == 20031]

        print(f"\n🔍 Atividades 20031 pós-consolidação:")
        print(f"   Pedido 1: {len(massa_p1_pos)} atividade(s)")
        if massa_p1_pos:
            ativ = massa_p1_pos[0]
            print(f"     - Quantidade: {ativ.quantidade}g")
            print(f"     - Nome: {ativ.nome_item}")
            print(f"     - Consolidada: {getattr(ativ, '_is_consolidated', False)}")
            print(f"     - Tem configuracoes_equipamentos: {hasattr(ativ, 'configuracoes_equipamentos')}")
            print(f"     - Tem dados_atividade: {hasattr(ativ, 'dados_atividade')}")
            print(f"     - Tem duracao: {hasattr(ativ, 'duracao')}")

        print(f"   Pedido 2: {len(massa_p2_pos)} atividade(s)")
        if massa_p2_pos:
            print(f"     - Quantidade: {massa_p2_pos[0].quantidade}g")
            print(f"     - Nome: {massa_p2_pos[0].nome_item}")

        print("\n🧪 Testando agrupamento de subprodutos para execução...")
        if massa_p1_pos:
            atividades_subproduto = [
                a for a in pedido1.atividades_modulares
                if a.tipo_item == TipoItem.SUBPRODUTO
            ]

            print(f"   Subprodutos no pedido 1: {len(atividades_subproduto)}")
            for ativ in atividades_subproduto:
                print(f"     - ID {ativ.id_atividade}: {ativ.nome_item}")

            # Teste do agrupamento por dependência
            grupos = pedido1._agrupar_subprodutos_por_dependencia(atividades_subproduto)
            print(f"   Grupos de execução: {len(grupos)}")
            for nome_grupo, atividades_grupo in grupos.items():
                print(f"     Grupo '{nome_grupo}': {len(atividades_grupo)} atividades")
                for ativ in atividades_grupo:
                    consolidada = getattr(ativ, '_is_consolidated', False)
                    print(f"       - ID {ativ.id_atividade}: {ativ.quantidade}g {'[CONSOLIDADA]' if consolidada else ''}")

        return pedido1, pedido2, resultado

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

if __name__ == "__main__":
    pedido1, pedido2, resultado = debug_atividades_consolidadas()