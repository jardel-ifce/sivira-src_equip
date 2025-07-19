from math import ceil

def gramas_para_caixas(quantidade_gramas: int, peso_por_caixa: int = 20000) -> int:
    """
    Converte quantidade de gramas para número de caixas.
    Cada caixa suporta 'peso_por_caixa' gramas (default = 20000g).
    """
    if quantidade_gramas <= 0:
        raise ValueError("Quantidade de gramas deve ser maior que zero.")
    return ceil(quantidade_gramas / peso_por_caixa)


def gramas_para_niveis_tela(quantidade_gramas: int, peso_por_nivel: int = 1000) -> int:
    """
    Converte quantidade de gramas para número de níveis de tela.
    Cada nível suporta 'peso_por_nivel' gramas (default = 1000g).
    """
    if quantidade_gramas <= 0:
        raise ValueError("Quantidade de gramas deve ser maior que zero.")
    return ceil(quantidade_gramas / peso_por_nivel)


def gramas_para_bocas_fogao(quantidade_gramas: int, capacidade_por_boca_max: int) -> int:
    """
    Converte quantidade de gramas para número de bocas necessárias no fogão,
    baseado na capacidade máxima por boca (em gramas).
    """
    if quantidade_gramas <= 0:
        raise ValueError("Quantidade de gramas deve ser maior que zero.")
    if capacidade_por_boca_max <= 0:
        raise ValueError("Capacidade por boca deve ser maior que zero.")
    return ceil(quantidade_gramas / capacidade_por_boca_max)

def unidades_para_niveis_tela(quantidade_unidades: int, unidades_por_nivel: int = 30) -> int:
    """
    Converte quantidade de unidades para número de níveis de tela.
    Cada nível suporta 'unidades_por_nivel' unidades.
    """
    if quantidade_unidades <= 0:
        raise ValueError("Quantidade de unidades deve ser maior que zero.")
    print(f"Quantidade de unidades: {quantidade_unidades}, Unidades por nível: {unidades_por_nivel}")
    return ceil(quantidade_unidades / unidades_por_nivel)