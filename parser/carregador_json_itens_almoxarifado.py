import json
from typing import List
from enums.tipo_item import TipoItem
from enums.politica_producao import PoliticaProducao
from enums.unidade_medida import UnidadeMedida
from models.itens.item_almoxarifado import ItemAlmoxarifado


def carregar_itens_almoxarifado(caminho_json: str) -> List[ItemAlmoxarifado]:
    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    itens = []
    for d in dados:
        ficha_tecnica_id = None
        if "ficha_tecnica" in d and d["ficha_tecnica"]:
            ficha_tecnica_id = d["ficha_tecnica"].get("id_ficha_tecnica")

        item = ItemAlmoxarifado(
            id_item=d["id_item"],
            nome=d["nome"],
            descricao=d["descricao"],
            tipo_item=TipoItem[d["tipo_item"]],
            peso=d["peso"],
            unidade_medida=UnidadeMedida[d["unidade_medida"]],
            estoque_min=d["estoque_min"],
            estoque_max=d["estoque_max"],
            estoque_atual=d.get("estoque_atual", d["estoque_min"]),
            politica_producao=PoliticaProducao[d["politica_producao"]],
            ficha_tecnica=ficha_tecnica_id,
            consumo_diario_estimado=d.get("consumo_diario_estimado"),
            reabastecimento_previsto_em=d.get("reabastecimento_previsto_em"),
            reservas_futuras=d.get("reservas_futuras", [])
        )
        itens.append(item)

    return itens
