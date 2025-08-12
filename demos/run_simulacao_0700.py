# -*- coding: utf-8 -*-
import os, sys, datetime as dt
ROOT_DEFAULT = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip"
sys.path.append(os.environ.get("SIVIRA_ROOT", ROOT_DEFAULT))

from otimizador.path_resolver import resolver_item_paths
from otimizador.parser_json import parse_item_json
from otimizador.builder import InstanciaBuilder
from otimizador.modelo import resolver_milp

def equip_label(rid: str) -> str:
    if rid is None: return "—"
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

def escrever_logs(sol):
    base_ordem = 1
    por_pedido = {}
    for k,info in sol["atividades"].items():
        pid = info["pedido"]
        por_pedido.setdefault(pid, []).append(info)
    for pid, lst in por_pedido.items():
        lst_sorted = sorted(lst, key=lambda x: x["t0"])
        path = f"ordem: {base_ordem} | pedido: {pid}.log"
        with open(path, "w", encoding="utf-8") as f:
            for reg in lst_sorted:
                t0 = dt.datetime.fromisoformat(reg["t0"])
                tf = dt.datetime.fromisoformat(reg["tf"])
                linha = (
                    f"{base_ordem} | {reg['pedido']} | {reg['id_atividade']} | "
                    f"{reg['nome_item']} | {reg['nome_atividade']} | "
                    f"{equip_label(reg['recurso'])} | "
                    f"{render_dt(t0)} | {render_dt(tf)}\n"
                )
                f.write(linha)
        print(f"[LOG] salvo {path}")

if __name__ == "__main__":
    print(">> Simulação 07:00: 3 pedidos (com subprodutos)")
    ROOT = os.environ.get("SIVIRA_ROOT", ROOT_DEFAULT)

    # Mapeamento básico nome -> id
    nome_to_id = {
        "Pão Francês": 1001,
        "Pão Hambúrguer": 1002,
        "Pão de Forma": 1003,
    }
    # Seus 3 pedidos (todos com hora_fim = 07:00 e âncora na última atv do PRODUTO)
    pedidos_cfg = [
        {"produto": "Pão Francês", "quantidade": 450, "hora_fim": 7, "subs":[2001]},
        {"produto": "Pão Hambúrguer", "quantidade": 120, "hora_fim": 7, "subs":[2002]},
        {"produto": "Pão de Forma", "quantidade": 70,  "hora_fim": 7, "subs":[2002]},
    ]

    # Janela global
    SC_T0 = os.environ.get("SC_T0", "2025-06-25 02:00")
    SC_TF = os.environ.get("SC_TF", "2025-06-26 07:00")  # termina estritamente às 07:00
    t0 = dt.datetime.strptime(SC_T0, "%Y-%m-%d %H:%M")
    tf = dt.datetime.strptime(SC_TF, "%Y-%m-%d %H:%M")
    STEP_MIN = int(os.environ.get("STEP_MIN", "1"))

    builder = InstanciaBuilder(t0=t0, tf=tf, step_minutes=STEP_MIN)
    for idx, cfg in enumerate(pedidos_cfg, start=1):
        iid = nome_to_id[cfg["produto"]]
        pth = resolver_item_paths(ROOT, iid)
        if not pth["ativ"]:
            raise FileNotFoundError(f"Atividades do item {iid} não encontradas.")
        item = parse_item_json(pth["ativ"])
        janela_ini = t0
        janela_fim = tf  # âncora na última atv do PRODUTO
        builder.adicionar_pedido(
            idx=idx, item=item, quantidade=cfg["quantidade"],
            janela_ini=janela_ini, janela_fim=janela_fim,
            subprodutos_ids=cfg.get("subs", []),
            resolver_path_fn=lambda sid, _root=ROOT: resolver_item_paths(_root, sid)
        )
    inst = builder.construir_instancia()

    sol = resolver_milp(inst, ignorar_profissionais=True, verbose=True)
    escrever_logs(sol)

    print("\nResumo:")
    print(f" - Pedidos aceitos: {sol['aceitos']} / total={len(pedidos_cfg)}")
    for i in range(1, len(pedidos_cfg)+1):
        ok = "ACEITO" if i in sol["aceitos"] else "REJEITADO"
        print(f"   Pedido {i}: {ok}")
