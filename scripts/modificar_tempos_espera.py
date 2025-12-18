#!/usr/bin/env python3
"""
Script para modificar aleatoriamente ~50% das atividades com tempo_maximo_de_espera = 00:00:00
e gerar relatório das modificações.
"""

import json
import os
import random
from pathlib import Path
from datetime import datetime

# Configuração
BASE_DIR = Path("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")
PRODUTOS_DIR = BASE_DIR / "data" / "produtos" / "atividades"
SUBPRODUTOS_DIR = BASE_DIR / "data" / "subprodutos" / "atividades"
DOCS_DIR = BASE_DIR / "docs" / "modificacoes"

# Tempos disponíveis para atribuição (máximo 00:30:00)
TEMPOS_DISPONIVEIS = [
    "00:03:00",
    "00:05:00",
    "00:07:00",
    "00:10:00",
    "00:15:00",
    "00:20:00",
    "00:30:00"
]

# IDs dos produtos do exemplo_pedidos.csv
PRODUTOS_PEDIDOS = [1001, 1002, 1003, 1004, 1005, 1055, 1059, 1069, 1070, 1071, 1072, 1073, 1074]

# Seed para reprodutibilidade
random.seed(42)


def carregar_json(caminho: Path) -> dict:
    """Carrega um arquivo JSON."""
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


def salvar_json(caminho: Path, dados: dict):
    """Salva um arquivo JSON com formatação."""
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def encontrar_arquivos_produtos() -> list:
    """Encontra arquivos JSON dos produtos nos pedidos."""
    arquivos = []
    for produto_id in PRODUTOS_PEDIDOS:
        for arquivo in PRODUTOS_DIR.glob(f"{produto_id}_*.json"):
            arquivos.append(arquivo)
    return arquivos


def encontrar_arquivos_subprodutos() -> list:
    """Encontra todos os arquivos JSON de subprodutos."""
    return list(SUBPRODUTOS_DIR.glob("*.json"))


def identificar_atividades_tempo_zero(dados: dict) -> list:
    """Identifica atividades com tempo_maximo_de_espera = 00:00:00."""
    atividades = []
    for idx, ativ in enumerate(dados.get("atividades", [])):
        tempo = ativ.get("tempo_maximo_de_espera", "")
        if tempo == "00:00:00":
            atividades.append({
                "idx": idx,
                "id_atividade": ativ.get("id_atividade"),
                "nome": ativ.get("nome"),
                "tempo_original": tempo
            })
    return atividades


def modificar_arquivo(caminho: Path, porcentagem: float = 0.5) -> list:
    """
    Modifica ~50% das atividades com tempo zero em um arquivo.
    Retorna lista de modificações realizadas.
    """
    dados = carregar_json(caminho)
    atividades_zero = identificar_atividades_tempo_zero(dados)

    if not atividades_zero:
        return []

    # Seleciona ~50% aleatoriamente
    n_modificar = max(1, int(len(atividades_zero) * porcentagem))
    atividades_selecionadas = random.sample(atividades_zero, min(n_modificar, len(atividades_zero)))

    modificacoes = []
    for ativ in atividades_selecionadas:
        novo_tempo = random.choice(TEMPOS_DISPONIVEIS)
        dados["atividades"][ativ["idx"]]["tempo_maximo_de_espera"] = novo_tempo
        modificacoes.append({
            "arquivo": caminho.name,
            "item_id": dados.get("id_item"),
            "item_nome": dados.get("nome"),
            "id_atividade": ativ["id_atividade"],
            "nome_atividade": ativ["nome"],
            "tempo_anterior": ativ["tempo_original"],
            "tempo_novo": novo_tempo
        })

    # Salva o arquivo modificado
    salvar_json(caminho, dados)

    return modificacoes


def gerar_latex(modificacoes_produtos: list, modificacoes_subprodutos: list):
    """Gera documento LaTeX com relatório das modificações."""

    data_atual = datetime.now().strftime("%d/%m/%Y")

    latex = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[brazil]{babel}
\usepackage{geometry}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{fancyhdr}

\geometry{margin=2.5cm}

\pagestyle{fancy}
\fancyhf{}
\rhead{SIVIRA - Sistema de Planejamento de Produção}
\lhead{Modificações de Tempo Máximo de Espera}
\rfoot{Página \thepage}

\title{\textbf{Relatório de Modificações}\\[0.5cm]
\large Tempo Máximo de Espera nas Atividades}
\author{SIVIRA - Sistema de Planejamento de Produção}
\date{""" + data_atual + r"""}

\begin{document}

\maketitle

\section{Introdução}

Este documento apresenta as modificações realizadas no campo \texttt{tempo\_maximo\_de\_espera}
dos arquivos JSON de atividades. Aproximadamente 50\% das atividades que possuíam tempo
igual a \texttt{00:00:00} foram selecionadas aleatoriamente e receberam novos valores
entre \texttt{00:03:00} e \texttt{00:30:00}.

\section{Resumo das Modificações}

\begin{itemize}
    \item \textbf{Total de modificações em PRODUTOS:} """ + str(len(modificacoes_produtos)) + r"""
    \item \textbf{Total de modificações em SUBPRODUTOS:} """ + str(len(modificacoes_subprodutos)) + r"""
    \item \textbf{Total geral:} """ + str(len(modificacoes_produtos) + len(modificacoes_subprodutos)) + r"""
\end{itemize}

\section{Modificações em PRODUTOS}

"""

    if modificacoes_produtos:
        latex += r"""\begin{longtable}{p{4cm}p{5cm}cc}
\toprule
\textbf{Arquivo} & \textbf{Atividade} & \textbf{Antes} & \textbf{Depois} \\
\midrule
\endhead
"""
        for mod in modificacoes_produtos:
            nome_ativ = mod["nome_atividade"].replace("_", r"\_")[:30]
            arquivo = mod["arquivo"].replace("_", r"\_")[:25]
            latex += f"{arquivo} & {nome_ativ} & {mod['tempo_anterior']} & {mod['tempo_novo']} \\\\\n"

        latex += r"""\bottomrule
\end{longtable}
"""
    else:
        latex += r"\textit{Nenhuma modificação realizada em produtos.}" + "\n"

    latex += r"""
\section{Modificações em SUBPRODUTOS}

"""

    if modificacoes_subprodutos:
        latex += r"""\begin{longtable}{p{4cm}p{5cm}cc}
\toprule
\textbf{Arquivo} & \textbf{Atividade} & \textbf{Antes} & \textbf{Depois} \\
\midrule
\endhead
"""
        for mod in modificacoes_subprodutos:
            nome_ativ = mod["nome_atividade"].replace("_", r"\_")[:30]
            arquivo = mod["arquivo"].replace("_", r"\_")[:25]
            latex += f"{arquivo} & {nome_ativ} & {mod['tempo_anterior']} & {mod['tempo_novo']} \\\\\n"

        latex += r"""\bottomrule
\end{longtable}
"""
    else:
        latex += r"\textit{Nenhuma modificação realizada em subprodutos.}" + "\n"

    latex += r"""
\section{Tempos Utilizados}

Os seguintes valores de tempo máximo de espera foram utilizados nas modificações:

\begin{itemize}
    \item \texttt{00:03:00} - 3 minutos
    \item \texttt{00:05:00} - 5 minutos
    \item \texttt{00:07:00} - 7 minutos
    \item \texttt{00:10:00} - 10 minutos
    \item \texttt{00:15:00} - 15 minutos
    \item \texttt{00:20:00} - 20 minutos
    \item \texttt{00:30:00} - 30 minutos (máximo)
\end{itemize}

\section{Observações}

\begin{enumerate}
    \item As atividades foram selecionadas de forma aleatória usando seed 42 para reprodutibilidade.
    \item Atividades que já possuíam tempo diferente de \texttt{00:00:00} foram preservadas.
    \item A modificação do tempo máximo de espera permite flexibilidade no agendamento das atividades.
\end{enumerate}

\end{document}
"""

    return latex


def main():
    """Função principal."""
    print("=" * 60)
    print("MODIFICAÇÃO DE TEMPO MÁXIMO DE ESPERA")
    print("=" * 60)

    # Encontra arquivos
    arquivos_produtos = encontrar_arquivos_produtos()
    arquivos_subprodutos = encontrar_arquivos_subprodutos()

    print(f"\nArquivos de PRODUTOS encontrados: {len(arquivos_produtos)}")
    print(f"Arquivos de SUBPRODUTOS encontrados: {len(arquivos_subprodutos)}")

    # Modifica arquivos
    todas_modificacoes_produtos = []
    todas_modificacoes_subprodutos = []

    print("\n--- Modificando PRODUTOS ---")
    for arquivo in arquivos_produtos:
        mods = modificar_arquivo(arquivo)
        todas_modificacoes_produtos.extend(mods)
        if mods:
            print(f"  {arquivo.name}: {len(mods)} modificações")

    print("\n--- Modificando SUBPRODUTOS ---")
    for arquivo in arquivos_subprodutos:
        mods = modificar_arquivo(arquivo)
        todas_modificacoes_subprodutos.extend(mods)
        if mods:
            print(f"  {arquivo.name}: {len(mods)} modificações")

    # Gera LaTeX
    print("\n--- Gerando documento LaTeX ---")
    latex_content = gerar_latex(todas_modificacoes_produtos, todas_modificacoes_subprodutos)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    latex_path = DOCS_DIR / "MODIFICACOES_TEMPO_MAXIMO_ESPERA.tex"

    with open(latex_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)

    print(f"  Arquivo LaTeX salvo em: {latex_path}")

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Total de modificações em PRODUTOS: {len(todas_modificacoes_produtos)}")
    print(f"Total de modificações em SUBPRODUTOS: {len(todas_modificacoes_subprodutos)}")
    print(f"Total geral: {len(todas_modificacoes_produtos) + len(todas_modificacoes_subprodutos)}")

    # Exibe modificações detalhadas
    print("\n--- Detalhes das Modificações ---")
    for mod in todas_modificacoes_produtos + todas_modificacoes_subprodutos:
        print(f"  [{mod['item_id']}] {mod['nome_atividade']}: {mod['tempo_anterior']} -> {mod['tempo_novo']}")

    return todas_modificacoes_produtos, todas_modificacoes_subprodutos


if __name__ == "__main__":
    main()
