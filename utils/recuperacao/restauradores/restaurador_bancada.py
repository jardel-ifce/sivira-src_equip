"""
Restaurador para Bancadas
==========================

Restaura o estado de ocupações de bancadas.
"""

from typing import List
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.bancada import Bancada


class RestauradorBancada(RestauradorBase):
    """
    🪵 Restaurador especializado para Bancadas

    Restaura ocupações nas frações da bancada.

    Estrutura a restaurar no objeto Bancada:
    - fracoes_ocupacoes: List[List[Tuple[int, int, int, int, datetime, datetime]]]
      Formato da tupla: (id_ordem, id_pedido, id_atividade, id_item, inicio, fim)
    """

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: Bancada) -> bool:
        """
        Restaura ocupações na bancada

        Args:
            ocupacoes: Lista de OcupacaoDTO extraídas pelo parser
            equipamento: Objeto Bancada onde o estado será restaurado

        Returns:
            True se restauração foi bem-sucedida, False caso contrário
        """
        self.limpar_erros()

        # Validações
        if not self.validar_tipo_equipamento(equipamento, Bancada):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))

        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                # Obter número da fração
                fracao_numero = ocupacao.obter_detalhe("fracao_numero")
                if fracao_numero is None:
                    self.adicionar_erro(f"Ocupação sem número de fração: {ocupacao}")
                    continue

                # Converter para índice (fração 1 = índice 0)
                fracao_index = fracao_numero - 1

                # Validar índice
                if not self.validar_indice_valido(
                    fracao_index,
                    equipamento.numero_fracoes,
                    "frações de bancada"
                ):
                    continue

                # Criar tupla no formato esperado pela Bancada
                tupla_ocupacao = (
                    ocupacao.id_ordem,
                    ocupacao.id_pedido,
                    ocupacao.id_atividade,
                    ocupacao.id_item,
                    ocupacao.inicio,
                    ocupacao.fim
                )

                # Adicionar à fração correspondente
                equipamento.fracoes_ocupacoes[fracao_index].append(tupla_ocupacao)
                total_restauradas += 1

            except Exception as e:
                erro = f"Erro ao restaurar ocupação {ocupacao}: {e}"
                self.adicionar_erro(erro)
                continue

        # Log de resultado
        if total_restauradas > 0:
            self.log_restauracao_sucesso(equipamento, total_restauradas)
            return True
        else:
            self.log_restauracao_erro(equipamento, "Nenhuma ocupação foi restaurada")
            return False

    def criar_backup_ocupacoes(self, equipamento: Bancada) -> List[List[tuple]]:
        """
        Cria backup das ocupações atuais da bancada

        Args:
            equipamento: Objeto Bancada

        Returns:
            Cópia profunda de fracoes_ocupacoes
        """
        return [fracao[:] for fracao in equipamento.fracoes_ocupacoes]

    def restaurar_backup_ocupacoes(self, equipamento: Bancada, backup: List[List[tuple]]):
        """
        Restaura bancada a partir de backup

        Args:
            equipamento: Objeto Bancada
            backup: Backup criado por criar_backup_ocupacoes
        """
        equipamento.fracoes_ocupacoes = [fracao[:] for fracao in backup]
