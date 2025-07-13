from models.atividades.pedido_de_producao import PedidoDeProducao
from copy import deepcopy
from typing import Tuple
from enums.producao.tipo_item import TipoItem
from datetime import datetime
from factory.fabrica_funcionarios import funcionarios_disponiveis
from otimizador.verificador_pedidos import verificar_pedido_executavel_isoladamente

# Cria os pedidos
pedidos = []
for i in range(1, 4):
    pedido = PedidoDeProducao(
        ordem_id=1,
        pedido_id=i,
        id_produto=1001,
        tipo_item=TipoItem.PRODUTO,
        quantidade=240,
        inicio_jornada=datetime(2025, 6, 24, 8, 0),
        fim_jornada=datetime(2025, 6, 24, 18, 0),
        todos_funcionarios=funcionarios_disponiveis
    )
    pedidos.append(pedido)
    
for pedido in pedidos:
    sucesso, erro = verificar_pedido_executavel_isoladamente(pedido)
    print(f"Pedido {pedido.pedido_id}: {'✅ OK' if sucesso else f'❌ ERRO: {erro}'}")
