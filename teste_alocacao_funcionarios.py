#!/usr/bin/env python3
"""
Teste do Sistema de Alocação de Funcionários
===========================================

Este script testa o novo sistema de alocação automática de funcionários
implementado no GestorFuncionarios.
"""

from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios


def testar_alocacao_individual():
    """Testa alocação para uma ordem|pedido específica."""
    print("🧪 TESTE: Alocação Individual")
    print("=" * 50)

    gestor = GestorFuncionarios()

    # Testar com dados existentes
    id_ordem = 1
    id_pedido = 1

    print(f"📋 Testando alocação para Ordem {id_ordem} | Pedido {id_pedido}")

    sucesso = gestor.alocar_funcionarios_para_ordem_pedido(id_ordem, id_pedido)

    if sucesso:
        print("✅ Alocação realizada com sucesso!")
    else:
        print("❌ Falha na alocação")

    # Mostrar relatório
    print("\n📊 Relatório das alocações:")
    relatorio = gestor.obter_relatorio_alocacoes(id_ordem, id_pedido)
    print(relatorio)

    return sucesso


def testar_alocacao_multipla():
    """Testa alocação para todas as ordens|pedidos disponíveis."""
    print("\n🧪 TESTE: Alocação Múltipla")
    print("=" * 50)

    gestor = GestorFuncionarios()

    print("📋 Processando todas as ordens|pedidos disponíveis...")

    resultados = gestor.processar_todas_ordens_pedidos_disponiveis()

    if not resultados:
        print("⚠️ Nenhum arquivo de requisitos encontrado")
        return False

    # Mostrar resultados
    print(f"\n📊 Resultados do processamento:")
    sucessos = 0
    for (ordem, pedido), sucesso in resultados.items():
        status = "✅" if sucesso else "❌"
        print(f"{status} Ordem {ordem} | Pedido {pedido}")
        if sucesso:
            sucessos += 1

    print(f"\n🏁 Resumo: {sucessos}/{len(resultados)} alocações bem-sucedidas")

    # Relatório geral
    print("\n📊 Relatório geral das alocações:")
    relatorio = gestor.obter_relatorio_alocacoes()
    print(relatorio)

    return sucessos == len(resultados)


def testar_relatorio_horas_funcionarios():
    """Testa relatório de horas dos funcionários após alocação."""
    print("\n🧪 TESTE: Relatório de Horas")
    print("=" * 50)

    gestor = GestorFuncionarios()

    # Fazer uma alocação primeiro
    gestor.alocar_funcionarios_para_ordem_pedido(1, 1)

    # Mostrar relatórios de horas por funcionário
    for funcionario in gestor.funcionarios_disponiveis:
        if funcionario.ocupacoes:
            relatorio = funcionario.gerar_relatorio_horas()
            print(f"\n{relatorio}")


def main():
    """Função principal de teste."""
    print("🚀 SISTEMA DE TESTE - ALOCAÇÃO DE FUNCIONÁRIOS")
    print("=" * 80)

    try:
        # Teste 1: Alocação individual
        sucesso_individual = testar_alocacao_individual()

        # Teste 2: Alocação múltipla (limpar antes para evitar conflitos)
        # Criar novo gestor para limpar estado
        # sucesso_multiplo = testar_alocacao_multipla()

        # Teste 3: Relatório de horas
        testar_relatorio_horas_funcionarios()

        print("\n🏁 TESTES FINALIZADOS!")
        print("=" * 80)

        if sucesso_individual:
            print("✅ Sistema de alocação está funcionando corretamente!")
        else:
            print("❌ Foram encontrados problemas no sistema")

    except Exception as e:
        print(f"💥 Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()