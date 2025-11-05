#!/usr/bin/env python3
"""
Script de teste para o ValidadorPedidos.
Testa a validação de pedidos aprovados e cancelados.
"""

from services.validacao.validador_pedidos import ValidadorPedidos

def testar_validador():
    print("=" * 80)
    print("🧪 TESTE: ValidadorPedidos")
    print("=" * 80)
    print()

    validador = ValidadorPedidos()

    # Testar pedidos existentes
    print("🔍 TESTANDO VALIDAÇÃO DE PEDIDOS EXISTENTES:")
    print("-" * 80)
    print()

    # Teste 1: Pedido 1|1 (deve ter equipamentos e funcionários OK)
    print("📋 Teste 1: Validando Ordem 1 | Pedido 1")
    print("-" * 60)
    resultado1 = validador.validar_pedido(1, 1, cancelar_se_invalido=True)
    print(f"   Status: {resultado1['status']}")
    print(f"   Válido: {resultado1['valido']}")
    print(f"   Equipamentos OK: {resultado1['equipamentos_ok']}")
    print(f"   Funcionários OK: {resultado1['funcionarios_ok']}")
    if not resultado1['valido']:
        print(f"   Motivo: {resultado1.get('motivo_cancelamento', 'N/A')}")
    print()

    # Teste 2: Pedido 2|1 (pode existir ou não)
    print("📋 Teste 2: Validando Ordem 2 | Pedido 1")
    print("-" * 60)
    resultado2 = validador.validar_pedido(2, 1, cancelar_se_invalido=True)
    print(f"   Status: {resultado2['status']}")
    print(f"   Válido: {resultado2['valido']}")
    print(f"   Equipamentos OK: {resultado2['equipamentos_ok']}")
    print(f"   Funcionários OK: {resultado2['funcionarios_ok']}")
    if not resultado2['valido']:
        print(f"   Motivo: {resultado2.get('motivo_cancelamento', 'N/A')}")
    print()

    # Listar pedidos aprovados
    print("✅ PEDIDOS APROVADOS:")
    print("-" * 60)
    aprovados = validador.listar_pedidos_aprovados()
    if aprovados:
        for pedido in aprovados:
            print(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']}")
            print(f"     Equipamentos: {pedido['detalhes']['equipamentos']['atividades_sucesso']}/{pedido['detalhes']['equipamentos']['total_atividades']}")
            print(f"     Funcionários: {pedido['detalhes']['funcionarios']['atividades_sucesso']}/{pedido['detalhes']['funcionarios']['total_atividades']}")
            print()
    else:
        print("   Nenhum pedido aprovado")
    print()

    # Listar pedidos cancelados
    print("❌ PEDIDOS CANCELADOS:")
    print("-" * 60)
    cancelados = validador.listar_pedidos_cancelados()
    if cancelados:
        for pedido in cancelados:
            print(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']}")
            print(f"     Motivo: {pedido.get('motivo_cancelamento', 'N/A')}")
            print()
    else:
        print("   Nenhum pedido cancelado")
    print()

    # Gerar relatório completo
    print("📊 RELATÓRIO COMPLETO:")
    print("-" * 80)
    relatorio = validador.gerar_relatorio_validacao()
    print(relatorio)

    print()
    print("=" * 80)
    print("✅ Teste concluído!")
    print("=" * 80)


if __name__ == "__main__":
    testar_validador()
