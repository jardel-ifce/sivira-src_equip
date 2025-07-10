from typing import List
from datetime import timedelta
from parser.carregador_json_atividades import buscar_antecipacao_por_id_item

def ordenar_pedidos_por_antecipacao(pedidos: List) -> List:
    """
    📦 Ordena os pedidos priorizando:
    1. Pedidos que NÃO podem ser adiantados (antecipação = 00:00:00)
    2. Em seguida, pedidos que podem, em ordem crescente do tempo de antecipação.
    """
    def chave(pedido):
        antecipacao = buscar_antecipacao_por_id_item(pedido.id_item, pedido.tipo_item)
        return (antecipacao > timedelta(0), antecipacao)

    return sorted(pedidos, key=chave)
