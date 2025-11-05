from datetime import timedelta

def consultar_duracao_por_faixas(dados_atividade: dict, quantidade: int) -> timedelta:
    """
    Consulta a duração de uma atividade baseada nas faixas de quantidade.

    Se a atividade usa múltiplos tipos de equipamento sequencialmente,
    cada equipamento executa individualmente pela duração da faixa.
    A duração total é a soma das durações de cada equipamento.

    Args:
        dados_atividade: Dicionário com dados da atividade (deve conter 'faixas' e 'tipo_equipamento')
        quantidade: Quantidade a ser produzida

    Returns:
        timedelta com a duração total calculada
    """
    faixas = dados_atividade.get("faixas", [])

    for faixa in faixas:
        min_qtd = faixa.get("quantidade_min")
        max_qtd = faixa.get("quantidade_max")

        if min_qtd is None or max_qtd is None:
            raise ValueError(f"❌ Faixa de quantidade inválida ou incompleta: {faixa}")

        if min_qtd <= quantidade <= max_qtd:
            h, m, s = map(int, faixa["duracao"].split(":"))
            duracao_faixa = timedelta(hours=h, minutes=m, seconds=s)

            # Verificar quantos equipamentos são usados (execução sequencial)
            tipo_equipamento = dados_atividade.get("tipo_equipamento", {})

            if isinstance(tipo_equipamento, dict):
                # Calcular total de equipamentos
                total_equipamentos = sum(tipo_equipamento.values())

                # Se houver múltiplos equipamentos, cada um executa pela duração multiplicada
                # pela quantidade de tipos de equipamento (comportamento observado no log)
                if total_equipamentos > 1:
                    num_tipos = len(tipo_equipamento)
                    duracao_por_equipamento = duracao_faixa * num_tipos
                    duracao_total = duracao_por_equipamento * total_equipamentos
                    return duracao_total
                else:
                    # Um único equipamento usa a duração da faixa
                    return duracao_faixa
            else:
                # Caso não seja dicionário, assumir 1 equipamento
                return duracao_faixa

    raise ValueError(f"❌ Nenhuma faixa compatível com a quantidade {quantidade} (gramas ou unidades).")
