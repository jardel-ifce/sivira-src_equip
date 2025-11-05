"""
Restaurador para Batedeiras (Industrial e Planetária)
==================================================

Restaura o estado de ocupações de Batedeiras a partir de logs detalhados.

Estrutura restaurada:
- ocupacoes: tuplas com (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidade, inicio, fim)
"""

from typing import List, Union
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.batedeira_industrial import BatedeiraIndustrial
from models.equipamentos.batedeira_planetaria import BatedeiraPlanetaria


class RestauradorBatedeira(RestauradorBase):
    """Restaurador especializado para Batedeiras (Industrial e Planetária)"""

    def restaurar(
        self,
        ocupacoes: List[OcupacaoDTO],
        equipamento: Union[BatedeiraIndustrial, BatedeiraPlanetaria]
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

        # Validações (aceita ambos os tipos de batedeira)
        if not isinstance(equipamento, (BatedeiraIndustrial, BatedeiraPlanetaria)):
            self.adicionar_erro(f"Tipo de equipamento inválido: {type(equipamento).__name__}")
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))
        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                quantidade = ocupacao.obter_detalhe("quantidade", 0.0)
                velocidade = ocupacao.obter_detalhe("velocidade", 0)

                # Tupla para batedeira: (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidade, inicio, fim)
                tupla_ocupacao = (
                    ocupacao.id_ordem,
                    ocupacao.id_pedido,
                    ocupacao.id_atividade,
                    ocupacao.id_item,
                    quantidade,
                    velocidade,
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
