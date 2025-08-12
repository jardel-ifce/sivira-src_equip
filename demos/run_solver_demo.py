# -*- coding: utf-8 -*-
import os, sys, datetime as dt
ROOT_DEFAULT = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip"
sys.path.append(os.environ.get("SIVIRA_ROOT", ROOT_DEFAULT))

from otimizador.path_resolver import resolver_por_ids
from otimizador.parser_json import parse_item_json
from otimizador.builder import InstanciaBuilder, print_instancia_debug
from otimizador.modelo import resolver_milp

def equip_label(rid: str) -> str:
    if rid is None:
        return "—"
    rid = str(rid)
    rep = (
        ("forno_", "Forno "),
        ("armario_fermentador_", "Armário Fermentador "),
        ("modeladora_de_paes_", "Modeladora de Pães "),
        ("divisora_de_massas_", "Divisora de Massas "),
        ("balanca_digital_", "Balança Digital "),
        ("bancada_", "Bancada "),
        ("masseira_", "Masseira "),
        ("embaladora_", "Embaladora "),
    )
    for k, v in rep:
        if rid.startswith(k):
            return v + rid.split("_")[-1]
    return rid

def render_dt(dtobj: dt.datetime) -> str:
    return dtobj.strftime("%H:%M [%d/%m]")

def escrever_logs(sol, inst):
    base_ordem = 1
    por_pedido = {}
    for k,info in sol["atividades"].items():
        por_pedido.setdefault(info["pedido"], []).append(info)
    for pid, lst in por_pedido.items():
        lst_sorted = sorted(lst, key=lambda x: x["t0"])
        path = f"ordem: {base_ordem} | pedido: {pid}.log"
        with open(path, "w", encoding="utf-8") as f:
            for reg in lst_sorted:
                linha = (
                    f"{base_ordem} | {reg['pedido']} | {reg['id_atividade']} | "
                    f"{reg['nome_item']} | {reg['nome_atividade']} | "
                    f"{equip_label(reg['recurso'])} | "
                    f"{render_dt(reg['t0'])} | {render_dt(reg['tf'])} \n"
                )
                f.write(linha)
        print(f"[LOG] salvo {path}")

if __name__ == "__main__":
    print(">> ETAPA 3: Solver MILP (PuLP)")
    ROOT = os.environ.get("SIVIRA_ROOT", ROOT_DEFAULT)
    ids_str = os.environ.get("ITEM_IDS", "1001,2001")
    ids = [int(x.strip()) for x in ids_str.split(",") if x.strip()]
    print(f"ROOT = {ROOT}")
    print(f"ITEM_IDS = {','.join(str(i) for i in ids)}")

    mapping = resolver_por_ids(ROOT, ids)
    itens = [parse_item_json(path) for _, path in mapping.items()]

    t0 = dt.datetime.strptime(os.environ.get("SC_T0", "2025-06-25 06:00"), "%Y-%m-%d %H:%M")
    tf = dt.datetime.strptime(os.environ.get("SC_TF", "2025-06-25 17:00"), "%Y-%m-%d %H:%M")
    step = int(os.environ.get("STEP_MIN", "2"))

    builder = InstanciaBuilder(t0=t0, tf=tf, step_minutes=step)
    cfgs = [
        (1, 1001, 240, t0, t0.replace(hour=9)),
        (2, 1001, 300, t0, t0.replace(hour=10)),
        (3, 2001, 15000, t0, t0.replace(hour=12)),
    ]
    for idx, iid, qtd, a, b in cfgs:
        item = next(x for x in itens if x.id_item == iid)
        builder.adicionar_pedido(idx, item, qtd, a, b)

    inst = builder.construir_instancia()
    # ✅ ADICIONAR:
    from expansor_fases import ExpansorFases
    expansor = ExpansorFases()  
    dados_fases = expansor.expandir_instancia_builder_out(inst)
    print_instancia_debug(inst)

    sol = resolver_milp(inst, ignorar_profissionais=True, verbose=True)

    # Relatório final estilo antes
    status = sol["status"]; obj = sol["objetivo"]
    print(f"\n🧮 Status do solver: {status} | Z* = {obj}")
    print("\n" + "="*80)
    print(f"Status: {status}")
    print("Pedidos:")
    for ped in inst.pedidos:
        aceito = ped.idx in sol["aceitos"]
        print(f"  - Pedido {ped.idx}: {'ACEITO' if aceito else 'REJEITADO'}")

    print("\nCronograma (atividades):")
    for ped in inst.pedidos:
        for a in ped.atividades:
            info = sol["atividades"].get(a.chave)
            if not info:
                print(f"  • {a.chave} '{a.nome_atividade}': NÃO ALOCADA")
            else:
                print(f"  • {a.chave} '{a.nome_atividade}': {info['t0']:%H:%M}–{info['tf']:%H:%M} ({int((info['tf']-info['t0']).total_seconds()/60)} min)")
    print("\nAgenda por recurso (equipamentos):")
    # simples: lista das atividades por recurso
    by_res = {}
    for k,info in sol["atividades"].items():
        if info["recurso"]:
            by_res.setdefault(info["recurso"], []).append(info)
    for r, lst in by_res.items():
        print(f"  > {r} (cap={inst.recursos_cap.get(r,'?')})")
        for reg in sorted(lst, key=lambda x: x["t0"]):
            print(f"     - {reg['t0']:%H:%M}–{reg['tf']:%H:%M} | {reg['pedido']}:{reg['id_atividade']} | {reg['nome_item']}")

    # Escrever logs no formato pedido
    escrever_logs(sol, inst)
