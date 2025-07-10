from typing import List

def chave_ordenacao_por_restricoes(pedido) -> tuple:
    """
    Gera uma tupla de ordenação com:
    - tempo_de_antecipacao da última atividade
    - tempo_de_espera da penúltima
    - tempo_de_espera da antepenúltima
    """
    atividades = pedido.atividades_modulares
    criterios = []

    for i in range(len(atividades)-1, -1, -1):
        atividade = atividades[i]
        if i == len(atividades) - 1:
            criterios.append(atividade.tempo_de_antecipacao.total_seconds())
        else:
            criterios.append(atividade.tempo_de_espera.total_seconds())

    return tuple(criterios)

def ordenar_pedidos_por_restricoes(pedidos: List) -> List:
    return sorted(pedidos, key=chave_ordenacao_por_restricoes)
