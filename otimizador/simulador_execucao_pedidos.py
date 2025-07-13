# simulador_execucao_pedidos.py
from pulp import LpProblem, LpMaximize, LpVariable, LpBinary, lpSum, LpStatus
from copy import deepcopy

def executar_simulacao(pedidos_originais, solver_funcao):
    """
    Executa a simulação dos pedidos com base no solver otimizado com PuLP.

    :param pedidos_originais: lista de objetos PedidoDeProducao prontos para execução
    :param solver_funcao: função que recebe pedidos e retorna dict {pedido_id: 0 ou 1}
    """
    # Rodar solver para decidir quais executar
    resultado = solver_funcao(pedidos_originais)

    pedidos_aceitos = []
    pedidos_descartados = []

    for pedido in pedidos_originais:
        pedido_id = pedido.pedido_id
        if resultado.get(pedido_id) == 1:
            try:
                print(f"✅ Executando pedido {pedido_id}...")
                pedido.mostrar_estrutura()
                pedido.criar_atividades_modulares_necessarias()
                pedido.executar_atividades_em_ordem()
                pedidos_aceitos.append(pedido)
            except RuntimeError as e:
                print(f"❌ Erro durante execução real do pedido {pedido_id}: {e}")
                pedidos_descartados.append(pedido)
        else:
            print(f"🚫 Pedido {pedido_id} descartado pela otimização.")
            pedidos_descartados.append(pedido)

    print(f"\n📊 Resumo:")
    print(f"  ➕ Atendidos: {[p.pedido_id for p in pedidos_aceitos]}")
    print(f"  ➖ Descartados: {[p.pedido_id for p in pedidos_descartados]}")

    return pedidos_aceitos, pedidos_descartados
