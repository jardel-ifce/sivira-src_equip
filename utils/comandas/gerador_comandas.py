import os
import json
from datetime import datetime
from typing import List, Dict, Union

PASTA_COMANDAS = "data/comandas"

def gerar_comanda_reserva_em_json(
    ordem_id: int,
    pedido_id: int,
    data_reserva: datetime,
    itens: List[Dict[str, Union[int, str, float]]]
):
    """
    Gera um arquivo .json com as reservas projetadas para um pedido.
    """
    if not os.path.exists(PASTA_COMANDAS):
        os.makedirs(PASTA_COMANDAS)

    comanda = {
        "ordem_id": ordem_id,
        "pedido_id": pedido_id,
        "data_reserva": data_reserva.strftime("%Y-%m-%d"),
        "itens": itens
    }

    nome_arquivo = f"ordem_{ordem_id}_pedido_{pedido_id}.json"
    caminho = os.path.join(PASTA_COMANDAS, nome_arquivo)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(comanda, f, ensure_ascii=False, indent=2)

    print(f"✅ Comanda salva em: {caminho}")
