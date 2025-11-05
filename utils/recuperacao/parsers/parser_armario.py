"""
Parser para Armario (Esqueleto e Fermentador)
==================================================

Extrai ocupações de Armarios do log detalhado.

Formato esperado no log:
🔹 Andar X, Nível Y (índice Z):
   🗂️ Ordem A | Pedido B | Atividade C | Item D | XX.XX unidades/gramas | HH:MM → HH:MM
"""

from typing import List, Optional
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
import re


class ParserArmario(ParserBase):
    """Parser especializado para Armarios (Esqueleto e Fermentador)"""

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Extrai ocupações de Armario do log

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
        andar_atual = None
        nivel_atual = None

        for linha in linhas:
            linha = linha.strip()

            # Detectar andar e nível: 🔹 Andar X, Nível Y (índice Z):
            if '🔹 Andar' in linha:
                andar_nivel = self._extrair_andar_nivel(linha)
                if andar_nivel:
                    andar_atual, nivel_atual = andar_nivel
                continue

            # Detectar ocupação: 🗂️ Ordem X | ...
            if '🗂️' in linha and andar_atual is not None and nivel_atual is not None:
                ocupacao = self._extrair_ocupacao_armario(
                    linha, andar_atual, nivel_atual, nome_equipamento, data_base
                )
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_andar_nivel(self, linha: str) -> Optional[tuple]:
        """Extrai andar e nível do formato: 🔹 Andar X, Nível Y (índice Z):"""
        try:
            match = re.search(r'Andar\s+(\d+),\s*Nível\s+(\d+)', linha)
            if match:
                andar = int(match.group(1))
                nivel = int(match.group(2))
                return (andar, nivel)
            return None
        except Exception:
            return None

    def _extrair_ocupacao_armario(
        self,
        linha: str,
        andar: int,
        nivel: int,
        nome_equipamento: str,
        data_base: datetime
    ) -> Optional[OcupacaoDTO]:
        """Extrai ocupação de armário"""
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

            # Quantidade (pode ser em unidades ou gramas)
            quantidade = self._extrair_quantidade_armario(linha)

            # Determinar tipo de equipamento
            tipo_equipamento = "ArmarioEsqueleto" if "Esqueleto" in nome_equipamento else "ArmarioFermentador"

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
                    "andar": andar,
                    "nivel": nivel,
                    "quantidade": quantidade
                }
            )

        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de armário: {e}")
            return None

    def _extrair_quantidade_armario(self, linha: str) -> Optional[float]:
        """Extrai quantidade do formato: XX.XX unidades/gramas"""
        try:
            match = re.search(r'(\d+\.?\d*)\s*unidades/gramas', linha)
            if match:
                return float(match.group(1))

            # Tentar formato alternativo
            match = re.search(r'(\d+\.?\d*)g', linha)
            if match:
                return float(match.group(1))

            return None
        except Exception:
            return None
