from typing import List, Dict
from models.atividades.atividade_modular import AtividadeModular
from parser.carregador_json_atividades import buscar_atividades_por_id_item
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_subproduto_por_nome
from enums.producao.tipo_item import TipoItem
from models.funcionarios.funcionario import Funcionario


class FabricaAtividadesSubproduto:
    @staticmethod
    def criar_atividades(
        subprodutos_agrupados: Dict[str, float],
        ordem_id: int,
        funcionarios_elegiveis: List[Funcionario]
    ) -> List[AtividadeModular]:
        atividades: List[AtividadeModular] = []
        contador_id = 9000  # ID artificial para diferenciar essas atividades

        for nome_subproduto, quantidade in subprodutos_agrupados.items():
            try:
                # Busca ficha técnica para obter id_item e id_ficha_tecnica
                ficha = buscar_ficha_tecnica_subproduto_por_nome(nome_subproduto)
                id_item = ficha["id_item"]

                # Busca as atividades modulares do subproduto
                atividades_dados = buscar_atividades_por_id_item(id_item, TipoItem.SUBPRODUTO)

                for dados_gerais, dados_atividade in atividades_dados:
                    atividade = AtividadeModular(
                        id=contador_id,
                        id_atividade=dados_atividade["id_atividade"],
                        tipo_item=TipoItem.SUBPRODUTO,
                        quantidade_produto=quantidade,
                        ordem_id=ordem_id,
                        pedido_id=None,  # Atividade agrupada, não pertence a 1 pedido específico
                        id_produto=id_item,
                        funcionarios_elegiveis=funcionarios_elegiveis,
                        dados=dados_atividade
                    )
                    atividades.append(atividade)
                    contador_id += 1

            except Exception as e:
                print(f"⚠️ Falha ao criar atividade para subproduto '{nome_subproduto}': {e}")

        return atividades
