"""
Parser para DivisoraDeMassas
==================================================

Extrai ocupações de DivisoraDeMassas do log detalhado.

Formato esperado no log:
🔪 Ordem X | Pedido Y | Atividade Z | Item W | XXXXg | Boleadora: Sim/Não | HH:MM → HH:MM
"""

from typing import List, Optional
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
import re


class ParserDivisora(ParserBase):
    """Parser especializado para DivisoraDeMassas"""

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Extrai ocupações de DivisoraDeMassas do log

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

            # Detectar ocupação: 🔪 Ordem X | ...
            if '🔪' in linha and 'Ordem' in linha:
                ocupacao = self._extrair_ocupacao_divisora(linha, nome_equipamento, data_base)
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_ocupacao_divisora(
        self,
        linha: str,
        nome_equipamento: str,
        data_base: datetime
    ) -> Optional[OcupacaoDTO]:
        """Extrai ocupação de divisora"""
        try:
            # IDs
            ids = self.extrair_ids_ocupacao(linha)
            if not ids:
                return None
            id_ordem, id_pedido, id_atividade, id_item = ids

            # Horários
            horarios = self.extrair_horarios(linha)
            if not horarios:
                return None
            inicio_str, fim_str = horarios

            inicio = self.converter_horario_para_datetime(inicio_str, data_base=data_base)
            fim = self.converter_horario_para_datetime(fim_str, data_base=data_base)
            fim = self.ajustar_data_se_atravessar_meia_noite(inicio, fim)

            # Quantidade em gramas
            quantidade = self.extrair_quantidade_gramas(linha)

            # Boleadora (Sim/Não)
            usa_boleadora = self._extrair_boleadora(linha)

            return OcupacaoDTO(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                inicio=inicio,
                fim=fim,
                nome_equipamento=nome_equipamento,
                tipo_equipamento="DivisoraDeMassas",
                detalhes={
                    "quantidade": quantidade,
                    "usa_boleadora": usa_boleadora
                }
            )

        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de divisora: {e}")
            return None

    def _extrair_boleadora(self, linha: str) -> Optional[bool]:
        """Extrai se usa boleadora do formato: Boleadora: Sim/Não"""
        try:
            match = re.search(r'Boleadora:\s*(Sim|Não|sim|não)', linha, re.IGNORECASE)
            if match:
                valor = match.group(1).lower()
                return valor in ['sim', 'yes', 's']
            return None
        except Exception:
            return None
