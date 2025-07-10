from datetime import datetime
from typing import List, Dict, Union
from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
from enums.producao.tipo_item import TipoItem
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from parser.gerenciador_json_comandas import salvar_comanda_em_json


def gerar_comanda_reserva(
    ordem_id: int,
    pedido_id: int,
    ficha: FichaTecnicaModular,
    gestor,
    data_execucao: datetime
) -> None:
    """
    🧾 Gera a comanda completa a partir da ficha técnica, incluindo o item principal a ser produzido,
    com seus subprodutos e insumos recursivamente aninhados.
    """
    produto_dict = {
        "id_item": ficha.id_item,
        "nome": ficha.descricao,
        "politica_producao": ficha.politica_producao,
        "quantidade_necessaria": ficha.quantidade_requerida,
        "itens_necessarios": _montar_itens_para_comanda_recursivo(
            ficha,
            gestor,
            data_execucao,
            ordem_id,
            pedido_id
        )
    }

    salvar_comanda_em_json(
        ordem_id=ordem_id,
        pedido_id=pedido_id,
        data_reserva=data_execucao,
        itens=[produto_dict]
    )


def _montar_itens_para_comanda_recursivo(
    ficha: FichaTecnicaModular,
    gestor,
    data_execucao: datetime,
    ordem_id: int,
    pedido_id: int
) -> List[Dict[str, Union[int, str, float, List]]]:
    """
    🔁 Monta recursivamente os itens a serem reservados (subprodutos e insumos).
    - SUBPRODUTOS SOB_DEMANDA → expandem para insumos
    - SUBPRODUTOS ESTOCADOS → não expandem
    """
    itens_formatados = []
    estimativas = ficha.calcular_quantidade_itens()

    for item_dict, quantidade in estimativas:
        tipo_item = item_dict["tipo_item"]
        politica = item_dict.get("politica_producao")
        id_item = item_dict["id_item"]
        nome = item_dict["descricao"]
        id_ficha = item_dict.get("id_ficha_tecnica")

        item = gestor.almoxarifado.buscar_por_id(id_item)
        unidade = item.unidade_medida.value if item else "GRAMAS"

        if tipo_item == "SUBPRODUTO":
            subproduto_dict = {
                "id_item": id_item,
                "nome": nome,
                "politica_producao": politica,
                "quantidade_necessaria": round(quantidade, 2)
            }

            if politica == "SOB_DEMANDA" and id_ficha:
                _, dados_ficha_sub = buscar_ficha_tecnica_por_id(
                    id_ficha_tecnica=id_ficha,
                    tipo_item=TipoItem.SUBPRODUTO
                )
                ficha_sub = FichaTecnicaModular(
                    dados_ficha_tecnica=dados_ficha_sub,
                    quantidade_requerida=quantidade
                )
                sub_itens = _montar_itens_para_comanda_recursivo(
                    ficha_sub,
                    gestor,
                    data_execucao,
                    ordem_id,
                    pedido_id
                )
                subproduto_dict["itens_necessarios"] = sub_itens

            itens_formatados.append(subproduto_dict)

        elif tipo_item == "INSUMO":
            insumo_dict = {
                "id_item": id_item,
                "nome": nome,
                "quantidade_necessaria": round(quantidade, 2),
                "unidade_medida": unidade,
                "tipo_item": tipo_item
            }

            if politica:
                insumo_dict["politica_producao"] = politica

            itens_formatados.append(insumo_dict)

    return itens_formatados
