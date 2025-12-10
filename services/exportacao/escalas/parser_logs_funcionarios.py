#!/usr/bin/env python3
"""
📋 PARSER DE LOGS DE FUNCIONÁRIOS
=================================

Módulo responsável por ler e processar os logs de alocação de funcionários,
extraindo informações sobre atividades, horários e funcionários alocados.

Formato esperado do log:
    ordem | pedido | id_atividade | ? | nome_atividade | funcionário ✅ | inicio | fim
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class AtividadeAlocada:
    """Representa uma atividade alocada a um funcionário."""
    ordem: int
    pedido: int
    id_atividade: int
    nome_atividade: str
    funcionario: str
    inicio: datetime
    fim: datetime

    def duracao_minutos(self) -> int:
        """Retorna a duração da atividade em minutos."""
        delta = self.fim - self.inicio
        return int(delta.total_seconds() / 60)


@dataclass
class ResumoFuncionario:
    """Resumo das atividades de um funcionário."""
    nome: str
    atividades: List[AtividadeAlocada] = field(default_factory=list)

    @property
    def total_atividades(self) -> int:
        return len(self.atividades)

    @property
    def tempo_total_minutos(self) -> int:
        return sum(a.duracao_minutos() for a in self.atividades)


class ParserLogsFuncionarios:
    """
    Parser para logs de alocação de funcionários.

    Lê arquivos .log do diretório de sucesso e extrai informações
    sobre as atividades alocadas a cada funcionário.
    """

    def __init__(self, diretorio_sucesso: str = "logs/funcionarios/sucesso"):
        """
        Inicializa o parser.

        Args:
            diretorio_sucesso: Caminho para o diretório de logs de sucesso
        """
        self.diretorio_sucesso = diretorio_sucesso
        self._atividades_por_funcionario: Dict[str, List[AtividadeAlocada]] = {}
        self._todas_atividades: List[AtividadeAlocada] = []

    def _parse_datetime(self, hora_str: str) -> Optional[datetime]:
        """
        Converte string de hora para datetime.

        Args:
            hora_str: String no formato "HH:MM [DD/MM/YYYY]"

        Returns:
            datetime ou None se não conseguir parsear
        """
        match = re.match(r'(\d{2}):(\d{2}) \[(\d{2})/(\d{2})/(\d{4})\]', hora_str.strip())
        if match:
            h, m, d, mo, y = match.groups()
            return datetime(int(y), int(mo), int(d), int(h), int(m))
        return None

    def _parse_linha(self, linha: str) -> Optional[AtividadeAlocada]:
        """
        Faz o parse de uma linha do log.

        Args:
            linha: Linha do arquivo de log

        Returns:
            AtividadeAlocada ou None se linha inválida
        """
        linha = linha.strip()
        if not linha:
            return None

        partes = [p.strip() for p in linha.split('|')]
        if len(partes) < 8:
            return None

        try:
            ordem = int(partes[0])
            pedido = int(partes[1])
            id_atividade = int(partes[2])
            nome_atividade = partes[4]
            funcionario = partes[5].replace('✅', '').strip()
            inicio = self._parse_datetime(partes[6])
            fim = self._parse_datetime(partes[7])

            if not inicio or not fim:
                return None

            return AtividadeAlocada(
                ordem=ordem,
                pedido=pedido,
                id_atividade=id_atividade,
                nome_atividade=nome_atividade,
                funcionario=funcionario,
                inicio=inicio,
                fim=fim
            )
        except (ValueError, IndexError):
            return None

    def carregar_logs(self) -> bool:
        """
        Carrega todos os logs do diretório de sucesso.

        Returns:
            True se carregou pelo menos um arquivo, False caso contrário
        """
        self._atividades_por_funcionario.clear()
        self._todas_atividades.clear()

        if not os.path.exists(self.diretorio_sucesso):
            return False

        arquivos_processados = 0

        for arquivo in os.listdir(self.diretorio_sucesso):
            if not arquivo.endswith('.log'):
                continue

            caminho = os.path.join(self.diretorio_sucesso, arquivo)

            with open(caminho, 'r', encoding='utf-8') as f:
                for linha in f:
                    atividade = self._parse_linha(linha)
                    if atividade:
                        self._todas_atividades.append(atividade)

                        if atividade.funcionario not in self._atividades_por_funcionario:
                            self._atividades_por_funcionario[atividade.funcionario] = []

                        self._atividades_por_funcionario[atividade.funcionario].append(atividade)

            arquivos_processados += 1

        return arquivos_processados > 0

    def obter_atividades_por_funcionario(self) -> Dict[str, List[AtividadeAlocada]]:
        """
        Retorna dicionário de atividades agrupadas por funcionário.

        Returns:
            Dict com nome do funcionário como chave e lista de atividades como valor
        """
        return self._atividades_por_funcionario.copy()

    def obter_todas_atividades(self) -> List[AtividadeAlocada]:
        """
        Retorna lista de todas as atividades carregadas.

        Returns:
            Lista de AtividadeAlocada
        """
        return self._todas_atividades.copy()

    def obter_resumo_funcionarios(self) -> List[ResumoFuncionario]:
        """
        Retorna resumo das atividades por funcionário.

        Returns:
            Lista de ResumoFuncionario ordenada por nome
        """
        resumos = []
        for nome, atividades in self._atividades_por_funcionario.items():
            resumo = ResumoFuncionario(nome=nome, atividades=atividades)
            resumos.append(resumo)

        return sorted(resumos, key=lambda r: r.nome)

    def obter_intervalo_temporal(self) -> tuple:
        """
        Retorna o intervalo temporal coberto pelos logs.

        Returns:
            Tupla (datetime_inicio, datetime_fim) ou (None, None) se vazio
        """
        if not self._todas_atividades:
            return (None, None)

        inicio = min(a.inicio for a in self._todas_atividades)
        fim = max(a.fim for a in self._todas_atividades)

        return (inicio, fim)

    def obter_funcionarios_unicos(self) -> List[str]:
        """
        Retorna lista de nomes únicos de funcionários.

        Returns:
            Lista de nomes ordenada
        """
        return sorted(self._atividades_por_funcionario.keys())

    def __repr__(self) -> str:
        return (
            f"ParserLogsFuncionarios("
            f"funcionarios={len(self._atividades_por_funcionario)}, "
            f"atividades={len(self._todas_atividades)})"
        )
