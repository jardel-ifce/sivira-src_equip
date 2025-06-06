import json
import os
from datetime import datetime
from collections import defaultdict

CAMINHO_ARQUIVO = os.path.join("dados", "ocupacoes_ids.json")


class GeradorDeOcupacaoID:
    """
    🔢 Gera e persiste IDs únicos de ocupação por data e equipamento.
    Salva no disco para manter continuidade após reinício.
    """

    _ids_gerados_por_data: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    @classmethod
    def _carregar_do_disco(cls):
        if os.path.exists(CAMINHO_ARQUIVO):
            with open(CAMINHO_ARQUIVO, "r", encoding="utf-8") as f:
                dados = json.load(f)
                for data, equipamentos in dados.items():
                    for nome_equipamento, valor in equipamentos.items():
                        cls._ids_gerados_por_data[data][nome_equipamento] = valor

    @classmethod
    def _salvar_no_disco(cls):
        # Converte defaultdict para dict normal para salvar no JSON
        dados_para_salvar = {
            data: dict(equipamentos)
            for data, equipamentos in cls._ids_gerados_por_data.items()
        }
        os.makedirs(os.path.dirname(CAMINHO_ARQUIVO), exist_ok=True)
        with open(CAMINHO_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(dados_para_salvar, f, indent=4, ensure_ascii=False)

    @classmethod
    def gerar_id(cls, nome_equipamento: str) -> int:
        if not cls._ids_gerados_por_data:  # Carrega apenas na primeira chamada
            cls._carregar_do_disco()

        data_hoje = datetime.now().date().isoformat()
        cls._ids_gerados_por_data[data_hoje][nome_equipamento] += 1
        cls._salvar_no_disco()
        return cls._ids_gerados_por_data[data_hoje][nome_equipamento]
