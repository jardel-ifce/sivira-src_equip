"""
Restaurador para Armarios (Esqueleto e Fermentador)
==================================================

Restaura o estado de ocupações de Armarios a partir de logs detalhados.

Estrutura restaurada:
- niveis_ocupacoes: lista de listas com tuplas (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
"""

from typing import List, Union
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.armario_esqueleto import ArmarioEsqueleto
from models.equipamentos.armario_fermentador import ArmarioFermentador


class RestauradorArmario(RestauradorBase):
    """Restaurador especializado para Armarios (Esqueleto e Fermentador)"""

    def restaurar(
        self,
        ocupacoes: List[OcupacaoDTO],
        equipamento: Union[ArmarioEsqueleto, ArmarioFermentador]
    ) -> bool:
        """
        Restaura ocupações no equipamento

        Args:
            ocupacoes: Lista de OcupacaoDTO extraídas pelo parser
            equipamento: Objeto onde o estado será restaurado

        Returns:
            True se restauração foi bem-sucedida, False caso contrário
        """
        self.limpar_erros()

        # Validações (aceita ambos os tipos de armário)
        if not isinstance(equipamento, (ArmarioEsqueleto, ArmarioFermentador)):
            self.adicionar_erro(f"Tipo de equipamento inválido: {type(equipamento).__name__}")
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))
        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                andar = ocupacao.obter_detalhe("andar")
                nivel = ocupacao.obter_detalhe("nivel")
                quantidade = ocupacao.obter_detalhe("quantidade", 0.0)

                if andar is None or nivel is None:
                    self.adicionar_erro(f"Ocupação sem andar/nível: {ocupacao}")
                    continue

                # Calcular índice do nível
                nivel_index = equipamento.obter_indice_por_andar_e_nivel(andar, nivel)

                if nivel_index < 0:
                    self.adicionar_erro(f"Índice inválido para andar {andar}, nível {nivel}")
                    continue

                if not self.validar_indice_valido(
                    nivel_index,
                    equipamento.total_niveis_tela,
                    "níveis de armário"
                ):
                    continue

                # Tupla para armário: (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
                tupla_ocupacao = (
                    ocupacao.id_ordem,
                    ocupacao.id_pedido,
                    ocupacao.id_atividade,
                    ocupacao.id_item,
                    quantidade,
                    ocupacao.inicio,
                    ocupacao.fim
                )

                equipamento.niveis_ocupacoes[nivel_index].append(tupla_ocupacao)
                total_restauradas += 1

            except Exception as e:
                self.adicionar_erro(f"Erro ao restaurar ocupação {ocupacao}: {e}")
                continue

        if total_restauradas > 0:
            self.log_restauracao_sucesso(equipamento, total_restauradas)
            return True
        else:
            self.log_restauracao_erro(equipamento, "Nenhuma ocupação foi restaurada")
            return False
