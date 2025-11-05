"""
Classe Base para Parsers de Equipamentos
=========================================

Define interface comum e utilitários compartilhados para todos os parsers.
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO


class ParserBase(ABC):
    """
    🔍 Classe base abstrata para parsers de equipamentos

    Cada parser específico deve:
    1. Herdar desta classe
    2. Implementar o método parse()
    3. Retornar lista de OcupacaoDTO com as ocupações extraídas

    Fornece utilitários comuns para:
    - Extração de horários
    - Extração de IDs (ordem, pedido, atividade, item)
    - Extração de quantidades
    - Conversão de strings para datetime
    """

    def __init__(self):
        """Inicializa parser base"""
        self.erros: List[str] = []

    @abstractmethod
    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        """
        Método abstrato que deve ser implementado por cada parser específico

        Args:
            log_content: Conteúdo do log do equipamento
            nome_equipamento: Nome do equipamento (ex: "Bancada 1")

        Returns:
            Lista de OcupacaoDTO com as ocupações extraídas
        """
        pass

    # ==========================================================
    # 🔧 UTILITÁRIOS DE EXTRAÇÃO - REGEX
    # ==========================================================

    def extrair_ids_ocupacao(self, linha: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Extrai IDs (ordem, pedido, atividade, item) de uma linha de log

        Padrão esperado: "Ordem X | Pedido Y | Atividade Z | Item W"

        Returns:
            Tupla (ordem, pedido, atividade, item) ou None se não encontrar
        """
        pattern = r'Ordem[:\s]+(\d+)\s*\|\s*Pedido[:\s]+(\d+)\s*\|\s*Atividade[:\s]+(\d+)\s*\|\s*Item[:\s]+(\d+)'
        match = re.search(pattern, linha, re.IGNORECASE)

        if match:
            return (
                int(match.group(1)),  # ordem
                int(match.group(2)),  # pedido
                int(match.group(3)),  # atividade
                int(match.group(4))   # item
            )
        return None

    def extrair_horarios(self, linha: str) -> Optional[Tuple[str, str]]:
        """
        Extrai horários de início e fim de uma linha

        Padrões suportados:
        - "2025-10-29 01:14 → 2025-10-29 01:26" (com data)
        - "01:14 → 01:26" (sem data, retrocompatível)
        - "01:14 - 01:26"
        - "Início: 01:14 | Fim: 01:26"

        Returns:
            Tupla (inicio_str, fim_str) ou None se não encontrar
        """
        # Padrão 1: YYYY-MM-DD HH:MM → YYYY-MM-DD HH:MM (novo formato com data)
        pattern_com_data = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*[→\-]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})'
        match = re.search(pattern_com_data, linha)
        if match:
            return (match.group(1), match.group(2))

        # Padrão 2: HH:MM → HH:MM ou HH:MM - HH:MM (formato antigo, retrocompatível)
        pattern_sem_data = r'(\d{2}:\d{2})\s*[→\-]\s*(\d{2}:\d{2})'
        match = re.search(pattern_sem_data, linha)
        if match:
            return (match.group(1), match.group(2))

        # Padrão 3: Início: HH:MM | Fim: HH:MM
        pattern_inicio_fim = r'Início:\s*(\d{2}:\d{2}).*?Fim:\s*(\d{2}:\d{2})'
        match = re.search(pattern_inicio_fim, linha, re.IGNORECASE)
        if match:
            return (match.group(1), match.group(2))

        return None

    def extrair_horario_completo(self, linha: str) -> Optional[Tuple[str, str]]:
        """
        Extrai horários com data opcional

        Padrões suportados:
        - "01:14 [27/10]" (com data)
        - "01:14" (sem data)

        Returns:
            Tupla (horario_str, data_str_ou_None)
        """
        # Com data
        pattern_com_data = r'(\d{2}:\d{2})\s*\[(\d{2}/\d{2})\]'
        match = re.search(pattern_com_data, linha)
        if match:
            return (match.group(1), match.group(2))

        # Sem data
        pattern_sem_data = r'(\d{2}:\d{2})'
        match = re.search(pattern_sem_data, linha)
        if match:
            return (match.group(1), None)

        return None

    def extrair_quantidade_gramas(self, linha: str) -> Optional[float]:
        """
        Extrai quantidade em gramas

        Padrões:
        - "1950g"
        - "1950.0g"
        - "Quantidade: 1950g"

        Returns:
            Float com quantidade em gramas ou None
        """
        pattern = r'(\d+(?:\.\d+)?)\s*g'
        match = re.search(pattern, linha, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    def extrair_quantidade_unidades(self, linha: str) -> Optional[float]:
        """
        Extrai quantidade em unidades

        Padrões:
        - "50 unidades"
        - "10.00 unidades/gramas"

        Returns:
            Float com quantidade ou None
        """
        pattern = r'(\d+(?:\.\d+)?)\s*unidades'
        match = re.search(pattern, linha, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    def extrair_numero_fracao(self, linha: str) -> Optional[int]:
        """
        Extrai número de fração

        Padrões:
        - "Fração 1:"
        - "fração 3:"

        Returns:
            Número da fração ou None
        """
        pattern = r'fração\s+(\d+)'
        match = re.search(pattern, linha, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def extrair_numero_boca(self, linha: str) -> Optional[int]:
        """
        Extrai número de boca (fogão)

        Padrões:
        - "Boca 1"
        - "boca 2:"

        Returns:
            Número da boca ou None
        """
        pattern = r'boca\s+(\d+)'
        match = re.search(pattern, linha, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def extrair_numero_nivel(self, linha: str) -> Optional[int]:
        """
        Extrai número de nível

        Padrões:
        - "Nível 1"
        - "Andar 0, Nível 1"

        Returns:
            Número do nível ou None
        """
        pattern = r'nível\s+(\d+)'
        match = re.search(pattern, linha, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def extrair_numero_caixa(self, linha: str) -> Optional[int]:
        """
        Extrai número de caixa

        Padrões:
        - "Caixa 1"
        - "caixa 2:"

        Returns:
            Número da caixa ou None
        """
        pattern = r'caixa\s+(\d+)'
        match = re.search(pattern, linha, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def extrair_temperatura(self, linha: str) -> Optional[float]:
        """
        Extrai temperatura

        Padrões:
        - "Temp: 4°C"
        - "-18°C"
        - "Temperatura: 4°C"

        Returns:
            Temperatura em °C ou None
        """
        pattern = r'(-?\d+(?:\.\d+)?)\s*°C'
        match = re.search(pattern, linha, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    # ==========================================================
    # 🕒 UTILITÁRIOS DE CONVERSÃO - DATETIME
    # ==========================================================

    def converter_horario_para_datetime(
        self,
        horario_str: str,
        data_str: Optional[str] = None,
        data_base: Optional[datetime] = None
    ) -> datetime:
        """
        Converte string de horário para datetime

        Args:
            horario_str: String no formato "HH:MM" ou "YYYY-MM-DD HH:MM"
            data_str: String opcional no formato "DD/MM"
            data_base: Data base para usar se data_str não fornecida

        Returns:
            Objeto datetime
        """
        # Verificar se horario_str já contém data completa (YYYY-MM-DD HH:MM)
        if ' ' in horario_str and len(horario_str) == 16:
            try:
                return datetime.strptime(horario_str, '%Y-%m-%d %H:%M')
            except ValueError:
                pass

        # Parse horário simples (HH:MM)
        horas, minutos = map(int, horario_str.split(':'))

        # Determinar data
        if data_str:
            dia, mes = map(int, data_str.split('/'))
            ano = data_base.year if data_base else datetime.now().year
            return datetime(ano, mes, dia, horas, minutos)
        elif data_base:
            return datetime(
                data_base.year,
                data_base.month,
                data_base.day,
                horas,
                minutos
            )
        else:
            # Usar data atual como fallback
            hoje = datetime.now()
            return datetime(hoje.year, hoje.month, hoje.day, horas, minutos)

    def ajustar_data_se_atravessar_meia_noite(
        self,
        inicio: datetime,
        fim: datetime
    ) -> datetime:
        """
        Ajusta data de fim se atravessar meia-noite

        Se fim < inicio, assume que fim é no dia seguinte

        Args:
            inicio: Datetime de início
            fim: Datetime de fim

        Returns:
            Datetime de fim ajustado
        """
        if fim < inicio:
            return fim + timedelta(days=1)
        return fim

    # ==========================================================
    # 🔧 UTILITÁRIOS DE VALIDAÇÃO
    # ==========================================================

    def validar_ids(self, ids: Tuple[int, int, int, int]) -> bool:
        """Valida se todos os IDs são positivos"""
        return all(id_val > 0 for id_val in ids)

    def validar_horarios(self, inicio: datetime, fim: datetime) -> bool:
        """Valida se fim é posterior ao início"""
        return fim > inicio

    def adicionar_erro(self, erro: str):
        """Adiciona erro à lista de erros"""
        self.erros.append(erro)

    def obter_erros(self) -> List[str]:
        """Retorna lista de erros encontrados"""
        return self.erros.copy()

    def limpar_erros(self):
        """Limpa lista de erros"""
        self.erros.clear()
