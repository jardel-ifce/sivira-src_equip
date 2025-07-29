# simulador_execucao_pedidos.py
from pulp import LpProblem, LpMaximize, LpVariable, LpBinary, lpSum, LpStatus
from copy import deepcopy

def executar_simulacao(pedidos_originais, solver_funcao):
    """
    Executa a simulação dos pedidos com base no solver otimizado com PuLP.

    :param pedidos_originais: lista de objetos PedidoDeProducao prontos para execução
    :param solver_funcao: função que recebe pedidos e retorna dict {id_pedido: 0 ou 1}
    """
    # Rodar solver para decidir quais executar
    resultado = solver_funcao(pedidos_originais)

    pedidos_aceitos = []
    pedidos_descartados = []

    for pedido in pedidos_originais:
        id_pedido = pedido.id_pedido
        if resultado.get(id_pedido) == 1:
            try:
                print(f"✅ Executando pedido {id_pedido}...")
                pedido.mostrar_estrutura()
                pedido.criar_atividades_modulares_necessarias()
                pedido.executar_atividades_em_ordem()
                pedidos_aceitos.append(pedido)
            except RuntimeError as e:
                print(f"❌ Erro durante execução real do pedido {id_pedido}: {e}")
                pedidos_descartados.append(pedido)
        else:
            print(f"🚫 Pedido {id_pedido} descartado pela otimização.")
            pedidos_descartados.append(pedido)

    print(f"\n📊 Resumo:")
    print(f"  ➕ Atendidos: {[p.id_pedido for p in pedidos_aceitos]}")
    print(f"  ➖ Descartados: {[p.id_pedido for p in pedidos_descartados]}")

    return pedidos_aceitos, pedidos_descartados
