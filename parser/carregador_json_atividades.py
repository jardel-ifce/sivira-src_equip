import json
import os
from enums.producao.tipo_item import TipoItem
from typing import Dict, Any, Tuple, List
from utils.logs.logger_factory import setup_logger

logger = setup_logger("CarregadorAtividades")

# ==========================================================
# 📦 Mapeamento de TipoItem → nome da pasta/arquivo (plural)
# ==========================================================
MAPA_CAMINHO = {
    TipoItem.PRODUTO: "produtos",
    TipoItem.SUBPRODUTO: "subprodutos"
}

# ==========================================================
# 📅 Busca por ID da Atividade (específica)
# ==========================================================
def buscar_dados_por_id_atividade(id_atividade: int, tipo_item: TipoItem) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if tipo_item not in MAPA_CAMINHO:
        raise ValueError(f"❌ TipoItem '{tipo_item.name}' não suportado.")

    nome_pasta = MAPA_CAMINHO[tipo_item]
    nome_arquivo = f"atividades_{nome_pasta}.json"
    caminho = os.path.join("data", nome_pasta, nome_arquivo)

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
            if not conteudo.strip():
                raise ValueError(f"❌ Arquivo {nome_arquivo} está vazio.")
            dados = json.loads(conteudo)
            # logger.info(f"✅ Arquivo '{nome_arquivo}' carregado com {len(dados)} produtos/subprodutos.")
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Arquivo não encontrado: {caminho}")
    except json.JSONDecodeError as e:
        raise ValueError(f"❌ Erro ao decodificar JSON: {e}")

    for item in dados:
        for atividade in item.get("atividades", []):
            if atividade.get("id_atividade") == id_atividade:
                # logger.info(f"🔍 Atividade {id_atividade} encontrada no '{item.get('nome')}'")
                item["nome_item"] = item.get("nome", "item_desconhecido")
                item["nome_atividade"] = atividade.get("nome", f"Atividade {id_atividade}")
                return item, atividade

    raise ValueError(f"❌ Atividade com id_atividade={id_atividade} não encontrada em {nome_arquivo}.")

# ==========================================================
# 📅 Busca todas as atividades por ID de Produto ou Subproduto
# ==========================================================
def buscar_dados_por_id_produto_ou_subproduto(id_produto_ou_subproduto: int, tipo_item: TipoItem) -> Dict[str, Any]:
    if tipo_item not in MAPA_CAMINHO:
        raise ValueError(f"❌ TipoItem '{tipo_item.name}' não suportado.")

    nome_pasta = MAPA_CAMINHO[tipo_item]
    nome_arquivo = f"atividades_{nome_pasta}.json"
    caminho = os.path.join("data", nome_pasta, nome_arquivo)

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
            if not conteudo.strip():
                raise ValueError(f"❌ Arquivo {nome_arquivo} está vazio.")
            dados = json.loads(conteudo)
            logger.info(f"✅ Arquivo '{nome_arquivo}' carregado com {len(dados)} produtos/subprodutos.")
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Arquivo não encontrado: {caminho}")
    except json.JSONDecodeError as e:
        raise ValueError(f"❌ Erro ao decodificar JSON: {e}")

    for item in dados:
        if item.get("id_item") == id_produto_ou_subproduto:
            # logger.info(f"🔍 Produto/Subproduto com id_item={id_produto_ou_subproduto} encontrado: '{item.get('nome')}'")
            return item

    raise ValueError(f"❌ Produto/Subproduto com id_item={id_produto_ou_subproduto} não encontrado em {nome_arquivo}.")

# def buscar_atividades_por_id_item(id_item: int, tipo_item: TipoItem) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
#     """
#     🔎 Retorna todas as atividades associadas ao id_item (subproduto ou produto).
#     """
#     if tipo_item not in MAPA_CAMINHO:
#         raise ValueError(f"❌ TipoItem '{tipo_item.name}' não suportado.")

#     nome_pasta = MAPA_CAMINHO[tipo_item]
#     caminho = os.path.join("data", nome_pasta, f"atividades_{nome_pasta}.json")

#     with open(caminho, encoding="utf-8") as f:
#         dados_json = json.load(f)

#     for entrada in dados_json:
#         if entrada["id_item"] == id_item:
#             atividades = entrada.get("atividades", [])
#             # logger.info(f"🔎 {len(atividades)} atividades encontradas para item {entrada['nome']}")
#             return [(entrada, atividade) for atividade in atividades]

#     raise ValueError(f"❌ Nenhuma atividade encontrada para id_item={id_item} em {caminho}")
def buscar_atividades_por_id_item(id_item: int, tipo_item: TipoItem) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    🔎 Retorna todas as atividades associadas ao id_item (subproduto ou produto).
    Agora exibe o caminho de busca e as atividades encontradas.
    """
    if tipo_item not in MAPA_CAMINHO:
        raise ValueError(f"❌ TipoItem '{tipo_item.name}' não suportado.")

    nome_pasta = MAPA_CAMINHO[tipo_item]
    caminho = os.path.join("data", nome_pasta, f"atividades_{nome_pasta}.json")

    print(f"📂 Buscando atividades em: {caminho}")

    with open(caminho, encoding="utf-8") as f:
        dados_json = json.load(f)

    for entrada in dados_json:
        if int(entrada["id_item"]) == int(id_item):
            atividades = entrada.get("atividades", [])
            print(f"✅ {len(atividades)} atividades encontradas para item '{entrada.get('nome')}' (ID: {id_item}):")
            for a in atividades:
                print(f"   🔹 ID: {a.get('id_atividade')} | Nome: {a.get('nome')}")
            resultado = [(entrada, atividade) for atividade in atividades]
            print(f"📦 Total de atividades retornadas: {len(resultado)}")
            return resultado

    raise ValueError(f"❌ Nenhuma atividade encontrada para id_item={id_item} em {caminho}")