#!/usr/bin/env python3
"""
Mapeador de Itens
================

Utilitário para mapear IDs de itens para seus nomes correspondentes,
consultando os arquivos JSON de subprodutos e produtos.
"""

import os
import json
from typing import Optional, Dict
from utils.logs.logger_factory import setup_logger

logger = setup_logger("MapeadorItens")

class MapeadorItens:
    """
    Classe responsável por mapear IDs de itens para seus nomes.
    Busca em arquivos JSON de subprodutos e produtos.
    """

    def __init__(self):
        self._cache_nomes = {}  # Cache para evitar releituras
        self._diretorio_subprodutos = "data/subprodutos/atividades"
        self._arquivo_produtos = "data/itens_almoxarifado.json"  # Assumindo que existe

    def obter_nome_item(self, id_item: int) -> Optional[str]:
        """
        Obtém o nome de um item pelo seu ID.

        Args:
            id_item: ID do item a ser consultado

        Returns:
            Nome do item ou None se não encontrado
        """
        # Verificar cache primeiro
        if id_item in self._cache_nomes:
            return self._cache_nomes[id_item]

        # Buscar em subprodutos primeiro
        nome = self._buscar_em_subprodutos(id_item)
        if nome:
            self._cache_nomes[id_item] = nome
            return nome

        # Se não encontrou, buscar em produtos
        nome = self._buscar_em_produtos(id_item)
        if nome:
            self._cache_nomes[id_item] = nome
            return nome

        logger.warning(f"⚠️ Nome não encontrado para id_item: {id_item}")
        return None

    def _buscar_em_subprodutos(self, id_item: int) -> Optional[str]:
        """Busca o nome do item nos arquivos de subprodutos."""
        if not os.path.exists(self._diretorio_subprodutos):
            return None

        try:
            for arquivo in os.listdir(self._diretorio_subprodutos):
                if arquivo.endswith('.json'):
                    caminho_arquivo = os.path.join(self._diretorio_subprodutos, arquivo)

                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        dados = json.load(f)

                    if dados.get('id_item') == id_item:
                        nome = dados.get('nome', '')
                        # Formatar nome: substituir underscore por espaços e capitalizar
                        nome_formatado = nome.replace('_', ' ').title()
                        logger.debug(f"✅ Subproduto encontrado: {id_item} -> {nome_formatado}")
                        return nome_formatado

        except Exception as e:
            logger.error(f"❌ Erro ao buscar em subprodutos: {e}")

        return None

    def _buscar_em_produtos(self, id_item: int) -> Optional[str]:
        """Busca o nome do item no arquivo de produtos/itens."""
        if not os.path.exists(self._arquivo_produtos):
            return None

        try:
            with open(self._arquivo_produtos, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            # Assumindo estrutura similar aos subprodutos
            if isinstance(dados, list):
                for item in dados:
                    if item.get('id_item') == id_item or item.get('id') == id_item:
                        nome = item.get('nome', item.get('name', ''))
                        nome_formatado = nome.replace('_', ' ').title()
                        logger.debug(f"✅ Produto encontrado: {id_item} -> {nome_formatado}")
                        return nome_formatado
            elif isinstance(dados, dict):
                # Se for um dicionário, pode ter estrutura diferente
                for key, item in dados.items():
                    if isinstance(item, dict):
                        if item.get('id_item') == id_item or item.get('id') == id_item:
                            nome = item.get('nome', item.get('name', key))
                            nome_formatado = nome.replace('_', ' ').title()
                            logger.debug(f"✅ Produto encontrado: {id_item} -> {nome_formatado}")
                            return nome_formatado

        except Exception as e:
            logger.error(f"❌ Erro ao buscar em produtos: {e}")

        return None

    def limpar_cache(self):
        """Limpa o cache de nomes para forçar nova consulta."""
        self._cache_nomes.clear()
        logger.info("🔄 Cache de nomes de itens limpo")

# Instância singleton
mapeador_itens = MapeadorItens()