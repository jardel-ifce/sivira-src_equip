"""
Restaurador para DivisoraDeMassas
==================================================

Restaura o estado de ocupações de DivisoraDeMassas a partir de logs detalhados.

Estrutura restaurada:
- ocupacoes: tuplas com (id_ordem, id_pedido, id_atividade, id_item, quantidade, usa_boleadora, inicio, fim)
"""

from typing import List
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.divisora_de_massas import DivisoraDeMassas


class RestauradorDivisora(RestauradorBase):
    """Restaurador especializado para DivisoraDeMassas"""

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: DivisoraDeMassas) -> bool:
        """
        Restaura ocupações no equipamento

        Args:
            ocupacoes: Lista de OcupacaoDTO extraídas pelo parser
            equipamento: Objeto onde o estado será restaurado

        Returns:
            True se restauração foi bem-sucedida, False caso contrário
        """
        self.limpar_erros()

        # Validações
        if not self.validar_tipo_equipamento(equipamento, DivisoraDeMassas):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))
        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                quantidade = ocupacao.obter_detalhe("quantidade", 0.0)
                usa_boleadora = ocupacao.obter_detalhe("usa_boleadora")

                # Tupla para divisora: (id_ordem, id_pedido, id_atividade, id_item, quantidade, usa_boleadora, inicio, fim)
                tupla_ocupacao = (
                    ocupacao.id_ordem,
                    ocupacao.id_pedido,
                    ocupacao.id_atividade,
                    ocupacao.id_item,
                    quantidade,
                    usa_boleadora,
                    ocupacao.inicio,
                    ocupacao.fim
                )

                equipamento.ocupacoes.append(tupla_ocupacao)
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
