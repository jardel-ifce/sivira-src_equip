"""
Parser para BalancaDigital
==================================================

Extrai ocupações de BalancaDigital do log detalhado.

Formato esperado no log:
⚖️ Ordem: X | Pedido: Y | Atividade: Z | Item: W | Quantidade: XXXXg | Início: HH:MM | Fim: HH:MM
"""

from typing import List, Optional
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
import re


class ParserBalanca(ParserBase):
    """Parser especializado para BalancaDigital"""

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Extrai ocupações de BalancaDigital do log

        Args:
            log_content: Conteúdo do log do equipamento
            nome_equipamento: Nome do equipamento

        Returns:
            Lista de OcupacaoDTO com as ocupações extraídas
        """
        self.limpar_erros()
        ocupacoes = []

        linhas = log_content.split('\n')
        data_base = datetime.now()

        for linha in linhas:
            linha = linha.strip()

            # Detectar ocupação: ⚖️ Ordem: X | ...
            if '⚖️' in linha and 'Ordem' in linha:
                ocupacao = self._extrair_ocupacao_balanca(linha, nome_equipamento, data_base)
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_ocupacao_balanca(
        self,
        linha: str,
        nome_equipamento: str,
        data_base: datetime
    ) -> Optional[OcupacaoDTO]:
        """Extrai ocupação de balança"""
        try:
            # IDs
            ids = self._extrair_ids_balanca(linha)
            if not ids:
                return None
            id_ordem, id_pedido, id_atividade, id_item = ids

            # Horários (formato "Início: HH:MM | Fim: HH:MM")
            horarios = self._extrair_horarios_balanca(linha)
            if not horarios:
                return None
            inicio_str, fim_str = horarios

            inicio = self.converter_horario_para_datetime(inicio_str, data_base=data_base)
            fim = self.converter_horario_para_datetime(fim_str, data_base=data_base)
            fim = self.ajustar_data_se_atravessar_meia_noite(inicio, fim)

            # Quantidade em gramas
            quantidade = self.extrair_quantidade_gramas(linha)

            return OcupacaoDTO(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                inicio=inicio,
                fim=fim,
                nome_equipamento=nome_equipamento,
                tipo_equipamento="BalancaDigital",
                detalhes={
                    "quantidade": quantidade
                }
            )

        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de balança: {e}")
            return None

    def _extrair_ids_balanca(self, linha: str) -> Optional[tuple]:
        """Extrai IDs no formato: Ordem: X | Pedido: Y | Atividade: Z | Item: W"""
        try:
            match = re.search(
                r'Ordem:\s*(\d+)\s*\|\s*Pedido:\s*(\d+)\s*\|\s*Atividade:\s*(\d+)\s*\|\s*Item:\s*(\d+)',
                linha
            )
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)))
            return None
        except Exception:
            return None

    def _extrair_horarios_balanca(self, linha: str) -> Optional[tuple]:
        """Extrai horários no formato: Início: YYYY-MM-DD HH:MM | Fim: YYYY-MM-DD HH:MM ou Início: HH:MM | Fim: HH:MM"""
        try:
            # Tentar formato com data completa primeiro (YYYY-MM-DD HH:MM)
            match = re.search(r'Início:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*\|\s*Fim:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', linha)
            if match:
                return (match.group(1), match.group(2))

            # Formato antigo (HH:MM) - retrocompatibilidade
            match = re.search(r'Início:\s*(\d{2}:\d{2})\s*\|\s*Fim:\s*(\d{2}:\d{2})', linha)
            if match:
                return (match.group(1), match.group(2))

            return None
        except Exception:
            return None
