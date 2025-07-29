import os
import json
from datetime import datetime
from typing import List, Dict, Union

PASTA_COMANDAS = "data/comandas"

def gerar_comanda_reserva_em_json(
    id_ordem: int,
    id_pedido: int,
    data_reserva: datetime,
    itens: List[Dict[str, Union[int, str, float]]]
):
    """
    Gera um arquivo .json com as reservas projetadas para um pedido.
    """
    if not os.path.exists(PASTA_COMANDAS):
        os.makedirs(PASTA_COMANDAS)

    comanda = {
        "id_ordem": id_ordem,
        "id_pedido": id_pedido,
        "data_reserva": data_reserva.strftime("%Y-%m-%d"),
        "itens": itens
    }

    nome_arquivo = f"ordem_{id_ordem}_pedido_{id_pedido}.json"
    caminho = os.path.join(PASTA_COMANDAS, nome_arquivo)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(comanda, f, ensure_ascii=False, indent=2)

    print(f"✅ Comanda salva em: {caminho}")
