from enums.producao.tipo_item import TipoItem
from typing import Dict, List, Tuple, Union
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from datetime import datetime
import logging
logger = logging.getLogger("FichaTecnica")
logger.setLevel(logging.INFO)


class FichaTecnicaModular:
    def __init__(
        self,
        dados_ficha_tecnica: Dict[str, Union[str, int, float, List[Dict]]],
        quantidade_requerida: int
    ):
        self.id = dados_ficha_tecnica["id_ficha_tecnica"]
        self.id_item = dados_ficha_tecnica["id_item"]
        self.nome = dados_ficha_tecnica["nome"]
        self.descricao = dados_ficha_tecnica["descricao"]
        self.tipo_item = TipoItem[dados_ficha_tecnica["tipo_item"]]
        self.unidade_medida = dados_ficha_tecnica["unidade_medida"]
        self.peso_unitario = dados_ficha_tecnica["peso_unitario"]
        self.quantidade_base = dados_ficha_tecnica["quantidade_base"]
        self.perda = dados_ficha_tecnica["perda_percentual"]
        self.politica_producao = dados_ficha_tecnica["politica_producao"]
        self.itens = dados_ficha_tecnica.get("itens", [])
        self.quantidade_requerida = quantidade_requerida

    
    def calcular_quantidade_itens(self) -> List[Tuple[Dict[str, Union[str, int, float]], float]]:
        """
        Estima a quantidade de cada item necessário com base na ficha técnica,
        considerando a quantidade requerida e a perda percentual.
        Arredonda as quantidades para duas casas decimais.
        """
        estimativas = []
        proporcoes = [item["proporcao"] for item in self.itens]
        soma_proporcoes = sum(proporcoes)
        soma_proporcoes_com_perda = soma_proporcoes - self.perda

        for item in self.itens:
            proporcao = item["proporcao"]

            if self.peso_unitario == 0:
                base = (proporcao * self.quantidade_requerida) / soma_proporcoes_com_perda
            else:
                base = (proporcao * self.peso_unitario * self.quantidade_requerida) / soma_proporcoes_com_perda

            quantidade_final = round(base, 2)

            item_enriquecido = item.copy()
            item_enriquecido["politica_producao"] = item.get("politica_producao")

            print(
                f"📦 Item: {item_enriquecido.get('descricao', 'N/D')} | "
                f"ID: {item_enriquecido.get('id_item')} | "
                f"Política: {item_enriquecido.get('politica_producao', 'N/D')}"
            )

            estimativas.append((item_enriquecido, quantidade_final))

        return estimativas



    def mostrar_estrutura(self, nivel: int = 0):
        """
        Mostra a estrutura hierárquica da ficha técnica (produto ou subproduto),
        com indentação e unidades corretamente formatadas.
        """
        prefixo = "│   " * nivel + ("├── " if nivel > 0 else "")
        unidade = self.unidade_medida if self.unidade_medida != "g" else "g"
        print(f"{prefixo}{self.nome} ({self.quantidade_requerida}{unidade})")

        estimativas = self.calcular_quantidade_itens()
        for item_dict, quantidade in estimativas:
            tipo = item_dict.get("tipo_item")
            descricao = item_dict.get("descricao")
            id_ficha = item_dict.get("id_ficha_tecnica")

            if tipo == "SUBPRODUTO" and id_ficha:
                _, dados_ficha_sub = buscar_ficha_tecnica_por_id(
                    id_ficha_tecnica=id_ficha,
                    tipo_item=TipoItem.SUBPRODUTO
                )
                from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
                ficha_sub = FichaTecnicaModular( 
                    dados_ficha_tecnica=dados_ficha_sub,
                    quantidade_requerida=quantidade
                )
                ficha_sub.mostrar_estrutura(nivel + 1)
            else:
                folha = "│   " * (nivel + 1) + "└── "
                print(f"{folha}{descricao} ({quantidade}g)")

    def imprimir_ficha_recursiva(self, nivel=0):
        sufixo = "un" if self.unidade_medida == "un" else "g"
        prefixo = "│   " * nivel + ("├── " if nivel > 0 else "")
        print(f"{prefixo}{self.nome} ({self.quantidade_requerida}{sufixo})")

        estimativas = self.calcular_quantidade_itens()
        for item_dict, quantidade in estimativas:
            descricao = item_dict.get("descricao", "Item sem nome")
            tipo = item_dict.get("tipo_item", "INSUMO")
            id_ficha = item_dict.get("id_ficha_tecnica")

            if tipo == "SUBPRODUTO" and id_ficha:
                _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha, TipoItem.SUBPRODUTO)
                ficha_sub = FichaTecnicaModular(dados_ficha_tecnica=dados_ficha_sub, quantidade_requerida=quantidade)
                ficha_sub.imprimir_ficha_recursiva(nivel + 1)
            else:
                folha = "│   " * (nivel + 1) + "└── "
                print(f"{folha}{descricao} ({quantidade}g)")
