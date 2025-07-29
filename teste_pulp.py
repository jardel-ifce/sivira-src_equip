from otimizador.otimizador_pulp import otimizar_pedidos_com_pulp
from otimizador.simulador_execucao_pedidos import executar_simulacao
from datetime import datetime
from models.atividades.pedido_de_producao import PedidoDeProducao
from factory.fabrica_funcionarios import funcionarios_disponiveis
from enums.producao.tipo_item import TipoItem
from utils.logs.gerenciador_logs import limpar_todos_os_logs

# 1. Criar os pedidos normalmente
# pedidos = [PedidoDeProducao(...), ...]
limpar_todos_os_logs()

pedidos = []
for i in range(1, 3):  # ou qualquer número de pedidos
    pedido = PedidoDeProducao(
        id_ordem=1,
        id_pedido=i,
        id_produto=1001,
        tipo_item=TipoItem.PRODUTO,
        quantidade=240,
        inicio_jornada=datetime(2025, 6, 24, 8, 0),
        fim_jornada=datetime(2025, 6, 24, 18, 0),
        todos_funcionarios=funcionarios_disponiveis
    )
    try:
        pedido.montar_estrutura()
        pedidos.append(pedido)
    except RuntimeError as e:
        print(f"⚠️ Falha ao montar estrutura do pedido {i}: {e}")


# 2. Rodar a simulação
executar_simulacao(pedidos, otimizar_pedidos_com_pulp)
