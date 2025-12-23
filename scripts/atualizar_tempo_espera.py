#!/usr/bin/env python3
"""
Script para atualizar o campo tempo_maximo_de_espera em todos os arquivos
de atividades de produtos e subprodutos com valores aleatórios entre
00:10:00 e 02:30:00.
"""

import json
import random
import os
from pathlib import Path

def gerar_tempo_aleatorio():
    """Gera um tempo aleatório entre 00:10:00 (10 min) e 02:30:00 (2h30min)."""
    # 10 minutos = 600 segundos
    # 2h30min = 150 minutos = 9000 segundos
    segundos_total = random.randint(600, 9000)

    horas = segundos_total // 3600
    minutos = (segundos_total % 3600) // 60
    segundos = segundos_total % 60

    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

def atualizar_arquivo(caminho_arquivo):
    """Atualiza o tempo_maximo_de_espera em todas as atividades de um arquivo."""
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    atividades_atualizadas = 0

    if 'atividades' in dados:
        for atividade in dados['atividades']:
            if 'tempo_maximo_de_espera' in atividade:
                novo_tempo = gerar_tempo_aleatorio()
                atividade['tempo_maximo_de_espera'] = novo_tempo
                atividades_atualizadas += 1

    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    return atividades_atualizadas

def main():
    base_path = Path(__file__).parent.parent / 'data'

    # Diretórios com arquivos de atividades
    diretorios = [
        base_path / 'produtos' / 'atividades',
        base_path / 'subprodutos' / 'atividades'
    ]

    total_arquivos = 0
    total_atividades = 0

    for diretorio in diretorios:
        if not diretorio.exists():
            print(f"Diretório não encontrado: {diretorio}")
            continue

        print(f"\nProcessando: {diretorio}")
        print("-" * 50)

        for arquivo in sorted(diretorio.glob('*.json')):
            atividades = atualizar_arquivo(arquivo)
            total_arquivos += 1
            total_atividades += atividades
            print(f"  {arquivo.name}: {atividades} atividade(s) atualizada(s)")

    print("\n" + "=" * 50)
    print(f"RESUMO: {total_arquivos} arquivos, {total_atividades} atividades atualizadas")

if __name__ == '__main__':
    main()
