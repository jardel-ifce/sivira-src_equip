"""
Parser para Bancadas
====================

Extrai ocupações de bancadas do log detalhado.

Formato esperado no log:
```
📅 Agenda da Bancada 1
==============================================
🔹 Fração 1:
   🪵 Ordem 1 | Pedido 1 | Atividade 10016 | Item 1001 | 06:33 → 06:37
   🪵 Ordem 1 | Pedido 1 | Atividade 10014 | Item 1001 | 03:30 → 03:33
🔹 Fração 2:
   🪵 Ordem 1 | Pedido 1 | Atividade 10016 | Item 1001 | 06:33 → 06:37
```
"""

from typing import List
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO


class ParserBancada(ParserBase):
    """
    🪵 Parser especializado para Bancadas

    Extrai ocupações por fração, identificando:
    - Número da fração
    - IDs (ordem, pedido, atividade, item)
    - Horários de início e fim
    """

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Extrai ocupações de bancada do log

        Args:
            log_content: Conteúdo do log do equipamento
            nome_equipamento: Nome do equipamento (ex: "Bancada 1")

        Returns:
            Lista de OcupacaoDTO com as ocupações extraídas
        """
        self.limpar_erros()
        ocupacoes = []

        linhas = log_content.split('\n')
        fracao_atual = None
        data_base = datetime.now()  # Data base para conversão de horários

        for linha in linhas:
            linha = linha.strip()

            # Detectar início de nova fração
            if '🔹 Fração' in linha:
                fracao_numero = self.extrair_numero_fracao(linha)
                if fracao_numero is not None:
                    fracao_atual = fracao_numero
                continue

            # Detectar ocupação em fração
            if fracao_atual is not None and '🪵' in linha:
                ocupacao = self._extrair_ocupacao_fracao(
                    linha,
                    fracao_atual,
                    nome_equipamento,
                    data_base
                )
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_ocupacao_fracao(
        self,
        linha: str,
        fracao_numero: int,
        nome_equipamento: str,
        data_base: datetime
    ) -> OcupacaoDTO:
        """
        Extrai uma ocupação de fração de bancada

        Args:
            linha: Linha do log
            fracao_numero: Número da fração
            nome_equipamento: Nome do equipamento
            data_base: Data base para conversão

        Returns:
            OcupacaoDTO ou None se não conseguir extrair
        """
        try:
            # Extrair IDs
            ids = self.extrair_ids_ocupacao(linha)
            if not ids:
                self.adicionar_erro(f"Não foi possível extrair IDs da linha: {linha}")
                return None

            if not self.validar_ids(ids):
                self.adicionar_erro(f"IDs inválidos na linha: {linha}")
                return None

            id_ordem, id_pedido, id_atividade, id_item = ids

            # Extrair horários
            horarios = self.extrair_horarios(linha)
            if not horarios:
                self.adicionar_erro(f"Não foi possível extrair horários da linha: {linha}")
                return None

            inicio_str, fim_str = horarios

            # Converter para datetime
            inicio = self.converter_horario_para_datetime(inicio_str, data_base=data_base)
            fim = self.converter_horario_para_datetime(fim_str, data_base=data_base)

            # Ajustar se atravessar meia-noite
            fim = self.ajustar_data_se_atravessar_meia_noite(inicio, fim)

            # Validar horários
            if not self.validar_horarios(inicio, fim):
                self.adicionar_erro(f"Horários inválidos: {inicio_str} -> {fim_str}")
                return None

            # Criar DTO
            return OcupacaoDTO(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                inicio=inicio,
                fim=fim,
                nome_equipamento=nome_equipamento,
                tipo_equipamento="Bancada",
                detalhes={
                    "fracao_numero": fracao_numero
                }
            )

        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de bancada: {e}")
            return None
