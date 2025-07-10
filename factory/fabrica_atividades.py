import importlib
from pathlib import Path
from parser.parser_json_atividade import ParserAtividadeModular
from models.atividade_generica import AtividadeGenerica
from enums.tipo_atividade import TipoAtividade
from enums.funcionarios.tipo_profissional import TipoProfissional
from typing import Optional
import inflect

# p = inflect.engine()  # opcional se quiser pluralizar/despluralizar

class FabricaDeAtividades:
    """
    🏭 Fábrica que cria instâncias de atividades com base em arquivos JSON.
    """

    def __init__(self, caminho_json: str):
        self.parser = ParserAtividadeModular(caminho_json)
        self.parser.carregar_json()
        self.parser.validar_campos()
        self.definicao = self.parser.dados

    def criar_atividade(
        self,
        id: int,
        tipo_atividade: Optional[TipoAtividade],
        tipos_profissionais: list,
        quantidade_funcionarios: int,
        equipamentos_elegiveis: list,
        fips_equipamentos: dict,
        quantidade_produto: float
    ):
        nome_classe = self._converter_id_para_nome_classe(self.definicao["id_atividade"])
        modulo_path = f"models.atividades.{self.definicao['id_atividade']}"  # precisa bater com a pasta

        try:
            modulo = importlib.import_module(modulo_path)
            classe = getattr(modulo, nome_classe)
            print(f"✅ Usando classe concreta: {nome_classe}")
            return classe(
                id=id,
                tipo_atividade=tipo_atividade,
                tipos_profissionais_permitidos=tipos_profissionais,
                quantidade_funcionarios=quantidade_funcionarios,
                equipamentos_elegiveis=equipamentos_elegiveis,
                quantidade_produto=quantidade_produto,
                fips_equipamentos=fips_equipamentos
            )
        except (ModuleNotFoundError, AttributeError):
            print(f"⚠️ Classe concreta '{nome_classe}' não encontrada. Usando AtividadeGenerica.")
            return AtividadeGenerica(
                definicao_json=self.definicao,
                id=id,
                tipo_atividade=tipo_atividade,
                tipos_profissionais_permitidos=tipos_profissionais,
                quantidade_funcionarios=quantidade_funcionarios,
                equipamentos_elegiveis=equipamentos_elegiveis,
                quantidade_produto=quantidade_produto,
                fips_equipamentos=fips_equipamentos
            )

    def _converter_id_para_nome_classe(self, id_str: str) -> str:
        # exemplo: "preparo_armazenamento_creme_lula" → "PreparoArmazenamentoCremeLula"
        partes = id_str.strip().split("_")
        return "".join(p.capitalize() for p in partes)
