#!/usr/bin/env python3
"""
📊 GERADOR DE ESCALAS CSV
=========================

Módulo responsável por gerar arquivos CSV com escalas de funcionários
formatadas, incluindo intervalos de tempo e atividades alocadas.
"""

import os
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from services.exportacao.escalas.parser_logs_funcionarios import (
    ParserLogsFuncionarios,
    AtividadeAlocada
)


@dataclass
class ConfiguracaoCSV:
    """Configurações para geração do arquivo CSV."""
    intervalo_minutos: int = 30
    exibir_nomes_completos: bool = True
    excluir_linhas_vazias: bool = True
    separador: str = ";"


class GeradorEscalaCSV:
    """
    Gerador de arquivos CSV com escalas de funcionários.

    Gera arquivos CSV formatados com:
    - Intervalos de tempo nas linhas
    - Funcionários nas colunas
    - Atividades alocadas nas células
    """

    def __init__(
        self,
        arquivo_funcionarios: str = "data/funcionarios/funcionarios.json",
        diretorio_logs: str = "logs/funcionarios/sucesso",
        diretorio_saida: str = "data/escalas"
    ):
        """
        Inicializa o gerador.

        Args:
            arquivo_funcionarios: Caminho para o JSON de funcionários
            diretorio_logs: Caminho para logs de alocação
            diretorio_saida: Diretório para salvar o arquivo
        """
        self.arquivo_funcionarios = arquivo_funcionarios
        self.diretorio_logs = diretorio_logs
        self.diretorio_saida = diretorio_saida
        self.config = ConfiguracaoCSV()

        self._funcionarios: Dict[int, dict] = {}
        self._parser = ParserLogsFuncionarios(diretorio_logs)

    def _carregar_funcionarios(self) -> bool:
        """
        Carrega funcionários do arquivo JSON.

        Returns:
            True se carregou com sucesso
        """
        if not os.path.exists(self.arquivo_funcionarios):
            return False

        with open(self.arquivo_funcionarios, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._funcionarios = {
            f['id']: f for f in data.get('funcionarios', [])
        }

        return len(self._funcionarios) > 0

    def _gerar_intervalos(
        self,
        inicio: datetime,
        fim: datetime
    ) -> List[datetime]:
        """
        Gera lista de intervalos de tempo.

        Args:
            inicio: Data/hora inicial
            fim: Data/hora final

        Returns:
            Lista de datetimes representando início de cada intervalo
        """
        intervalos = []
        atual = inicio.replace(
            minute=(inicio.minute // self.config.intervalo_minutos)
                   * self.config.intervalo_minutos,
            second=0,
            microsecond=0
        )

        while atual <= fim:
            intervalos.append(atual)
            atual += timedelta(minutes=self.config.intervalo_minutos)

        return intervalos

    def _formatar_intervalo(self, inicio: datetime) -> str:
        """
        Formata um intervalo para exibição.

        Args:
            inicio: Datetime do início do intervalo

        Returns:
            String formatada "HH:MM - HH:MM [DD/MM]"
        """
        fim = inicio + timedelta(minutes=self.config.intervalo_minutos)
        return f"{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')} [{inicio.strftime('%d/%m')}]"

    def _encontrar_intervalos_com_atividades(
        self,
        intervalos: List[datetime],
        atividades: Dict[str, List[AtividadeAlocada]]
    ) -> Set[int]:
        """
        Encontra índices de intervalos que possuem atividades.

        Args:
            intervalos: Lista de intervalos
            atividades: Dicionário de atividades por funcionário

        Returns:
            Conjunto de índices de intervalos com atividades
        """
        indices = set()

        for lista_ativ in atividades.values():
            for ativ in lista_ativ:
                for idx, intervalo in enumerate(intervalos):
                    # Verificar sobreposição entre atividade e intervalo
                    fim_intervalo = intervalo + timedelta(minutes=self.config.intervalo_minutos)
                    if ativ.inicio < fim_intervalo and ativ.fim > intervalo:
                        indices.add(idx)

        return indices

    def gerar_escala(
        self,
        nome_arquivo: str = "escala_funcionarios_atividades.csv"
    ) -> Optional[str]:
        """
        Gera o arquivo CSV com a escala de funcionários.

        Args:
            nome_arquivo: Nome do arquivo de saída

        Returns:
            Caminho do arquivo gerado ou None se falhar
        """
        # Carregar dados
        if not self._carregar_funcionarios():
            print("❌ Erro ao carregar funcionários")
            return None

        if not self._parser.carregar_logs():
            print("❌ Erro ao carregar logs de funcionários")
            return None

        atividades = self._parser.obter_atividades_por_funcionario()
        inicio, fim = self._parser.obter_intervalo_temporal()

        if not inicio or not fim:
            print("❌ Nenhuma atividade encontrada nos logs")
            return None

        # Gerar intervalos
        todos_intervalos = self._gerar_intervalos(inicio, fim)

        # Filtrar intervalos vazios se configurado
        if self.config.excluir_linhas_vazias:
            indices_ativos = self._encontrar_intervalos_com_atividades(
                todos_intervalos, atividades
            )
            intervalos = [
                (idx, todos_intervalos[idx])
                for idx in sorted(indices_ativos)
            ]
        else:
            intervalos = list(enumerate(todos_intervalos))

        # Lista ordenada de funcionários
        funcionarios_ordenados = [
            self._funcionarios[func_id]
            for func_id in sorted(self._funcionarios.keys())
        ]

        # Criar diretório se não existir
        os.makedirs(self.diretorio_saida, exist_ok=True)

        # Caminho do arquivo
        caminho_saida = os.path.join(self.diretorio_saida, nome_arquivo)

        # Escrever CSV
        with open(caminho_saida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=self.config.separador)

            # Cabeçalho
            cabecalho = ['Intervalo'] + [func['nome'] for func in funcionarios_ordenados]
            writer.writerow(cabecalho)

            # Criar mapeamento nome -> coluna
            func_cols = {func['nome']: idx for idx, func in enumerate(funcionarios_ordenados)}

            # Preencher linhas
            for orig_idx, intervalo in intervalos:
                # Iniciar linha com intervalo
                linha = [self._formatar_intervalo(intervalo)]

                # Preencher células de funcionários
                for func in funcionarios_ordenados:
                    nome_func = func['nome']
                    celula = ""

                    # Verificar se funcionário tem atividade neste intervalo
                    if nome_func in atividades:
                        for ativ in atividades[nome_func]:
                            fim_intervalo = intervalo + timedelta(minutes=self.config.intervalo_minutos)
                            if ativ.inicio < fim_intervalo and ativ.fim > intervalo:
                                # Nome da atividade
                                nome = ativ.nome_atividade
                                if not self.config.exibir_nomes_completos and len(nome) > 20:
                                    nome = nome[:18] + '..'

                                # Formato: nome_atividade [ordem X | pedido Y]
                                celula = f"{nome} [ordem {ativ.ordem} | pedido {ativ.pedido}]"
                                break

                    linha.append(celula)

                writer.writerow(linha)

        print(f"✅ Escala CSV salva em: {caminho_saida}")
        print(f"   Total de funcionários: {len(self._funcionarios)}")
        print(f"   Funcionários com atividades: {len(atividades)}")
        print(f"   Intervalos com atividades: {len(intervalos)}")

        return caminho_saida

    def configurar(self, **kwargs) -> 'GeradorEscalaCSV':
        """
        Configura opções do gerador.

        Args:
            **kwargs: Opções de configuração

        Returns:
            self para encadeamento
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        return self


def gerar_escala_funcionarios(
    arquivo_funcionarios: str = "data/funcionarios/funcionarios.json",
    diretorio_logs: str = "logs/funcionarios/sucesso",
    diretorio_saida: str = "data/escalas",
    nome_arquivo: str = "escala_funcionarios_atividades.csv",
    excluir_linhas_vazias: bool = True,
    nomes_completos: bool = True
) -> Optional[str]:
    """
    Função utilitária para gerar escala de funcionários em CSV.

    Args:
        arquivo_funcionarios: Caminho para JSON de funcionários
        diretorio_logs: Caminho para logs de alocação
        diretorio_saida: Diretório de saída
        nome_arquivo: Nome do arquivo CSV
        excluir_linhas_vazias: Se True, remove linhas sem atividades
        nomes_completos: Se True, exibe nomes completos das atividades

    Returns:
        Caminho do arquivo gerado ou None
    """
    gerador = GeradorEscalaCSV(
        arquivo_funcionarios=arquivo_funcionarios,
        diretorio_logs=diretorio_logs,
        diretorio_saida=diretorio_saida
    )

    gerador.configurar(
        excluir_linhas_vazias=excluir_linhas_vazias,
        exibir_nomes_completos=nomes_completos
    )

    return gerador.gerar_escala(nome_arquivo)


# Execução direta para testes
if __name__ == "__main__":
    caminho = gerar_escala_funcionarios()
    if caminho:
        print(f"\n📊 Escala CSV gerada com sucesso: {caminho}")
    else:
        print("\n❌ Falha ao gerar escala CSV")
