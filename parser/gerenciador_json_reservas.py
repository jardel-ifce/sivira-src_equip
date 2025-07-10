import json
import os
from typing import List, Dict, Optional, Union
from datetime import datetime, date

CAMINHO_ITENS = "data/almoxarifado/itens_almoxarifado.json"

def registrar_reservas_em_itens_almoxarifado(reservas: List[Dict], caminho: str = CAMINHO_ITENS) -> None:
    """
    📝 Atualiza o JSON de itens do almoxarifado com as novas reservas vindas das comandas.
    Apenas reservas com tipo 'CONSUMO' são registradas.
    Inclui os campos: data, quantidade_reservada, ordem_id, pedido_id, atividade_id (opcional).
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
        ordem_id = reserva.get("ordem_id", 0)
        pedido_id = reserva.get("pedido_id", 0)
        atividade_id = reserva.get("atividade_id")

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
                if r["data"] == data and r.get("ordem_id") == ordem_id and r.get("pedido_id") == pedido_id
            ),
            None
        )

        if existente:
            existente["quantidade_reservada"] += round(quantidade, 2)
        else:
            nova_reserva = {
                "data": data,
                "quantidade_reservada": round(quantidade, 2),
                "ordem_id": ordem_id,
                "pedido_id": pedido_id,
            }
            if atividade_id is not None:
                nova_reserva["atividade_id"] = atividade_id

            reservas_item.append(nova_reserva)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(list(mapa_itens.values()), f, indent=2, ensure_ascii=False)

    print(f"✅ Reservas registradas com sucesso no arquivo: {caminho}")

def descontar_estoque_por_reservas(
    data: Optional[Union[str, date, datetime]] = None,
    ordem_id: Optional[int] = None,
    pedido_id: Optional[int] = None,
    caminho: str = CAMINHO_ITENS
) -> None:
    """
    🔻 Desconta o estoque_atual dos itens com base nas reservas_futuras.
    Se nenhum parâmetro for passado, todas as reservas serão consumidas.
    Parâmetros opcionais permitem filtrar por data (str, date ou datetime), ordem_id e pedido_id.
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
            cond_ordem = (ordem_id is None or reserva.get("ordem_id") == ordem_id)
            cond_pedido = (pedido_id is None or reserva.get("pedido_id") == pedido_id)

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
