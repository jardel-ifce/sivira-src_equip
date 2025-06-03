import json
from pathlib import Path
from typing import List, Dict, Any


class ParserAtividadeModular:
    """
    📄 Classe responsável por ler um arquivo JSON de definição de atividade e gerar uma estrutura interpretável.
    """

    def __init__(self, caminho_arquivo: str):
        self.caminho = Path(caminho_arquivo)
        self.dados: Dict[str, Any] = {}

    def carregar_json(self):
        if not self.caminho.exists():
            raise FileNotFoundError(f"❌ Arquivo JSON não encontrado: {self.caminho}")
        with open(self.caminho, 'r', encoding='utf-8') as f:
            self.dados = json.load(f)
        print(f"✅ JSON carregado com sucesso de: {self.caminho}")

    def validar_campos(self):
        campos_obrigatorios = [
            "id_atividade",
            "nome_logger",
            "descricao",
            "tipo_ocupacao",
            "equipamentos",
            "duracao_por_faixa"
        ]
        for campo in campos_obrigatorios:
            if campo not in self.dados:
                raise ValueError(f"❌ Campo obrigatório '{campo}' ausente no JSON.")

    def get_id(self) -> str:
        return self.dados["id_atividade"]

    def get_logger_nome(self) -> str:
        return self.dados["nome_logger"]

    def get_descricao(self) -> str:
        return self.dados["descricao"]

    def get_tipo_ocupacao(self) -> str:
        return self.dados["tipo_ocupacao"]

    def get_equipamentos(self) -> List[Dict[str, Any]]:
        return self.dados["equipamentos"]

    def get_duracoes(self) -> List[Dict[str, Any]]:
        return self.dados["duracao_por_faixa"]
