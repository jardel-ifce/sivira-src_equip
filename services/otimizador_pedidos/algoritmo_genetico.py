# services/otimizador_pedidos/algoritmo_genetico.py

import random
import copy
from typing import List
from models.atividades.pedido_de_producao import PedidoDeProducao
from services.otimizador_pedidos.avaliador_pedidos import avaliar_sequencia_de_pedidos
from utils.logs.logger_factory import setup_logger

logger = setup_logger("AlgoritmoGenetico")

class AlgoritmoGenetico:
    def __init__(self, pedidos: List[PedidoDeProducao], tamanho_populacao=20, geracoes=30, taxa_mutacao=0.2):
        self.pedidos_originais = pedidos
        self.tamanho_populacao = tamanho_populacao
        self.geracoes = geracoes
        self.taxa_mutacao = taxa_mutacao

    def _gerar_populacao_inicial(self) -> List[List[PedidoDeProducao]]:
        populacao = []
        for _ in range(self.tamanho_populacao):
            cromossomo = random.sample(self.pedidos_originais, len(self.pedidos_originais))
            populacao.append(cromossomo)
        return populacao

    def _selecionar_pais(self, populacao: List[List[PedidoDeProducao]]) -> List[List[PedidoDeProducao]]:
        populacao_ordenada = sorted(populacao, key=avaliar_sequencia_de_pedidos, reverse=True)
        return populacao_ordenada[:2]  # elitismo: seleciona os dois melhores

    def _crossover(self, pai1: List[PedidoDeProducao], pai2: List[PedidoDeProducao]) -> List[PedidoDeProducao]:
        tamanho = len(pai1)
        ponto_corte = random.randint(1, tamanho - 2)
        filho = pai1[:ponto_corte] + [p for p in pai2 if p not in pai1[:ponto_corte]]
        return filho

    def _mutar(self, individuo: List[PedidoDeProducao]):
        if random.random() < self.taxa_mutacao:
            i, j = random.sample(range(len(individuo)), 2)
            individuo[i], individuo[j] = individuo[j], individuo[i]

    def executar(self) -> List[PedidoDeProducao]:
        populacao = self._gerar_populacao_inicial()
        melhor_solucao = []
        melhor_score = -1

        for geracao in range(self.geracoes):
            nova_populacao = []
            pais = self._selecionar_pais(populacao)
            nova_populacao.extend(pais)

            while len(nova_populacao) < self.tamanho_populacao:
                filho = self._crossover(*random.sample(pais, 2))
                self._mutar(filho)
                nova_populacao.append(filho)

            populacao = nova_populacao

            melhor_individuo = max(populacao, key=avaliar_sequencia_de_pedidos)
            score = avaliar_sequencia_de_pedidos(melhor_individuo)

            logger.info(f"Geração {geracao + 1}: {score} pedidos alocados com sucesso")

            if score > melhor_score:
                melhor_score = score
                melhor_solucao = melhor_individuo

        return melhor_solucao
