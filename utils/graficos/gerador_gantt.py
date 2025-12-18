#!/usr/bin/env python3
"""
📊 GERADOR DE GRÁFICO DE GANTT
==============================

Módulo responsável por gerar gráficos de Gantt para visualização
da timeline de atividades dos funcionários com precisão de minutos.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.patches as mpatches
    MATPLOTLIB_DISPONIVEL = True
except ImportError:
    MATPLOTLIB_DISPONIVEL = False

from services.exportacao.escalas.parser_logs_funcionarios import (
    ParserLogsFuncionarios,
    AtividadeAlocada
)


# Cores para diferentes pedidos
CORES_PEDIDOS = [
    '#FF6B6B',  # Vermelho
    '#4ECDC4',  # Turquesa
    '#45B7D1',  # Azul claro
    '#96CEB4',  # Verde claro
    '#FFEAA7',  # Amarelo
    '#DDA0DD',  # Roxo claro
    '#98D8C8',  # Verde água
    '#F7DC6F',  # Amarelo dourado
    '#BB8FCE',  # Lilás
    '#85C1E9',  # Azul céu
    '#F8B500',  # Laranja
    '#82E0AA',  # Verde menta
    '#F1948A',  # Rosa
    '#AED6F1',  # Azul pastel
]


class GeradorGantt:
    """
    Gerador de gráficos de Gantt para visualização de escalas.
    """

    def __init__(
        self,
        arquivo_funcionarios: str = "data/funcionarios/funcionarios.json",
        diretorio_logs: str = "logs/funcionarios/sucesso",
        diretorio_saida: str = "data/escalas"
    ):
        if not MATPLOTLIB_DISPONIVEL:
            raise ImportError(
                "Módulo matplotlib não encontrado. "
                "Instale com: pip install matplotlib"
            )

        self.arquivo_funcionarios = arquivo_funcionarios
        self.diretorio_logs = diretorio_logs
        self.diretorio_saida = diretorio_saida

        self._funcionarios: Dict[int, dict] = {}
        self._parser = ParserLogsFuncionarios(diretorio_logs)

        # Configurações
        self.largura_figura = 20
        self.altura_por_funcionario = 0.6
        self.altura_barra = 0.4
        self.tamanho_fonte = 8
        self.intervalo_grid = 30
        self.dpi = 150

    def _carregar_funcionarios(self) -> bool:
        if not os.path.exists(self.arquivo_funcionarios):
            return False

        with open(self.arquivo_funcionarios, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._funcionarios = {
            f['id']: f for f in data.get('funcionarios', [])
        }

        return len(self._funcionarios) > 0

    def _obter_cor_pedido(self, pedido: int) -> str:
        return CORES_PEDIDOS[(pedido - 1) % len(CORES_PEDIDOS)]

    def gerar_gantt(
        self,
        nome_arquivo: str = "gantt_funcionarios.png"
    ) -> Optional[str]:
        """
        Gera o gráfico de Gantt.

        Args:
            nome_arquivo: Nome do arquivo de saída

        Returns:
            Caminho do arquivo gerado ou None
        """
        if not self._carregar_funcionarios():
            print("❌ Erro ao carregar funcionários")
            return None

        if not self._parser.carregar_logs():
            print("❌ Erro ao carregar logs de funcionários")
            return None

        atividades = self._parser.obter_atividades_por_funcionario()
        inicio_geral, fim_geral = self._parser.obter_intervalo_temporal()

        if not inicio_geral or not fim_geral:
            print("❌ Nenhuma atividade encontrada nos logs")
            return None

        # Funcionários com atividades
        funcionarios_ativos = sorted(atividades.keys())

        if not funcionarios_ativos:
            print("❌ Nenhum funcionário com atividades")
            return None

        num_funcionarios = len(funcionarios_ativos)
        altura_figura = max(8, num_funcionarios * self.altura_por_funcionario + 2)

        # Criar figura
        fig, ax = plt.subplots(
            figsize=(self.largura_figura, altura_figura),
            dpi=self.dpi
        )

        pedidos_encontrados = set()

        # Plotar barras
        for idx, nome_func in enumerate(funcionarios_ativos):
            y_pos = num_funcionarios - idx - 1

            for ativ in atividades[nome_func]:
                pedidos_encontrados.add(ativ.pedido)
                cor = self._obter_cor_pedido(ativ.pedido)
                duracao = (ativ.fim - ativ.inicio).total_seconds() / 3600

                ax.barh(
                    y_pos,
                    duracao,
                    left=mdates.date2num(ativ.inicio),
                    height=self.altura_barra,
                    color=cor,
                    edgecolor='black',
                    linewidth=0.5,
                    alpha=0.8
                )

                # Texto na barra (se couber)
                duracao_min = (ativ.fim - ativ.inicio).total_seconds() / 60
                if duracao_min >= 15:
                    nome_curto = ativ.nome_atividade[:20] + '..' if len(ativ.nome_atividade) > 22 else ativ.nome_atividade
                    texto = f"{nome_curto}\n[P{ativ.pedido}]"
                    centro_x = mdates.date2num(ativ.inicio) + duracao / 2
                    ax.text(
                        centro_x, y_pos, texto,
                        ha='center', va='center',
                        fontsize=self.tamanho_fonte - 1,
                        color='black', fontweight='bold'
                    )

        # Eixo Y
        ax.set_yticks(range(num_funcionarios))
        ax.set_yticklabels(list(reversed(funcionarios_ativos)), fontsize=self.tamanho_fonte)

        # Eixo X
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%d/%m'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=self.intervalo_grid))

        margem = timedelta(minutes=15)
        ax.set_xlim(
            mdates.date2num(inicio_geral - margem),
            mdates.date2num(fim_geral + margem)
        )

        # Grid
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        # Título
        ax.set_title(
            f'Gráfico de Gantt - Escala de Funcionários\n'
            f'{inicio_geral.strftime("%d/%m/%Y %H:%M")} a {fim_geral.strftime("%d/%m/%Y %H:%M")}',
            fontsize=12, fontweight='bold', pad=20
        )

        ax.set_xlabel('Horário', fontsize=10)
        ax.set_ylabel('Funcionário', fontsize=10)

        # Legenda
        legend_patches = [
            mpatches.Patch(color=self._obter_cor_pedido(p), label=f'Pedido {p}')
            for p in sorted(pedidos_encontrados)
        ]
        ax.legend(
            handles=legend_patches,
            loc='upper right',
            fontsize=8,
            title='Pedidos',
            title_fontsize=9
        )

        plt.tight_layout()

        # Salvar
        os.makedirs(self.diretorio_saida, exist_ok=True)
        caminho_saida = os.path.join(self.diretorio_saida, nome_arquivo)
        plt.savefig(caminho_saida, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"✅ Gráfico de Gantt salvo em: {caminho_saida}")
        print(f"   Funcionários: {num_funcionarios}")
        print(f"   Pedidos: {len(pedidos_encontrados)}")

        return caminho_saida


def gerar_gantt_funcionarios(
    arquivo_funcionarios: str = "data/funcionarios/funcionarios.json",
    diretorio_logs: str = "logs/funcionarios/sucesso",
    diretorio_saida: str = "data/escalas",
    nome_arquivo: str = "gantt_funcionarios.png"
) -> Optional[str]:
    """
    Função utilitária para gerar gráfico de Gantt.
    """
    gerador = GeradorGantt(
        arquivo_funcionarios=arquivo_funcionarios,
        diretorio_logs=diretorio_logs,
        diretorio_saida=diretorio_saida
    )
    return gerador.gerar_gantt(nome_arquivo)


if __name__ == "__main__":
    caminho = gerar_gantt_funcionarios()
    if caminho:
        print(f"\n📊 Gantt gerado: {caminho}")
    else:
        print("\n❌ Falha ao gerar Gantt")
