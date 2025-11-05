"""
Parser para Fogao
==================================================

Extrai ocupações de Fogao do log detalhado.

Formato esperado no log:
🔹 Boca X:
   🔥 Ordem A | Pedido B | Atividade C | Item D | XXXXg | Chama: TIPO | Pressões: [P1, P2] | HH:MM → HH:MM
"""

from typing import List, Optional
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
import re


class ParserFogao(ParserBase):
    """Parser especializado para Fogao"""

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Extrai ocupações de Fogao do log

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
        boca_atual = None

        for linha in linhas:
            linha = linha.strip()

            # Detectar boca: 🔹 Boca X:
            if '🔹 Boca' in linha:
                boca_atual = self._extrair_numero_boca(linha)
                continue

            # Detectar ocupação: 🔥 Ordem X | ...
            if '🔥' in linha and 'Ordem' in linha and boca_atual is not None:
                ocupacao = self._extrair_ocupacao_fogao(linha, boca_atual, nome_equipamento, data_base)
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_numero_boca(self, linha: str) -> Optional[int]:
        """Extrai número da boca"""
        try:
            match = re.search(r'Boca\s+(\d+)', linha)
            if match:
                return int(match.group(1))
            return None
        except Exception:
            return None

    def _extrair_ocupacao_fogao(
        self,
        linha: str,
        boca: int,
        nome_equipamento: str,
        data_base: datetime
    ) -> Optional[OcupacaoDTO]:
        """Extrai ocupação de fogão"""
        try:
            ids = self.extrair_ids_ocupacao(linha)
            if not ids:
                return None
            id_ordem, id_pedido, id_atividade, id_item = ids

            horarios = self.extrair_horarios(linha)
            if not horarios:
                return None
            inicio_str, fim_str = horarios

            inicio = self.converter_horario_para_datetime(inicio_str, data_base=data_base)
            fim = self.converter_horario_para_datetime(fim_str, data_base=data_base)
            fim = self.ajustar_data_se_atravessar_meia_noite(inicio, fim)

            quantidade = self.extrair_quantidade_gramas(linha)
            tipo_chama, pressoes = self._extrair_chama_pressoes(linha)

            return OcupacaoDTO(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                inicio=inicio,
                fim=fim,
                nome_equipamento=nome_equipamento,
                tipo_equipamento="Fogao",
                detalhes={
                    "boca": boca,
                    "quantidade": quantidade,
                    "tipo_chama": tipo_chama,
                    "pressoes": pressoes
                }
            )
        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de fogão: {e}")
            return None

    def _extrair_chama_pressoes(self, linha: str) -> tuple:
        """Extrai tipo de chama e pressões"""
        tipo_chama = None
        pressoes = []

        try:
            match = re.search(r'Chama:\s*([A-Z_]+)', linha)
            if match:
                tipo_chama = match.group(1)

            match = re.search(r'Pressões?:\s*\[([^\]]+)\]', linha)
            if match:
                pressoes_str = match.group(1)
                pressoes = [p.strip() for p in pressoes_str.split(',')]
        except Exception:
            pass

        return tipo_chama, pressoes
