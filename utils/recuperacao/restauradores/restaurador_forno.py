"""
Restaurador para Forno
==================================================

Restaura o estado de ocupações de Forno.

TODO: Implementar restauração específica para Forno
"""

from typing import List
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.forno import Forno


class RestauradorForno(RestauradorBase):
    """
    Restaurador especializado para Forno

    TODO: Implementar restauração de ocupações
    """

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: Forno) -> bool:
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
        if not self.validar_tipo_equipamento(equipamento, Forno):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        # TODO: Implementar restauração específica
        self.adicionar_erro("Restaurador RestauradorForno ainda não implementado")

        return False
