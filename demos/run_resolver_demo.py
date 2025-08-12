# -*- coding: utf-8 -*-
import os, sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

from otimizador.schema import ConfigGeral
from otimizador.parser_json import carregar_por_ids

if __name__ == "__main__":
    print("\n>> ETAPA 1: Resolver por IDs -> Parser (GENÉRICO)")
    ROOT = os.environ.get("SIVIRA_ROOT", "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")
    ids = [int(x) for x in os.environ.get("ITEM_IDS", "1001,2001").split(",")]
    cfg = ConfigGeral(inicio_hhmm="06:00", fim_hhmm="17:00", t_step_min=2)
    problema = carregar_por_ids(ROOT, ids, {}, cfg)
    print("\n" + "="*80)
    print("✅ Resolver+Parser concluído (genérico). Resumo:")
    print(f"- Janela: {cfg.inicio_hhmm} -> {cfg.fim_hhmm} | step={cfg.t_step_min} min")
    print(f"- Total de itens carregados: {len(problema.itens)}")
    print(f"- Total de atividades: {sum(len(x.atividades) for x in problema.itens.values())}")
    print(f"- Total de recursos inferidos: {len(problema.recursos)}")
    print("="*80)
