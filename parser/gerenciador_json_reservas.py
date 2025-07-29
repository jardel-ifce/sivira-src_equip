import json
import os
from typing import List, Dict, Optional, Union
from datetime import datetime, date

CAMINHO_ITENS = "data/almoxarifado/itens_almoxarifado.json"

def registrar_reservas_em_itens_almoxarifado(reservas: List[Dict], caminho: str = CAMINHO_ITENS) -> None:
    """
    📝 Atualiza o JSON de itens do almoxarifado com as novas reservas vindas das comandas.
    Apenas reservas com tipo 'CONSUMO' são registradas.
    Inclui os campos: data, quantidade_reservada, id_ordem, id_pedido, id_atividade (opcional).
    """
    if not os.path.exists(caminho):
        print(f"❌ Arquivo de itens não encontrado: {caminho}")
        return

    with open(caminho, "r", encoding="utf-8") as f:
        itens = json.load(f)

    mapa_itens = {item["id_item"]: item for item in itens}

    for reserva in reservas:
        if "tipo" in reserva and reserva["tipo"] != "CONSUMO":
            continue

        id_item = reserva["id_item"]
        data = reserva["data_reserva"]
        quantidade = reserva["quantidade_necessaria"]
        id_ordem = reserva.get("id_ordem", 0)
        id_pedido = reserva.get("id_pedido", 0)
        id_atividade = reserva.get("id_atividade")

        item = mapa_itens.get(id_item)
        if item is None:
            print(f"⚠️ Item com id {id_item} não encontrado no almoxarifado.")
            continue

        if "reservas_futuras" not in item:
            item["reservas_futuras"] = []

        reservas_item = item["reservas_futuras"]

        # Checa se já existe uma reserva exatamente com a mesma data, ordem e pedido
        existente = next(
            (
                r for r in reservas_item
                if r["data"] == data and r.get("id_ordem") == id_ordem and r.get("id_pedido") == id_pedido
            ),
            None
        )

        if existente:
            existente["quantidade_reservada"] += round(quantidade, 2)
        else:
            nova_reserva = {
                "data": data,
                "quantidade_reservada": round(quantidade, 2),
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
            }
            if id_atividade is not None:
                nova_reserva["id_atividade"] = id_atividade

            reservas_item.append(nova_reserva)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(list(mapa_itens.values()), f, indent=2, ensure_ascii=False)

    print(f"✅ Reservas registradas com sucesso no arquivo: {caminho}")

def descontar_estoque_por_reservas(
    data: Optional[Union[str, date, datetime]] = None,
    id_ordem: Optional[int] = None,
    id_pedido: Optional[int] = None,
    caminho: str = CAMINHO_ITENS
) -> None:
    """
    🔻 Desconta o estoque_atual dos itens com base nas reservas_futuras.
    Se nenhum parâmetro for passado, todas as reservas serão consumidas.
    Parâmetros opcionais permitem filtrar por data (str, date ou datetime), id_ordem e id_pedido.
    """
    if not os.path.exists(caminho):
        print(f"❌ Arquivo não encontrado: {caminho}")
        return

    # Normalizar a data para string no formato YYYY-MM-DD
    if data is not None:
        if isinstance(data, datetime):
            data = data.date().isoformat()
        elif isinstance(data, date):
            data = data.isoformat()
        elif isinstance(data, str):
            try:
                datetime.strptime(data, "%Y-%m-%d")  # valida o formato
            except ValueError:
                print(f"❌ Data inválida: {data}")
                return
        else:
            print(f"❌ Tipo de data não suportado: {type(data)}")
            return

    with open(caminho, "r", encoding="utf-8") as f:
        itens = json.load(f)

    for item in itens:
        reservas = item.get("reservas_futuras", [])
        novas_reservas = []
        total_descontado = 0.0

        for reserva in reservas:
            cond_data = (data is None or reserva["data"] == data)
            cond_ordem = (id_ordem is None or reserva.get("id_ordem") == id_ordem)
            cond_pedido = (id_pedido is None or reserva.get("id_pedido") == id_pedido)

            if cond_data and cond_ordem and cond_pedido:
                total_descontado += reserva["quantidade_reservada"]
            else:
                novas_reservas.append(reserva)

        if total_descontado > 0:
            item["estoque_atual"] = round(item.get("estoque_atual", 0) - total_descontado, 2)
            item["reservas_futuras"] = novas_reservas
            print(f"🟢 Item {item['id_item']} atualizado | ↓{total_descontado} | Estoque atual: {item['estoque_atual']}")

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(itens, f, indent=2, ensure_ascii=False)

    print("✅ Descontos aplicados com sucesso.")
