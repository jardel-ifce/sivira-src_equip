"""
Parser para Batedeira (Industrial e Planetária)
==================================================

Extrai ocupações de Batedeiras do log detalhado.

Formato esperado no log:
🥄 Ordem X | Pedido Y | Atividade Z | Item W | XXXXg | Velocidade: N | HH:MM → HH:MM
"""

from typing import List, Optional
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
import re


class ParserBatedeira(ParserBase):
    """Parser especializado para Batedeiras (Industrial e Planetária)"""

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Extrai ocupações de Batedeira do log

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

            # Detectar ocupação: 🥄 Ordem X | ...
            if '🥄' in linha and 'Ordem' in linha:
                ocupacao = self._extrair_ocupacao_batedeira(linha, nome_equipamento, data_base)
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_ocupacao_batedeira(
        self,
        linha: str,
        nome_equipamento: str,
        data_base: datetime
    ) -> Optional[OcupacaoDTO]:
        """Extrai ocupação de batedeira"""
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
            velocidade = self._extrair_velocidade(linha)

            # Determinar tipo
            tipo_equipamento = "BatedeiraIndustrial" if "Industrial" in nome_equipamento else "BatedeiraPlanetaria"

            return OcupacaoDTO(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                inicio=inicio,
                fim=fim,
                nome_equipamento=nome_equipamento,
                tipo_equipamento=tipo_equipamento,
                detalhes={
                    "quantidade": quantidade,
                    "velocidade": velocidade
                }
            )
        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de batedeira: {e}")
            return None

    def _extrair_velocidade(self, linha: str) -> Optional[int]:
        """Extrai velocidade da ocupação"""
        try:
            match = re.search(r'Velocidade:\s*(\d+)', linha)
            if match:
                return int(match.group(1))
            return None
        except Exception:
            return None
