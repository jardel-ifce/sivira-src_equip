import random
from typing import List

def gerar_populacao_inicial(pedidos: List, tamanho_populacao: int) -> List[List]:
    """
    🧬 Gera uma população inicial para o algoritmo genético.
    
    Cada indivíduo é uma ordem diferente (permutações) dos pedidos.
    """
    populacao = []
    for _ in range(tamanho_populacao):
        individuo = pedidos.copy()
        random.shuffle(individuo)
        populacao.append(individuo)
    return populacao
