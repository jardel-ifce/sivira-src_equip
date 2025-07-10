import json
import os
from enums.producao.tipo_item import TipoItem
from typing import Dict, Any, Tuple
from utils.logs.logger_factory import setup_logger

logger = setup_logger("CarregadorFichaTecnica")

# ==========================================================
# 📦 Mapeamento de TipoItem → nome da pasta/arquivo (plural)
# ==========================================================
MAPA_CAMINHO = {
    TipoItem.PRODUTO: "produtos",
    TipoItem.SUBPRODUTO: "subprodutos"
}

# ===============================================
# 📦 Leitura e carregamento de fichas técnicas
# ===============================================
def buscar_ficha_tecnica_por_id(id_ficha_tecnica: int, tipo_item: TipoItem) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Carrega a ficha técnica correspondente a um tipo de item (PRODUTO ou SUBPRODUTO)
    a partir de um arquivo JSON nomeado conforme o tipo.
    Retorna uma tupla: (item_completo, ficha_tecnica_do_item)
    """
    if tipo_item not in MAPA_CAMINHO:
        raise ValueError(f"❌ TipoItem '{tipo_item.name}' não suportado.")

    nome_pasta = MAPA_CAMINHO[tipo_item]
    nome_arquivo = f"fichas_tecnicas_{nome_pasta}.json"
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
        if id_ficha_tecnica == item.get("id_ficha_tecnica"):
            # logger.info(f"🔍 Ficha técnica {id_ficha_tecnica} encontrada no '{item.get('nome')}'")
            return item, item  # Retorna duas vezes o item (nome + ficha técnica)

    raise ValueError(f"❌ Ficha técnica com id_ficha_tecnica={id_ficha_tecnica} não encontrada em {nome_arquivo}.")
