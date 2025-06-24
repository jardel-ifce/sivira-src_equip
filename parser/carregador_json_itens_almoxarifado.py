import json
from typing import List, Optional
from enums.tipo_item import TipoItem
from enums.politica_producao import PoliticaProducao
from enums.unidade_medida import UnidadeMedida
from models.ficha_tecnica_modular import FichaTecnicaModular
from models.itens.item_almoxarifado import ItemAlmoxarifado
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id

def carregar_itens_almoxarifado(caminho_json: str) -> List[ItemAlmoxarifado]:
    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    itens = []
    for d in dados:
        ficha = None
        if "ficha_tecnica" in d and d["ficha_tecnica"]:
            id_ficha = d["ficha_tecnica"]["id_ficha_tecnica"]
            _, dados_ficha = buscar_ficha_tecnica_por_id(id_ficha, TipoItem[d["tipo_item"]])
            ficha = FichaTecnicaModular(
                dados_ficha_tecnica=dados_ficha,
                quantidade_requerida=d["ficha_tecnica"].get("quantidade_base", 0)  # ou outro valor default
            )

        item = ItemAlmoxarifado(
            id=d["id_item"],
            descricao=d["descricao"],
            tipo_item=TipoItem[d["tipo_item"]],
            peso=d["peso"],
            unidade_medida=UnidadeMedida[d["unidade_medida"]],
            estoque_min=d["estoque_min"],
            estoque_max=d["estoque_max"],
            estoque_atual=d.get("estoque_atual", d["estoque_min"]),
            politica_producao=PoliticaProducao[d["politica_producao"]],
            ficha_tecnica=ficha,
            consumo_diario_estimado=d.get("consumo_diario_estimado"),
            reabastecimento_previsto_em=d.get("reabastecimento_previsto_em"),
            reservas_futuras=d.get("reservas_futuras", [])
        )
        itens.append(item)

    return itens
