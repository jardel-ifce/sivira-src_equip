import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

import json
import os

from enums.funcionarios.tipo_profissional import TipoProfissional
from typing import Set


def buscar_tipos_profissionais_por_id_item(id_item: int) -> Set[TipoProfissional]:
    """
    📦 Coleta os tipos únicos de profissionais exigidos nas atividades de um produto
    e de seus subprodutos (se houver), com base no ID do item (produto ou subproduto).

    Args:
        id_item (int): ID do item (produto ou subproduto)

    Returns:
        Set[TipoProfissional]: Conjunto com tipos únicos de profissionais envolvidos
    """
    tipos: Set[TipoProfissional] = set()

    # Caminhos dos arquivos
    caminho_produto = os.path.join("data", "produtos", "atividades_produtos.json")
    caminho_subproduto = os.path.join("data", "subprodutos", "atividades_subprodutos.json")

    # Leitura dos JSONs
    with open(caminho_produto, "r", encoding="utf-8") as f:
        atividades_produtos = json.load(f)

    with open(caminho_subproduto, "r", encoding="utf-8") as f:
        atividades_subprodutos = json.load(f)

    # Criação de mapas por id_item
    mapa_produtos = {item["id_item"]: item for item in atividades_produtos}
    mapa_subprodutos = {item["id_item"]: item for item in atividades_subprodutos}

    # 🔁 Função auxiliar para adicionar tipos de uma lista de atividades
    def adicionar_tipos(atividades: list):
        for atividade in atividades:
            for nome_tipo in atividade.get("tipos_profissionais_permitidos", []):
                if nome_tipo:
                    tipos.add(TipoProfissional[nome_tipo])

    # 🔁 Função recursiva para explorar subprodutos (caso existam)
    def explorar(id_alvo: int):
        if id_alvo in mapa_produtos:
            item = mapa_produtos[id_alvo]
        elif id_alvo in mapa_subprodutos:
            item = mapa_subprodutos[id_alvo]
        else:
            return

        adicionar_tipos(item.get("atividades", []))

        # Busca por subatividades com base no campo "id_macroatividade_produto"
        for atividade in item.get("atividades", []):
            id_sub = atividade.get("id_macroatividade_produto")
            if id_sub and isinstance(id_sub, int):
                explorar(id_sub)

    # 🧭 Início da exploração
    explorar(id_item)

    return tipos


# 🎯 Teste rápido
if __name__ == "__main__":
    tipos = buscar_tipos_profissionais_por_id_item(1)  # ID do produto ou subproduto
    print("=== Tipos Profissionais Únicos ===")
    for tipo in sorted(tipos, key=lambda t: t.name):
        print(f"✔️ {tipo.name}")
