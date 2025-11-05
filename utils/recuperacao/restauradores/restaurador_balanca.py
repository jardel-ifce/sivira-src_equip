"""
Restaurador para BalancaDigital
==================================================

Restaura o estado de ocupações de BalancaDigital a partir de logs detalhados.

Estrutura restaurada:
- ocupacoes: tuplas com (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
"""

from typing import List
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.balanca_digital import BalancaDigital


class RestauradorBalanca(RestauradorBase):
    """Restaurador especializado para BalancaDigital"""

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: BalancaDigital) -> bool:
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
        if not self.validar_tipo_equipamento(equipamento, BalancaDigital):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))
        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                quantidade = ocupacao.obter_detalhe("quantidade", 0.0)

                # Tupla para balança: (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
                tupla_ocupacao = (
                    ocupacao.id_ordem,
                    ocupacao.id_pedido,
                    ocupacao.id_atividade,
                    ocupacao.id_item,
                    quantidade,
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
