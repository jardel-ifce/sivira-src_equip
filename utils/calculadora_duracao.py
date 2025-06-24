from datetime import timedelta

def consultar_duracao_por_faixas(dados_atividade: dict, quantidade: int) -> timedelta:
    faixas = dados_atividade.get("faixas", [])

    for faixa in faixas:
        min_qtd = faixa.get("quantidade_min")
        max_qtd = faixa.get("quantidade_max")

        if min_qtd is None or max_qtd is None:
            raise ValueError(f"❌ Faixa de quantidade inválida ou incompleta: {faixa}")

        if min_qtd <= quantidade <= max_qtd:
            h, m, s = map(int, faixa["duracao"].split(":"))
            return timedelta(hours=h, minutes=m, seconds=s)

    raise ValueError(f"❌ Nenhuma faixa compatível com a quantidade {quantidade}g.")
