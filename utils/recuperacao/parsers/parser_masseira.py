"""
Parser para Masseira
==================================================

Extrai ocupações de Masseira do log detalhado.

Formato esperado no log:
🥣 Ordem X | Pedido Y | Atividade Z | Item W | XXXXg | HH:MM → HH:MM | Velocidades: ALTA, MEDIA | Mistura: RAPIDA
"""

from typing import List, Optional
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
import re


class ParserMasseira(ParserBase):
    """Parser especializado para Masseira"""

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Extrai ocupações de Masseira do log

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

            # Detectar ocupação: 🥣 Ordem X | Pedido Y | ...
            if '🥣' in linha and 'Ordem' in linha:
                ocupacao = self._extrair_ocupacao_masseira(linha, nome_equipamento, data_base)
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_ocupacao_masseira(
        self,
        linha: str,
        nome_equipamento: str,
        data_base: datetime
    ) -> Optional[OcupacaoDTO]:
        """Extrai ocupação de masseira"""
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

            # Velocidades (podem ser múltiplas)
            velocidades = self._extrair_velocidades(linha)

            # Tipo de mistura
            tipo_mistura = self._extrair_tipo_mistura(linha)

            return OcupacaoDTO(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                inicio=inicio,
                fim=fim,
                nome_equipamento=nome_equipamento,
                tipo_equipamento="Masseira",
                detalhes={
                    "quantidade": quantidade,
                    "velocidades": velocidades,
                    "tipo_mistura": tipo_mistura
                }
            )

        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de masseira: {e}")
            return None

    def _extrair_velocidades(self, linha: str) -> Optional[List[str]]:
        """Extrai velocidades da ocupação"""
        try:
            match = re.search(r'Velocidades?:\s*([A-Z_,\s]+?)(?:\s*\||\s*$)', linha)
            if match:
                velocidades_str = match.group(1).strip()
                # Separar por vírgula e limpar
                velocidades = [v.strip() for v in velocidades_str.split(',') if v.strip()]
                return velocidades if velocidades else None
            return None
        except Exception:
            return None

    def _extrair_tipo_mistura(self, linha: str) -> Optional[str]:
        """Extrai tipo de mistura da ocupação"""
        try:
            match = re.search(r'Mistura:\s*([A-Z_]+)', linha)
            if match:
                return match.group(1).strip()
            return None
        except Exception:
            return None
