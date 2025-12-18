#!/usr/bin/env python3
"""
Coleta de Metricas para Relatorio Comparativo SEQ vs PL
========================================================

Executa multiplas rodadas de simulacao e coleta metricas detalhadas
para geracao de relatorio LaTeX.

Criado em: 11/12/2025
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Adicionar paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu.gerenciador_pedidos import GerenciadorPedidos, DadosPedidoMenu
from services.gestores.producao import GestorProducao
from utils.logs.gerenciador_logs import limpar_logs_inicializacao
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
import csv as csv_module


class ColetorMetricas:
    """Coleta metricas de multiplas rodadas de simulacao"""

    def __init__(self, arquivo_csv: str, num_rodadas: int = 5):
        self.arquivo_csv = arquivo_csv
        self.num_rodadas = num_rodadas
        self.resultados_seq = []
        self.resultados_pl = []

    def limpar_ambiente(self):
        """Limpa logs e comandas para ambiente limpo"""
        limpar_logs_inicializacao()
        apagar_todas_as_comandas()

    def carregar_pedidos(self) -> List[DadosPedidoMenu]:
        """Carrega pedidos do CSV"""
        gerenciador = GerenciadorPedidos()

        with open(self.arquivo_csv, 'r', encoding='utf-8') as f:
            reader = csv_module.DictReader(f)

            for row in reader:
                id_item = int(row['id'])
                tipo_item = row['tipo_produto'].strip().upper()
                quantidade = int(row['quantidade'])
                fim_jornada_str = row['fim_jornada'].strip()
                fim_jornada = datetime.strptime(fim_jornada_str, '%Y-%m-%d %H:%M:%S')

                gerenciador.registrar_pedido(
                    id_item=id_item,
                    tipo_item=tipo_item,
                    quantidade=quantidade,
                    fim_jornada=fim_jornada
                )

        return gerenciador.pedidos

    def contar_pedidos_logs(self) -> Dict:
        """Conta pedidos executados a partir dos logs"""
        dir_sucesso = Path('logs/equipamentos/sucesso')
        dir_erro = Path('logs/equipamentos/erros')

        pedidos_sucesso = set()
        pedidos_erro = set()

        # Logs de sucesso
        if dir_sucesso.exists():
            for arquivo in dir_sucesso.glob('*.log'):
                # Extrair ID do pedido do nome do arquivo
                nome = arquivo.stem
                if 'pedido:' in nome:
                    try:
                        # Formato: "ordem: X | pedido: Y"
                        partes = nome.split('|')
                        for parte in partes:
                            if 'pedido:' in parte:
                                pedido_id = int(parte.replace('pedido:', '').strip())
                                pedidos_sucesso.add(pedido_id)
                    except:
                        pass

        # Logs de erro
        if dir_erro.exists():
            for arquivo in dir_erro.glob('*.log'):
                nome = arquivo.stem
                if 'pedido:' in nome:
                    try:
                        partes = nome.split('|')
                        for parte in partes:
                            if 'pedido:' in parte:
                                pedido_id = int(parte.replace('pedido:', '').strip())
                                pedidos_erro.add(pedido_id)
                    except:
                        pass

        return {
            'sucesso': sorted(list(pedidos_sucesso)),
            'erro': sorted(list(pedidos_erro)),
            'total_sucesso': len(pedidos_sucesso),
            'total_erro': len(pedidos_erro)
        }

    def executar_rodada_seq(self, pedidos: List[DadosPedidoMenu], rodada: int) -> Dict:
        """Executa uma rodada do metodo sequencial"""
        self.limpar_ambiente()

        gestor = GestorProducao()

        inicio = time.time()
        inicio_cpu = time.process_time()

        sucesso = gestor.executar_sequencial(pedidos)

        fim = time.time()
        fim_cpu = time.process_time()

        # Coletar metricas dos logs
        metricas_logs = self.contar_pedidos_logs()

        return {
            'rodada': rodada,
            'metodo': 'SEQ',
            'tempo_wall': fim - inicio,
            'tempo_cpu': fim_cpu - inicio_cpu,
            'sucesso_geral': sucesso,
            'pedidos_sucesso': metricas_logs['sucesso'],
            'pedidos_erro': metricas_logs['erro'],
            'total_sucesso': metricas_logs['total_sucesso'],
            'total_erro': metricas_logs['total_erro'],
            'taxa_sucesso': metricas_logs['total_sucesso'] / 13 * 100
        }

    def executar_rodada_pl(self, pedidos: List[DadosPedidoMenu], rodada: int) -> Dict:
        """Executa uma rodada do metodo PL"""
        self.limpar_ambiente()

        gestor = GestorProducao()

        inicio = time.time()
        inicio_cpu = time.process_time()

        sucesso = gestor.executar_otimizado(pedidos)

        fim = time.time()
        fim_cpu = time.process_time()

        # Coletar metricas dos logs
        metricas_logs = self.contar_pedidos_logs()

        return {
            'rodada': rodada,
            'metodo': 'PL',
            'tempo_wall': fim - inicio,
            'tempo_cpu': fim_cpu - inicio_cpu,
            'sucesso_geral': sucesso,
            'pedidos_sucesso': metricas_logs['sucesso'],
            'pedidos_erro': metricas_logs['erro'],
            'total_sucesso': metricas_logs['total_sucesso'],
            'total_erro': metricas_logs['total_erro'],
            'taxa_sucesso': metricas_logs['total_sucesso'] / 13 * 100
        }

    def executar_coleta(self) -> Dict:
        """Executa coleta completa de metricas"""
        print("\n" + "="*70)
        print("COLETA DE METRICAS - SEQ vs PL")
        print("="*70)
        print(f"Arquivo CSV: {self.arquivo_csv}")
        print(f"Numero de rodadas: {self.num_rodadas}")
        print(f"Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*70)

        # Carregar pedidos uma vez
        pedidos = self.carregar_pedidos()
        print(f"\nPedidos carregados: {len(pedidos)}")

        # Executar rodadas SEQ
        print("\n" + "-"*50)
        print("EXECUTANDO METODO SEQUENCIAL")
        print("-"*50)

        for i in range(1, self.num_rodadas + 1):
            print(f"\n[SEQ] Rodada {i}/{self.num_rodadas}...")
            resultado = self.executar_rodada_seq(pedidos, i)
            self.resultados_seq.append(resultado)
            print(f"   Tempo: {resultado['tempo_wall']:.2f}s | Sucesso: {resultado['total_sucesso']}/13 ({resultado['taxa_sucesso']:.1f}%)")
            time.sleep(1)  # Pequena pausa entre rodadas

        # Executar rodadas PL
        print("\n" + "-"*50)
        print("EXECUTANDO METODO PL (OR-Tools)")
        print("-"*50)

        for i in range(1, self.num_rodadas + 1):
            print(f"\n[PL] Rodada {i}/{self.num_rodadas}...")
            resultado = self.executar_rodada_pl(pedidos, i)
            self.resultados_pl.append(resultado)
            print(f"   Tempo: {resultado['tempo_wall']:.2f}s | Sucesso: {resultado['total_sucesso']}/13 ({resultado['taxa_sucesso']:.1f}%)")
            time.sleep(1)

        # Calcular estatisticas agregadas
        stats = self.calcular_estatisticas()

        # Exibir resumo
        self.exibir_resumo(stats)

        # Salvar resultados
        self.salvar_resultados(stats)

        return stats

    def calcular_estatisticas(self) -> Dict:
        """Calcula estatisticas agregadas"""
        # SEQ
        tempos_seq = [r['tempo_wall'] for r in self.resultados_seq]
        taxas_seq = [r['taxa_sucesso'] for r in self.resultados_seq]
        sucessos_seq = [r['total_sucesso'] for r in self.resultados_seq]

        # PL
        tempos_pl = [r['tempo_wall'] for r in self.resultados_pl]
        taxas_pl = [r['taxa_sucesso'] for r in self.resultados_pl]
        sucessos_pl = [r['total_sucesso'] for r in self.resultados_pl]

        return {
            'seq': {
                'tempo_medio': sum(tempos_seq) / len(tempos_seq),
                'tempo_min': min(tempos_seq),
                'tempo_max': max(tempos_seq),
                'taxa_media': sum(taxas_seq) / len(taxas_seq),
                'sucesso_medio': sum(sucessos_seq) / len(sucessos_seq),
                'rodadas': self.resultados_seq
            },
            'pl': {
                'tempo_medio': sum(tempos_pl) / len(tempos_pl),
                'tempo_min': min(tempos_pl),
                'tempo_max': max(tempos_pl),
                'taxa_media': sum(taxas_pl) / len(taxas_pl),
                'sucesso_medio': sum(sucessos_pl) / len(sucessos_pl),
                'rodadas': self.resultados_pl
            },
            'comparacao': {
                'diferenca_tempo': sum(tempos_pl) / len(tempos_pl) - sum(tempos_seq) / len(tempos_seq),
                'diferenca_taxa': sum(taxas_pl) / len(taxas_pl) - sum(taxas_seq) / len(taxas_seq),
                'diferenca_sucesso': sum(sucessos_pl) / len(sucessos_pl) - sum(sucessos_seq) / len(sucessos_seq)
            },
            'metadata': {
                'arquivo_csv': self.arquivo_csv,
                'num_rodadas': self.num_rodadas,
                'total_pedidos': 13,
                'timestamp': datetime.now().isoformat()
            }
        }

    def exibir_resumo(self, stats: Dict):
        """Exibe resumo das metricas"""
        print("\n" + "="*70)
        print("RESUMO DAS METRICAS")
        print("="*70)

        print("\n{:<25} | {:>15} | {:>15}".format('Metrica', 'SEQ', 'PL'))
        print("-"*60)

        print("{:<25} | {:>15.2f}s | {:>15.2f}s".format(
            'Tempo medio',
            stats['seq']['tempo_medio'],
            stats['pl']['tempo_medio']
        ))
        print("{:<25} | {:>15.2f}s | {:>15.2f}s".format(
            'Tempo min',
            stats['seq']['tempo_min'],
            stats['pl']['tempo_min']
        ))
        print("{:<25} | {:>15.2f}s | {:>15.2f}s".format(
            'Tempo max',
            stats['seq']['tempo_max'],
            stats['pl']['tempo_max']
        ))
        print("{:<25} | {:>14.1f}% | {:>14.1f}%".format(
            'Taxa sucesso media',
            stats['seq']['taxa_media'],
            stats['pl']['taxa_media']
        ))
        print("{:<25} | {:>15.1f} | {:>15.1f}".format(
            'Pedidos sucesso medio',
            stats['seq']['sucesso_medio'],
            stats['pl']['sucesso_medio']
        ))

        print("\n" + "-"*60)
        print("DIFERENCA (PL - SEQ):")
        print(f"  Tempo: {stats['comparacao']['diferenca_tempo']:+.2f}s")
        print(f"  Taxa:  {stats['comparacao']['diferenca_taxa']:+.1f}%")
        print(f"  Pedidos: {stats['comparacao']['diferenca_sucesso']:+.1f}")

    def salvar_resultados(self, stats: Dict):
        """Salva resultados em JSON"""
        arquivo_saida = 'docs/comparacao/metricas_coletadas.json'

        # Garantir diretorio existe
        Path('docs/comparacao').mkdir(parents=True, exist_ok=True)

        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False, default=str)

        print(f"\nResultados salvos em: {arquivo_saida}")


def main():
    """Funcao principal"""
    arquivo_csv = 'data/csv/exemplo_pedidos.csv'

    if not os.path.exists(arquivo_csv):
        print(f"Arquivo nao encontrado: {arquivo_csv}")
        sys.exit(1)

    coletor = ColetorMetricas(arquivo_csv, num_rodadas=5)
    coletor.executar_coleta()


if __name__ == '__main__':
    main()
