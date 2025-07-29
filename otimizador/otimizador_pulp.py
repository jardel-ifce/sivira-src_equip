from pulp import LpProblem, LpVariable, LpMaximize, LpBinary, LpStatus, value
from typing import List
from copy import deepcopy
from models.atividades.pedido_de_producao import PedidoDeProducao

def otimizar_pedidos_com_pulp(pedidos: List[PedidoDeProducao]):
    print("\n🔍 Iniciando otimização com Programação Linear...")

    problema = LpProblem("Maximizacao_Pedidos", LpMaximize)

    variaveis = {
        pedido.id_pedido: LpVariable(f"x_{pedido.id_pedido}", cat=LpBinary)
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
            problema += variaveis[pedido.id_pedido] == 0, f"Restricao_Falha_{pedido.id_pedido}"
            print(f"❌ Pedido {pedido.id_pedido} não viável isoladamente: {e}")

    status = problema.solve()
    print(f"\n📈 Status da otimização: {LpStatus[status]}")
    print("Pedidos selecionados:")
    for id_pedido, var in variaveis.items():
        if value(var) == 1.0:
            print(f"✅ Pedido {id_pedido} será atendido")
        else:
            print(f"❌ Pedido {id_pedido} será descartado")

    resultado = {
        id_pedido: int(value(var)) for id_pedido, var in variaveis.items()
    }
    return resultado
