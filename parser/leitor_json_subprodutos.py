import json
import os
from typing import Dict, Any, Tuple
from utils.logger_factory import setup_logger

logger = setup_logger("LeitorSubprodutos")

# ==========================================================
# 📥 Leitura segura dos dados do JSON de subprodutos
# ==========================================================
CAMINHO_JSON = os.path.join("jsons", "subprodutos.json")

try:
    with open(CAMINHO_JSON, "r", encoding="utf-8") as f:
        conteudo = f.read()
        if not conteudo.strip():
            raise ValueError("❌ Arquivo JSON está vazio.")
        DADOS_ATIVIDADES = json.loads(conteudo)
        logger.info(f"✅ Dados de atividades carregados com sucesso ({len(DADOS_ATIVIDADES)} produtos)")
except FileNotFoundError:
    raise FileNotFoundError(f"❌ Arquivo não encontrado: {CAMINHO_JSON}")
except json.JSONDecodeError as e:
    raise ValueError(f"❌ Erro ao decodificar JSON: {e}")

# ==========================================================
# 🔎 Busca dados da atividade por ID
# ==========================================================
def buscar_dados_por_id_atividade(id_atividade: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    for produto in DADOS_ATIVIDADES:
        for atividade in produto.get("atividades", []):
            if atividade.get("id_atividade") == id_atividade:
                logger.info(f"🔍 Atividade {id_atividade} encontrada no produto '{produto.get('nome_produto')}'")
                return produto, atividade
    raise ValueError(f"❌ Atividade com id_atividade={id_atividade} não encontrada.")
