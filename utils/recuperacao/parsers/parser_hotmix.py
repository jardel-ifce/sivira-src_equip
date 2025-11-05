"""
Parser para HotMix
==================================================

Extrai ocupações de HotMix do log detalhado.

TODO: Implementar parsing específico para HotMix
"""

from typing import List
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO


class ParserHotMix(ParserBase):
    """
    Parser especializado para HotMix

    TODO: Implementar extração de ocupações
    """

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Extrai ocupações de HotMix do log

        Args:
            log_content: Conteúdo do log do equipamento
            nome_equipamento: Nome do equipamento

        Returns:
            Lista de OcupacaoDTO com as ocupações extraídas
        """
        self.limpar_erros()
        ocupacoes = []

        # TODO: Implementar parsing específico
        self.adicionar_erro("Parser ParserHotMix ainda não implementado")

        return ocupacoes
