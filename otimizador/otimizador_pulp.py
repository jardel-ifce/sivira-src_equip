from pulp import LpProblem, LpVariable, LpMaximize, LpBinary, LpStatus, value
from typing import List
from copy import deepcopy
from models.atividades.pedido_de_producao import PedidoDeProducao

def otimizar_pedidos_com_pulp(pedidos: List[PedidoDeProducao]):
    print("\n🔍 Iniciando otimização com Programação Linear...")

    problema = LpProblem("Maximizacao_Pedidos", LpMaximize)

    variaveis = {
        pedido.pedido_id: LpVariable(f"x_{pedido.pedido_id}", cat=LpBinary)
        for pedido in pedidos
    }

    problema += sum(variaveis.values()), "Maximizar_Pedidos_Atendidos"

    for pedido in pedidos:
        copia = deepcopy(pedido)
        try:
            copia.montar_estrutura()
            copia.criar_atividades_modulares_necessarias()
            copia.executar_atividades_em_ordem()
        except Exception as e:
            problema += variaveis[pedido.pedido_id] == 0, f"Restricao_Falha_{pedido.pedido_id}"
            print(f"❌ Pedido {pedido.pedido_id} não viável isoladamente: {e}")

    status = problema.solve()
    print(f"\n📈 Status da otimização: {LpStatus[status]}")
    print("Pedidos selecionados:")
    for pedido_id, var in variaveis.items():
        if value(var) == 1.0:
            print(f"✅ Pedido {pedido_id} será atendido")
        else:
            print(f"❌ Pedido {pedido_id} será descartado")

    resultado = {
        pedido_id: int(value(var)) for pedido_id, var in variaveis.items()
    }
    return resultado
