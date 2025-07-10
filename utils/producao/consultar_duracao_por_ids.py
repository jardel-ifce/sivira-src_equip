from datetime import timedelta
import json

def string_para_timedelta(s: str) -> timedelta:
    h, m, s = map(int, s.split(":"))
    return timedelta(hours=h, minutes=m, seconds=s)

# Carregar dados
with open("jsons/faixa_tempo_subproduto.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

# Indexar por id_produto e id_atividade
indice = {}
for produto in dados:
    id_produto = produto["id_produto"]
    for atividade in produto["atividades"]:
        id_atividade = atividade["id_atividade"]
        chave = (id_produto, id_atividade)
        indice[chave] = []

        for faixa in atividade["faixas"]:
            faixa_dict = {
                "quantidade_min": int(faixa["quantidade"].split("–")[0]),
                "quantidade_max": int(faixa["quantidade"].split("–")[1]),
                "duracao": string_para_timedelta(faixa["duracao"])
            }
            indice[chave].append(faixa_dict)

def consultar_duracao_por_ids(id_produto: int, id_atividade: int, quantidade: int):
    chave = (id_produto, id_atividade)
    if chave not in indice:
        raise ValueError(f"❌ Combinação id_produto={id_produto} e id_atividade={id_atividade} não encontrada.")

    for faixa in indice[chave]:
        if faixa["quantidade_min"] <= quantidade <= faixa["quantidade_max"]:
            return faixa["duracao"]

    raise ValueError(f"❌ Quantidade {quantidade} fora das faixas registradas para id_atividade={id_atividade}.")


