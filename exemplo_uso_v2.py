"""
Exemplo de Uso do Otimizador v2.0
==================================

Demonstra como usar o otimizador v2 de forma simples e direta.
"""

import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")


# ============================================================================
# EXEMPLO 1: Uso Ultra-Rápido (1 linha)
# ============================================================================
def exemplo_rapido():
    """Uso mais simples possível - uma única função"""
    from otimizador_v2 import executar_otimizacao_rapida

    print("EXEMPLO 1: Uso Ultra-Rápido\n")

    # Executa tudo com uma chamada
    solucao = executar_otimizacao_rapida(
        csv_path='data/csv/exemplo_pedidos.csv',
        timeout=300,
        limitar=2  # Apenas 2 primeiros pedidos
    )

    if solucao:
        print(f"\n✅ Otimização concluída!")
        print(f"   Pedidos atendidos: {solucao.pedidos_atendidos}")
        print(f"   Tempo: {solucao.tempo_resolucao:.2f}s")
    else:
        print(f"\n❌ Otimização falhou")


# ============================================================================
# EXEMPLO 2: Uso Simples com Controle
# ============================================================================
def exemplo_simples():
    """Uso simples com um pouco mais de controle"""
    from otimizador_v2 import ExecutorV2

    print("\nEXEMPLO 2: Uso Simples com Controle\n")

    # 1. Criar executor
    executor = ExecutorV2()

    # 2. Inicializar ambiente
    if not executor.inicializar():
        print("Erro na inicialização")
        return

    # 3. Otimizar
    solucao = executor.otimizar_csv(
        csv_path='data/csv/exemplo_pedidos.csv',
        timeout_segundos=300,
        limitar_pedidos=2
    )

    # 4. Mostrar resultados
    if solucao:
        pedidos = executor.adaptador.carregar_pedidos_do_csv('data/csv/exemplo_pedidos.csv')
        executor.imprimir_resumo_solucao(solucao, pedidos[:2])


# ============================================================================
# EXEMPLO 3: Uso Avançado com Comparação
# ============================================================================
def exemplo_avancado():
    """Uso avançado com comparação entre métodos"""
    from otimizador_v2 import ExecutorV2

    print("\nEXEMPLO 3: Uso Avançado com Comparação\n")

    executor = ExecutorV2()

    # Inicializar
    executor.inicializar()

    # Otimizar conjunto completo (13 pedidos)
    solucao = executor.otimizar_csv(
        csv_path='data/csv/exemplo_pedidos.csv',
        timeout_segundos=600
    )

    if solucao:
        # Carregar pedidos
        pedidos = executor.adaptador.carregar_pedidos_do_csv('data/csv/exemplo_pedidos.csv')

        # Resumo detalhado
        executor.imprimir_resumo_solucao(solucao, pedidos)

        # Comparação com métodos anteriores
        executor.comparar_com_baseline(solucao, len(pedidos))


# ============================================================================
# EXEMPLO 4: Uso Programático (sem CSV)
# ============================================================================
def exemplo_programatico():
    """Uso programático criando pedidos manualmente"""
    from datetime import datetime, timedelta
    from otimizador_v2 import ExecutorV2, AdaptadorDados, FabricaAdaptador
    from models.atividades.pedido_de_producao import PedidoDeProducao
    from enums.producao.tipo_item import TipoItem

    print("\nEXEMPLO 4: Uso Programático (sem CSV)\n")

    # 1. Criar executor
    executor = ExecutorV2()
    executor.inicializar()

    # 2. Criar pedidos manualmente
    fim = datetime(2024, 12, 31, 7, 0, 0)
    inicio = fim - timedelta(days=3)

    pedido1 = PedidoDeProducao(
        id_ordem=1,
        id_pedido=1,
        id_produto=1001,  # Pão Francês
        tipo_item=TipoItem.PRODUTO,
        quantidade=100,
        inicio_jornada=inicio,
        fim_jornada=fim,
        gestor_almoxarifado=executor.configurador.gestor_almoxarifado
    )
    pedido1.montar_estrutura()
    pedido1.criar_atividades_modulares_necessarias()

    pedidos = [pedido1]

    # 3. Otimizar
    solucao = executor.otimizar_pedidos(
        pedidos=pedidos,
        timeout_segundos=180
    )

    # 4. Resultados
    if solucao:
        print(f"\n✅ Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    print("="*80)
    print("EXEMPLOS DE USO DO OTIMIZADOR v2.0")
    print("="*80)

    # Escolha qual exemplo rodar:

    # Descomente o exemplo que deseja executar:

    exemplo_rapido()        # Mais simples
    # exemplo_simples()       # Simples com controle
    # exemplo_avancado()      # Com comparação
    # exemplo_programatico()  # Programático

    print("\n" + "="*80)
