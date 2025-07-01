# services/otimizador_pedidos/otimizador_genetico_equipamentos.py

import random
import copy
from typing import List
from models.atividades.pedido_de_producao import PedidoDeProducao
from services.otimizador_pedidos.avaliador_pedidos import avaliar_sequencia_de_pedidos
from services.otimizador_pedidos.gerador_populacao import gerar_populacao_inicial
from services.otimizador_pedidos.utils_genetico import selecao, crossover, mutacao

def executar_otimizacao_genetica(
    pedidos_originais: List[PedidoDeProducao],
    n_geracoes: int = 30,
    tamanho_populacao: int = 20,
    taxa_mutacao: float = 0.1
) -> List[PedidoDeProducao]:
    """
    Executa um algoritmo genético para encontrar a melhor sequência de pedidos
    que maximize o número de alocações de equipamentos com sucesso.
    """
    populacao = gerar_populacao_inicial(pedidos_originais, tamanho_populacao)

    for _ in range(n_geracoes):
        avaliados = [(seq, avaliar_sequencia_de_pedidos(seq)) for seq in populacao]
        avaliados.sort(key=lambda x: x[1], reverse=True)

        nova_populacao = []

        # Elitismo (mantém os melhores)
        elite = [ind for ind, _ in avaliados[:2]]
        nova_populacao.extend(elite)

        while len(nova_populacao) < tamanho_populacao:
            pai1, pai2 = selecao(avaliados)
            filho = crossover(pai1, pai2)
            filho = mutacao(filho, taxa_mutacao)
            nova_populacao.append(filho)

        populacao = nova_populacao

    melhor_seq, _ = max(
        [(seq, avaliar_sequencia_de_pedidos(seq)) for seq in populacao],
        key=lambda x: x[1]
    )
    return melhor_seq
