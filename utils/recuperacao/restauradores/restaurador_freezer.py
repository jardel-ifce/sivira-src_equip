"""
Restaurador para Freezer
==================================================

Restaura o estado de ocupações de Freezer a partir de logs detalhados.

Estrutura restaurada:
- caixas_ocupacoes: ocupações em caixas individuais
- intervalos_temperatura: intervalos de temperatura aplicados
"""

from typing import List
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.freezer import Freezer


class RestauradorFreezer(RestauradorBase):
    """Restaurador especializado para Freezer"""

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: Freezer) -> bool:
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
        if not self.validar_tipo_equipamento(equipamento, Freezer):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))
        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                caixa_numero = ocupacao.obter_detalhe("caixa_numero")
                temperatura = ocupacao.obter_detalhe("temperatura")
                quantidade = ocupacao.obter_detalhe("quantidade", 0.0)

                # Restaurar em caixa
                if caixa_numero is not None:
                    caixa_index = caixa_numero - 1

                    if not self.validar_indice_valido(
                        caixa_index,
                        equipamento.qtd_caixas,
                        "caixas de freezer"
                    ):
                        continue

                    tupla_ocupacao = (
                        ocupacao.id_ordem,
                        ocupacao.id_pedido,
                        ocupacao.id_atividade,
                        ocupacao.id_item,
                        quantidade,
                        ocupacao.inicio,
                        ocupacao.fim
                    )
                    equipamento.caixas_ocupacoes[caixa_index].append(tupla_ocupacao)

                # Restaurar temperatura
                if temperatura is not None:
                    intervalo_temp = (temperatura, ocupacao.inicio, ocupacao.fim)
                    if intervalo_temp not in equipamento.intervalos_temperatura:
                        equipamento.intervalos_temperatura.append(intervalo_temp)

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
