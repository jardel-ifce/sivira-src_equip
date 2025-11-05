#!/usr/bin/env python3
"""
Script para comparar durações calculadas com os logs de equipamentos.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path


def formatar_duracao(duracao: timedelta) -> str:
    """Formata timedelta para HH:MM:SS."""
    total_segundos = int(duracao.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def parse_log_line(linha: str) -> dict:
    """
    Parse de uma linha do log de equipamentos.
    Formato: ordem | pedido | id_atividade | item | atividade | equipamento | inicio | fim
    """
    partes = [p.strip() for p in linha.split('|')]

    if len(partes) < 8:
        return None

    try:
        # Extrair timestamps
        inicio_str = partes[6]  # Ex: "16:47 [28/10]"
        fim_str = partes[7]     # Ex: "16:55 [28/10]"

        # Parse do formato "HH:MM [DD/MM]"
        inicio_match = re.match(r'(\d+):(\d+) \[(\d+)/(\d+)\]', inicio_str)
        fim_match = re.match(r'(\d+):(\d+) \[(\d+)/(\d+)\]', fim_str)

        if not inicio_match or not fim_match:
            return None

        # Criar objetos datetime (assumindo ano 2025)
        inicio_h, inicio_m, inicio_d, inicio_mes = inicio_match.groups()
        fim_h, fim_m, fim_d, fim_mes = fim_match.groups()

        inicio = datetime(2025, int(inicio_mes), int(inicio_d), int(inicio_h), int(inicio_m))
        fim = datetime(2025, int(fim_mes), int(fim_d), int(fim_h), int(fim_m))

        duracao = fim - inicio

        return {
            'ordem': int(partes[0]),
            'pedido': int(partes[1]),
            'id_atividade': int(partes[2]),
            'item': partes[3].strip(),
            'atividade': partes[4].strip(),
            'equipamento': partes[5].strip(),
            'inicio': inicio,
            'fim': fim,
            'duracao': duracao
        }
    except (ValueError, IndexError) as e:
        return None


def analisar_log_pedido(caminho_log: str) -> dict:
    """Analisa o log de um pedido e retorna informações sobre as atividades."""
    try:
        with open(caminho_log, 'r', encoding='utf-8') as f:
            linhas = f.readlines()

        atividades = {}
        ordem_atividades = []

        # Parse de cada linha (ordem reversa, do fim para o início)
        for linha in reversed(linhas):
            linha = linha.strip()
            if not linha:
                continue

            dados = parse_log_line(linha)
            if not dados:
                continue

            id_atividade = dados['id_atividade']

            # Agregar durações por atividade (algumas atividades usam múltiplos equipamentos)
            if id_atividade not in atividades:
                atividades[id_atividade] = {
                    'id_atividade': id_atividade,
                    'nome': dados['atividade'],
                    'item': dados['item'],
                    'equipamentos': [],
                    'duracao_total': timedelta(),
                    'inicio': dados['inicio'],
                    'fim': dados['fim']
                }
                ordem_atividades.append(id_atividade)

            # Atualizar informações
            atividade = atividades[id_atividade]
            atividade['equipamentos'].append({
                'nome': dados['equipamento'],
                'inicio': dados['inicio'],
                'fim': dados['fim'],
                'duracao': dados['duracao']
            })

            # Expandir o range de tempo da atividade
            if dados['inicio'] < atividade['inicio']:
                atividade['inicio'] = dados['inicio']
            if dados['fim'] > atividade['fim']:
                atividade['fim'] = dados['fim']

        # Calcular duração total de cada atividade
        for id_atividade, atividade in atividades.items():
            atividade['duracao_total'] = atividade['fim'] - atividade['inicio']

        return {
            'atividades': atividades,
            'ordem_atividades': list(reversed(ordem_atividades)),  # Ordem cronológica
            'sucesso': True
        }

    except FileNotFoundError:
        return {'sucesso': False, 'erro': 'Arquivo não encontrado'}
    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}


def comparar_com_calculado(pedido_id: int, ordem_id: int):
    """Compara durações calculadas com as do log."""
    print(f"\n{'='*100}")
    print(f"COMPARAÇÃO: PEDIDO #{pedido_id}")
    print(f"{'='*100}\n")

    # Carregar dados calculados
    caminho_calculado = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/pedidos/duracoes_calculadas.json"
    try:
        with open(caminho_calculado, 'r', encoding='utf-8') as f:
            dados_calculados = json.load(f)

        # Encontrar o pedido
        pedido_calc = None
        for resultado in dados_calculados['resultados']:
            if resultado['id_pedido'] == pedido_id:
                pedido_calc = resultado
                break

        if not pedido_calc:
            print(f"❌ Pedido {pedido_id} não encontrado nos dados calculados.")
            return

    except Exception as e:
        print(f"❌ Erro ao carregar dados calculados: {e}")
        return

    # Analisar log
    caminho_log = f"/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/equipamentos/sucesso/ordem: {ordem_id} | pedido: {pedido_id}.log"
    log_data = analisar_log_pedido(caminho_log)

    if not log_data['sucesso']:
        print(f"❌ Erro ao analisar log: {log_data.get('erro', 'Desconhecido')}")
        return

    print(f"Item: {pedido_calc['nome_item']}")
    print(f"Quantidade: {pedido_calc['quantidade']:,}g")
    print(f"\n{'─'*100}")
    print(f"{'ATIVIDADE':<60} | {'CALCULADO':>12} | {'NO LOG':>12} | {'DIFERENÇA':>12}")
    print(f"{'─'*100}")

    diferenca_total = timedelta()
    atividades_comparadas = 0
    atividades_divergentes = 0

    # Comparar cada atividade
    for ativ_calc in pedido_calc['atividades']:
        id_ativ = ativ_calc['id_atividade']
        nome_ativ = ativ_calc['nome']

        # Buscar no log
        if id_ativ in log_data['atividades']:
            ativ_log = log_data['atividades'][id_ativ]

            duracao_calc = timedelta(seconds=ativ_calc['duracao_segundos'])
            duracao_log = ativ_log['duracao_total']
            diferenca = duracao_log - duracao_calc
            diferenca_total += abs(diferenca)

            atividades_comparadas += 1

            # Marcar divergências (diferença > 1 minuto)
            divergente = abs(diferenca.total_seconds()) > 60
            if divergente:
                atividades_divergentes += 1
                marca = "⚠️ "
            else:
                marca = "✓  "

            # Formatar equipamentos
            equipamentos_str = ", ".join([eq['nome'] for eq in ativ_log['equipamentos']])
            nome_completo = f"{marca}[{id_ativ}] {nome_ativ[:45]}"

            print(f"{nome_completo:<60} | {formatar_duracao(duracao_calc):>12} | "
                  f"{formatar_duracao(duracao_log):>12} | {formatar_duracao(diferenca):>12}")

            # Detalhar equipamentos se houver múltiplos
            if len(ativ_log['equipamentos']) > 1:
                for eq in ativ_log['equipamentos']:
                    print(f"  └─ {eq['nome']:<56} | {formatar_duracao(eq['duracao']):>12} |")
        else:
            print(f"⚠️  [{id_ativ}] {nome_ativ:<45} | {ativ_calc['duracao']:>12} | {'N/A':>12} | {'N/A':>12}")

    print(f"{'─'*100}")

    # Totais
    duracao_total_calc = timedelta(seconds=pedido_calc['duracao_total_segundos'])
    duracao_total_log = sum([ativ['duracao_total'] for ativ in log_data['atividades'].values()], timedelta())
    diferenca_total_pedido = duracao_total_log - duracao_total_calc

    print(f"{'TOTAL DO PEDIDO':<60} | {formatar_duracao(duracao_total_calc):>12} | "
          f"{formatar_duracao(duracao_total_log):>12} | {formatar_duracao(diferenca_total_pedido):>12}")

    # Período de execução no log
    inicio_exec = min([ativ['inicio'] for ativ in log_data['atividades'].values()])
    fim_exec = max([ativ['fim'] for ativ in log_data['atividades'].values()])
    tempo_total_execucao = fim_exec - inicio_exec

    print(f"\n{'─'*100}")
    print(f"Período de execução (log): {inicio_exec.strftime('%d/%m %H:%M')} → {fim_exec.strftime('%d/%m %H:%M')} "
          f"(duração total: {formatar_duracao(tempo_total_execucao)})")
    print(f"Atividades comparadas: {atividades_comparadas}")
    print(f"Atividades com divergência > 1 min: {atividades_divergentes}")

    # Análise
    if atividades_divergentes == 0:
        print(f"\n✓ Todos os tempos calculados estão de acordo com os logs!")
    else:
        print(f"\n⚠️  Há {atividades_divergentes} atividade(s) com divergência significativa.")

    print(f"{'='*100}\n")


def main():
    """Função principal."""
    print("\n" + "="*100)
    print("COMPARAÇÃO DE DURAÇÕES: CALCULADO vs. LOGS DE EQUIPAMENTOS")
    print("="*100)

    # Comparar pedidos 1 e 2
    comparar_com_calculado(pedido_id=1, ordem_id=1)
    comparar_com_calculado(pedido_id=2, ordem_id=1)

    print("\n" + "="*100)
    print("ANÁLISE COMPLETA")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
