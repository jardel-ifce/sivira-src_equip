from typing import List, Dict
from models.atividades.pedido_de_producao import PedidoDeProducao
from enums.producao.tipo_item import TipoItem
from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
import logging

logger = logging.getLogger("AgrupadorSubprodutosGlobal")

class AgrupadorSubprodutosGlobal:
    def __init__(self, pedidos: List[PedidoDeProducao]):
        self.pedidos = pedidos

    def somar_todos_os_subprodutos(self) -> Dict[str, float]:
        """
        Agrupa subprodutos SOB_DEMANDA por chave (nome) e soma suas quantidades.
        Retorna: dict[chave: quantidade_total]
        """
        mapa: Dict[str, float] = {}

        for pedido in self.pedidos:
            if not pedido.ficha_tecnica_modular:
                logger.warning(f"Pedido {pedido.id_pedido} ainda não possui ficha técnica montada.")
                continue

            ficha = pedido.ficha_tecnica_modular
            self._agrupar_recursivamente(ficha, mapa)

        return mapa

    def _agrupar_recursivamente(self, ficha: FichaTecnicaModular, mapa: Dict[str, float]):
        for item_dict, quantidade in ficha.calcular_quantidade_itens():
            tipo = item_dict.get("tipo_item")
            politica = item_dict.get("politica_producao")
            chave = item_dict.get("nome")

            if tipo == "SUBPRODUTO" and politica == "SOB_DEMANDA":
                if chave in mapa:
                    mapa[chave] += quantidade
                else:
                    mapa[chave] = quantidade

                id_ficha_sub = item_dict.get("id_ficha_tecnica")
                if id_ficha_sub:
                    from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
                    _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha_sub, TipoItem.SUBPRODUTO)
                    ficha_sub = FichaTecnicaModular(dados_ficha_sub, quantidade)
                    self._agrupar_recursivamente(ficha_sub, mapa)
