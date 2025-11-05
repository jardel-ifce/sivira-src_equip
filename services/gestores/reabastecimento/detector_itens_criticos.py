"""
Detector de Itens Críticos para Reabastecimento.

Identifica subprodutos estocados que estão abaixo do estoque mínimo
e precisam ser reabastecidos.
"""

from typing import List, Dict
from enums.producao.tipo_item import TipoItem
from enums.producao.politica_producao import PoliticaProducao


class DetectorItensCriticos:
    """
    Detecta itens críticos que precisam de reabastecimento.

    Critérios:
    - tipo_item == SUBPRODUTO
    - politica_producao == ESTOCADO
    - estoque_atual < estoque_minimo
    """

    def __init__(self, almoxarifado):
        """
        Inicializa o detector.

        Args:
            almoxarifado: Instância do almoxarifado
        """
        self.almoxarifado = almoxarifado

    def detectar_itens_criticos(self) -> List[Dict]:
        """
        Detecta itens críticos que precisam de reabastecimento.

        Returns:
            Lista de dicionários com informações dos itens críticos:
            [
                {
                    'id': int,
                    'nome': str,
                    'descricao': str,
                    'estoque_atual': float,
                    'estoque_minimo': float,
                    'estoque_maximo': float,
                    'quantidade_reabastecer': float,
                    'deficit': float,
                    'percentual_deficit': float,
                    'unidade_medida': str
                }
            ]
        """
        itens_criticos = []

        for item in self.almoxarifado.itens:
            # Verificar se atende aos critérios
            if not self._item_requer_reabastecimento(item):
                continue

            # Calcular quantidades
            deficit = item.estoque_min - item.estoque_atual
            quantidade_reabastecer = item.estoque_max - item.estoque_atual
            percentual_deficit = (deficit / item.estoque_min * 100) if item.estoque_min > 0 else 0

            itens_criticos.append({
                'id': item.id_item,
                'nome': item.nome,
                'descricao': item.descricao,
                'estoque_atual': item.estoque_atual,
                'estoque_minimo': item.estoque_min,
                'estoque_maximo': item.estoque_max,
                'quantidade_reabastecer': quantidade_reabastecer,
                'deficit': deficit,
                'percentual_deficit': percentual_deficit,
                'unidade_medida': item.unidade_medida.value if hasattr(item.unidade_medida, 'value') else str(item.unidade_medida)
            })

        # Ordenar por percentual de déficit (mais críticos primeiro)
        itens_criticos.sort(key=lambda x: x['percentual_deficit'], reverse=True)

        return itens_criticos

    def _item_requer_reabastecimento(self, item) -> bool:
        """
        Verifica se o item atende aos critérios para reabastecimento.

        Args:
            item: Item do almoxarifado

        Returns:
            True se o item requer reabastecimento
        """
        # Critério 1: Deve ser SUBPRODUTO
        if not hasattr(item, 'tipo_item'):
            return False

        tipo_item_str = item.tipo_item.value if hasattr(item.tipo_item, 'value') else str(item.tipo_item)
        if tipo_item_str != TipoItem.SUBPRODUTO.value:
            return False

        # Critério 2: Deve ter política ESTOCADO
        if not hasattr(item, 'politica_producao'):
            return False

        politica_str = item.politica_producao.value if hasattr(item.politica_producao, 'value') else str(item.politica_producao)
        if politica_str != PoliticaProducao.ESTOCADO.value:
            return False

        # Critério 3: Estoque atual deve estar abaixo do mínimo
        if item.estoque_atual >= item.estoque_min:
            return False

        return True

    def obter_resumo_criticos(self, itens_criticos: List[Dict]) -> Dict:
        """
        Gera resumo estatístico dos itens críticos.

        Args:
            itens_criticos: Lista de itens críticos

        Returns:
            Dicionário com estatísticas
        """
        if not itens_criticos:
            return {
                'total_itens': 0,
                'quantidade_total_reabastecer': 0,
                'deficit_total': 0,
                'mais_critico': None
            }

        return {
            'total_itens': len(itens_criticos),
            'quantidade_total_reabastecer': sum(item['quantidade_reabastecer'] for item in itens_criticos),
            'deficit_total': sum(item['deficit'] for item in itens_criticos),
            'mais_critico': itens_criticos[0] if itens_criticos else None
        }
