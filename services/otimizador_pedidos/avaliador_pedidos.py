# services/otimizador_pedidos/avaliador_pedidos.py

import copy
from typing import List
from models.atividades.pedido_de_producao import PedidoDeProducao
from utils.logger_factory import setup_logger

logger = setup_logger("AvaliadorPedidos")

def avaliar_sequencia_de_pedidos(sequencia: List[PedidoDeProducao]) -> int:
    """
    Avalia quantos pedidos conseguem ser alocados com sucesso com base nos equipamentos.
    Faz uma deep copy da lista para não afetar os objetos reais.
    """
    pedidos_clonados = [copy.deepcopy(pedido) for pedido in sequencia]
    total_sucesso = 0

    for pedido in pedidos_clonados:
        try:
            pedido.montar_estrutura()
            pedido.criar_atividades_modulares_necessarias()
            pedido.executar_atividades_em_ordem()
            total_sucesso += 1
        except Exception as e:
            logger.warning(f"❌ Pedido {pedido.pedido_id} falhou: {e}")

    return total_sucesso
