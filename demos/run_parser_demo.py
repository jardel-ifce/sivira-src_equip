# -*- coding: utf-8 -*-
import os, sys, json
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

from otimizador.schema import ConfigGeral
from otimizador.parser_json import carregar_por_ids

if __name__ == "__main__":
    print("\n>> ETAPA 1: Parser JSON -> Estrutura Básica\n")
    ROOT = os.environ.get("SIVIRA_ROOT", "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")
    ids = [int(x) for x in os.environ.get("ITEM_IDS", "1001,2001").split(",")]
    cfg = ConfigGeral(inicio_hhmm="06:00", fim_hhmm="17:00", t_step_min=2,
                      dias_antes=int(os.environ.get("DIAS_ANTES", "0")))
    capacidades = {}  # pode sobrescrever se quiser
    problema = carregar_por_ids(ROOT, ids, capacidades, cfg)
