# -*- coding: utf-8 -*-
import os, sys, json
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

from otimizador.schema import ConfigGeral
from otimizador.parser_json import carregar_por_ids
from otimizador.builder import montar_instancia

if __name__ == "__main__":
    print("\n>> ETAPA 2: Builder de instância (GENÉRICO por ID, sem solver)")
    ROOT = os.environ.get("SIVIRA_ROOT", "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")
    ids = [int(x) for x in os.environ.get("ITEM_IDS", "1001,2001").split(",")]
    cfg = ConfigGeral(inicio_hhmm="06:00", fim_hhmm="17:00", t_step_min=2,
                      dias_antes=int(os.environ.get("DIAS_ANTES", "0")))
    capacidades = {
        # sobrescreva aqui se quiser
        # exemplo: "divisora_de_massas_1": 1, "masseira_1": 1,
    }

    problema = carregar_por_ids(ROOT, ids, capacidades, cfg)

    # pedidos demo (ou use PEDIDOS_JSON)
    pedidos_json = os.environ.get("PEDIDOS_JSON", "")
    if pedidos_json.strip():
        pedidos = json.loads(pedidos_json)
    else:
        pedidos = [
            {"id_pedido": 1, "id_item": 1001, "quantidade_unidades": 240, "release": "06:00", "deadline": "09:00"},
            {"id_pedido": 2, "id_item": 1001, "quantidade_unidades": 300, "release": "06:00", "deadline": "10:00"},
            {"id_pedido": 3, "id_item": 2001, "quantidade_unidades": 15000, "release": "06:00", "deadline": "12:00"},
        ]

    out = montar_instancia(problema, pedidos, capacidades_override=capacidades)
    # ✅ ADICIONAR LOGO APÓS:
    from expansor_fases import ExpansorFases
    expansor = ExpansorFases()
    dados_fases = expansor.expandir_instancia_builder_out(out, verbose=True)