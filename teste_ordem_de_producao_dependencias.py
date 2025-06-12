from models.atividades.atividade_modular import AtividadeModular
from parser.carregador_json_atividades import buscar_dados_por_id_atividade
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from utils.gerador_ocupacao import GeradorDeOcupacaoID
from models.ficha_tecnica_modular import FichaTecnicaModular
from enums.tipo_item import TipoItem
from typing import List

class OrdemDeProducao:
    def __init__(self, id_produto: int, quantidade: int):
        self.id_produto = id_produto
        self.quantidade = quantidade
        self.ficha_tecnica_modular = None
        self.atividades_modulares: List[AtividadeModular] = []

    def montar_estrutura(self):
        _, dados_ficha = buscar_ficha_tecnica_por_id(self.id_produto, TipoItem.PRODUTO)
        self.ficha_tecnica_modular = FichaTecnicaModular(
            dados_ficha_tecnica=dados_ficha,
            quantidade_requerida=self.quantidade
        )

    def mostrar_estrutura(self):
        if self.ficha_tecnica_modular:
            self.ficha_tecnica_modular.mostrar_estrutura()

    def criar_atividades_modulares_necessarias(self):
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada.")

        self._criar_atividades_recursivas(self.ficha_tecnica_modular)

    def _criar_atividades_recursivas(self, ficha_modular: FichaTecnicaModular):
        estimativas = ficha_modular.calcular_quantidade_itens()

        for item_dict, quantidade in estimativas:
            tipo = item_dict.get("tipo_item")
            id_ficha = item_dict.get("id_ficha_tecnica")
            id_item = item_dict.get("id_item")
            nome = item_dict.get("nome")

            if tipo == "SUBPRODUTO" and id_ficha:
                # Criação da atividade modular
                try:
                    dados_gerais, _ = buscar_dados_por_id_atividade(id_atividade=id_ficha, tipo_item=TipoItem.SUBPRODUTO)
                except FileNotFoundError:
                    print(f"❌ Atividade para '{nome}' (ID: {id_ficha}) não encontrada.")
                    continue

                atividade = AtividadeModular(
                    id=GeradorDeOcupacaoID().gerar_id(),  # ID único da atividade
                    id_atividade=id_ficha,
                    tipo_item=TipoItem.SUBPRODUTO,
                    quantidade_produto=quantidade
                )

                self.atividades_modulares.append(atividade)

                # Recursão para os filhos da ficha
                _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha, TipoItem.SUBPRODUTO)
                ficha_sub = FichaTecnicaModular(dados_ficha_sub, quantidade)
                self._criar_atividades_recursivas(ficha_sub)

ordem = OrdemDeProducao(id_produto=1, quantidade=1000)
ordem.montar_estrutura()
ordem.mostrar_estrutura()

ordem.criar_atividades_modulares_necessarias()

print("🛠️ Atividades criadas:")
for a in ordem.atividades_modulares:
    print(f"🔹 {a.tipo_item.name} | ID Atividade: {a.id_atividade} | Quantidade: {a.quantidade_produto}")
