import os
import json
from datetime import datetime
from typing import List, Dict, Union

def salvar_comanda_em_json(
    id_ordem: int,
    id_pedido: int,
    data_reserva: datetime,
    itens: List[Dict[str, Union[int, str, float]]]
) -> None:
    """
    💾 Salva a comanda de reserva como arquivo JSON.
    """
    pasta_saida = "data/comandas"
    os.makedirs(pasta_saida, exist_ok=True)

    nome_arquivo = f"comanda_ordem_{id_ordem}_pedido_{id_pedido}.json"
    caminho = os.path.join(pasta_saida, nome_arquivo)

    dados = {
        "id_ordem": id_ordem,
        "id_pedido": id_pedido,
        "data_reserva": data_reserva.strftime("%Y-%m-%d"),
        "itens": itens
    }

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"✅ Comanda salva em: {caminho}")


def ler_comandas_em_pasta(
    caminho: str = "data/comandas"
) -> List[Dict[str, Union[int, float, str]]]:
    """
    📥 Lê todas as comandas (.json) da pasta especificada.
    Retorna uma lista de reservas individuais, incluindo subprodutos e insumos aninhados.
    """
    reservas: List[Dict[str, Union[int, float, str]]] = []

    def extrair_reservas_recursivas(
        item: Dict[str, Union[int, str, float, List]],
        id_ordem: int,
        id_pedido: int,
        data_reserva: str
    ) -> List[Dict[str, Union[int, float, str]]]:
        """
        🔄 Extrai reservas de um item e seus itens_necessarios recursivamente.
        """
        reservas_extraidas = []

        # Itens obrigatórios
        id_item = item.get("id_item") or item.get("id_subproduto")
        quantidade = item.get("quantidade_necessaria", 0)

        if id_item is not None:
            reservas_extraidas.append({
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_item": id_item,
                "quantidade_necessaria": quantidade,
                "data_reserva": data_reserva,
                "tipo": "CONSUMO",
                "id_atividade": None
            })

        # Processa filhos recursivamente
        for subitem in item.get("itens_necessarios", []):
            reservas_extraidas.extend(
                extrair_reservas_recursivas(subitem, id_ordem, id_pedido, data_reserva)
            )

        return reservas_extraidas

    if not os.path.exists(caminho):
        print(f"📁 Pasta de comandas não encontrada: {caminho}")
        return reservas

    for arquivo in os.listdir(caminho):
        if not arquivo.endswith(".json"):
            continue

        caminho_arquivo = os.path.join(caminho, arquivo)
        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                comanda = json.load(f)

            id_ordem = comanda["id_ordem"]
            id_pedido = comanda["id_pedido"]
            data_reserva = comanda["data_reserva"]

            for item in comanda.get("itens", []):
                reservas.extend(
                    extrair_reservas_recursivas(item, id_ordem, id_pedido, data_reserva)
                )

            print(f"✅ Comanda processada: {arquivo}")

        except Exception as e:
            print(f"❌ Erro ao ler '{arquivo}': {e}")

    return reservas
