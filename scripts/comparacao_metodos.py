#!/usr/bin/env python3
"""
Script de Comparação: Método Sequencial vs Otimizado (PL)
==========================================================

Executa duas simulações usando pedidos de um arquivo CSV e compara:
- Tempo de execução
- Makespan (tempo total de produção)
- Utilização de equipamentos
- Métricas de qualidade da solução

Enfoque acadêmico para análise científica de desempenho.
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import csv as csv_module

# Adicionar paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu.gerenciador_pedidos import GerenciadorPedidos, DadosPedidoMenu
from services.gestores.producao import GestorProducao
from utils.logs.gerenciador_logs import limpar_logs_inicializacao
from utils.comandas.limpador_comandas import apagar_todas_as_comandas


class ComparadorMetodos:
    """Compara métodos de execução sequencial vs otimizado"""

    def __init__(self, arquivo_csv: str):
        self.arquivo_csv = arquivo_csv
        self.resultados = {
            'sequencial': {},
            'otimizado': {},
            'comparacao': {}
        }
        self.dir_logs_sequencial = None
        self.dir_logs_otimizado = None

    def limpar_ambiente(self):
        """Limpa logs e comandas para ambiente limpo"""
        print("\n🧹 Limpando ambiente...")
        limpar_logs_inicializacao()
        apagar_todas_as_comandas()
        print("✅ Ambiente limpo!")

    def carregar_pedidos_csv(self) -> List[DadosPedidoMenu]:
        """Carrega pedidos do arquivo CSV usando o Gerenciador"""
        print(f"\n📄 Carregando pedidos de: {self.arquivo_csv}")

        # Criar gerenciador
        gerenciador = GerenciadorPedidos()

        try:
            with open(self.arquivo_csv, 'r', encoding='utf-8') as f:
                reader = csv_module.DictReader(f)

                for row in reader:
                    id_item = int(row['id'])
                    tipo_item = row['tipo_produto'].strip().upper()
                    quantidade = int(row['quantidade'])
                    fim_jornada_str = row['fim_jornada'].strip()

                    # Parse do datetime
                    fim_jornada = datetime.strptime(fim_jornada_str, '%Y-%m-%d %H:%M:%S')

                    # Registra usando o gerenciador (que cuida de inicio_jornada, arquivo, etc)
                    sucesso, mensagem = gerenciador.registrar_pedido(
                        id_item=id_item,
                        tipo_item=tipo_item,
                        quantidade=quantidade,
                        fim_jornada=fim_jornada
                    )

                    if sucesso:
                        print(f"   ✓ Pedido {id_item}: {quantidade} unidades - {mensagem}")
                    else:
                        print(f"   ✗ Pedido {id_item}: {mensagem}")
                        raise ValueError(f"Falha ao registrar pedido {id_item}: {mensagem}")

        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {self.arquivo_csv}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erro ao carregar CSV: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        pedidos = gerenciador.pedidos
        print(f"✅ {len(pedidos)} pedidos carregados!")
        return pedidos

    def executar_sequencial(self, pedidos: List[DadosPedidoMenu]) -> Dict:
        """Executa método sequencial e coleta métricas"""
        print("\n" + "="*80)
        print("🔄 EXECUTANDO MÉTODO SEQUENCIAL")
        print("="*80)

        self.limpar_ambiente()

        # Inicializar gestor
        gestor = GestorProducao()

        # Marcar início
        inicio_execucao = time.time()
        inicio_cpu = time.process_time()

        # Executar
        print("\n⏱️ Iniciando execução sequencial...")
        sucesso = gestor.executar_sequencial(pedidos)

        # Marcar fim
        fim_execucao = time.time()
        fim_cpu = time.process_time()

        # Calcular tempos
        tempo_wall_clock = fim_execucao - inicio_execucao
        tempo_cpu = fim_cpu - inicio_cpu

        print(f"\n{'✅' if sucesso else '❌'} Execução sequencial {'concluída' if sucesso else 'falhou'}!")
        print(f"⏱️ Tempo wall-clock: {tempo_wall_clock:.2f}s")
        print(f"⏱️ Tempo CPU: {tempo_cpu:.2f}s")

        # Coletar métricas dos logs
        metricas = self.extrair_metricas_logs('sequencial')
        metricas['tempo_execucao'] = tempo_wall_clock
        metricas['tempo_cpu'] = tempo_cpu
        metricas['sucesso'] = sucesso
        metricas['timestamp'] = datetime.now().isoformat()

        # Copiar logs para diretório separado
        self.preservar_logs('sequencial')

        return metricas

    def executar_otimizado(self, pedidos: List[DadosPedidoMenu]) -> Dict:
        """Executa método otimizado (PL) e coleta métricas"""
        print("\n" + "="*80)
        print("🚀 EXECUTANDO MÉTODO OTIMIZADO (PL)")
        print("="*80)

        self.limpar_ambiente()

        # Verificar OR-Tools
        try:
            from ortools.linear_solver import pywraplp
            print("✅ OR-Tools disponível")
        except ImportError:
            print("❌ OR-Tools não disponível!")
            return {'erro': 'OR-Tools não instalado', 'sucesso': False}

        # Inicializar gestor
        gestor = GestorProducao()

        # Marcar início
        inicio_execucao = time.time()
        inicio_cpu = time.process_time()

        # Executar
        print("\n⏱️ Iniciando execução otimizada (PL)...")
        sucesso = gestor.executar_otimizado(pedidos)

        # Marcar fim
        fim_execucao = time.time()
        fim_cpu = time.process_time()

        # Calcular tempos
        tempo_wall_clock = fim_execucao - inicio_execucao
        tempo_cpu = fim_cpu - inicio_cpu

        print(f"\n{'✅' if sucesso else '❌'} Execução otimizada {'concluída' if sucesso else 'falhou'}!")
        print(f"⏱️ Tempo wall-clock: {tempo_wall_clock:.2f}s")
        print(f"⏱️ Tempo CPU: {tempo_cpu:.2f}s")

        # Coletar métricas dos logs
        metricas = self.extrair_metricas_logs('otimizado')
        metricas['tempo_execucao'] = tempo_wall_clock
        metricas['tempo_cpu'] = tempo_cpu
        metricas['sucesso'] = sucesso
        metricas['timestamp'] = datetime.now().isoformat()

        # Copiar logs para diretório separado
        self.preservar_logs('otimizado')

        return metricas

    def extrair_metricas_logs(self, metodo: str) -> Dict:
        """Extrai métricas dos logs de equipamentos"""
        print(f"\n📊 Extraindo métricas dos logs ({metodo})...")

        metricas = {
            'total_ocupacoes': 0,
            'equipamentos_utilizados': set(),
            'makespan_minutos': 0,
            'inicio_producao': None,
            'fim_producao': None,
            'pedidos_executados': set(),
            'atividades_executadas': set(),
            'ocupacoes_por_equipamento': {},
            'utilizacao_equipamentos': {}
        }

        # Buscar logs de sucesso
        dir_logs = Path('logs/equipamentos/sucesso')

        if not dir_logs.exists():
            print("⚠️ Diretório de logs não encontrado")
            return metricas

        arquivos_log = list(dir_logs.glob('*.log'))
        print(f"   Encontrados {len(arquivos_log)} arquivo(s) de log")

        for arquivo in arquivos_log:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    linhas = f.readlines()

                    for linha in linhas:
                        if '|' not in linha:
                            continue

                        # Parse da linha (formato: ordem | pedido | atividade | item | nome_ativ | equip | inicio | fim)
                        partes = [p.strip() for p in linha.split('|')]

                        if len(partes) < 8:
                            continue

                        try:
                            ordem = int(partes[0])
                            pedido = int(partes[1])
                            atividade = int(partes[2])
                            equipamento = partes[5]
                            inicio_str = partes[6]
                            fim_str = partes[7]

                            # Parse dos timestamps (formato: HH:MM [DD/MM])
                            inicio = self.parse_timestamp(inicio_str)
                            fim = self.parse_timestamp(fim_str)

                            if inicio and fim:
                                # Atualizar métricas
                                metricas['total_ocupacoes'] += 1
                                metricas['equipamentos_utilizados'].add(equipamento)
                                metricas['pedidos_executados'].add(pedido)
                                metricas['atividades_executadas'].add((pedido, atividade))

                                # Contabilizar por equipamento
                                if equipamento not in metricas['ocupacoes_por_equipamento']:
                                    metricas['ocupacoes_por_equipamento'][equipamento] = 0
                                metricas['ocupacoes_por_equipamento'][equipamento] += 1

                                # Atualizar makespan
                                if metricas['inicio_producao'] is None or inicio < metricas['inicio_producao']:
                                    metricas['inicio_producao'] = inicio
                                if metricas['fim_producao'] is None or fim > metricas['fim_producao']:
                                    metricas['fim_producao'] = fim

                        except (ValueError, IndexError):
                            continue

            except Exception as e:
                print(f"⚠️ Erro ao processar {arquivo.name}: {e}")
                continue

        # Calcular makespan
        if metricas['inicio_producao'] and metricas['fim_producao']:
            delta = metricas['fim_producao'] - metricas['inicio_producao']
            metricas['makespan_minutos'] = delta.total_seconds() / 60
            metricas['inicio_producao'] = metricas['inicio_producao'].isoformat()
            metricas['fim_producao'] = metricas['fim_producao'].isoformat()

        # Converter sets para listas (para JSON)
        metricas['equipamentos_utilizados'] = list(metricas['equipamentos_utilizados'])
        metricas['pedidos_executados'] = list(metricas['pedidos_executados'])
        metricas['atividades_executadas'] = len(metricas['atividades_executadas'])

        print(f"✅ Métricas extraídas:")
        print(f"   • Ocupações: {metricas['total_ocupacoes']}")
        print(f"   • Equipamentos: {len(metricas['equipamentos_utilizados'])}")
        print(f"   • Makespan: {metricas['makespan_minutos']:.2f} min")
        print(f"   • Pedidos: {len(metricas['pedidos_executados'])}")
        print(f"   • Atividades: {metricas['atividades_executadas']}")

        return metricas

    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp no formato HH:MM [DD/MM]"""
        import re

        match = re.match(r'(\d+):(\d+) \[(\d+)/(\d+)\]', timestamp_str)
        if match:
            hora, minuto, dia, mes = match.groups()
            # Assumir ano 2024
            return datetime(2024, int(mes), int(dia), int(hora), int(minuto))
        return None

    def preservar_logs(self, metodo: str):
        """Copia logs para diretório de preservação"""
        import shutil

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dir_destino = Path(f'logs/comparacao_{metodo}_{timestamp}')
        dir_destino.mkdir(parents=True, exist_ok=True)

        # Copiar logs de equipamentos
        dir_equipamentos = Path('logs/equipamentos')
        if dir_equipamentos.exists():
            shutil.copytree(dir_equipamentos, dir_destino / 'equipamentos', dirs_exist_ok=True)

        print(f"📁 Logs preservados em: {dir_destino}")

        if metodo == 'sequencial':
            self.dir_logs_sequencial = str(dir_destino)
        else:
            self.dir_logs_otimizado = str(dir_destino)

    def comparar_resultados(self):
        """Compara resultados de ambos os métodos"""
        print("\n" + "="*80)
        print("📊 COMPARAÇÃO DE RESULTADOS")
        print("="*80)

        seq = self.resultados['sequencial']
        otim = self.resultados['otimizado']

        # Calcular comparações
        comp = {
            'speedup_makespan': None,
            'reducao_makespan_pct': None,
            'diferenca_tempo_execucao': None,
            'diferenca_ocupacoes': None,
            'diferenca_equipamentos': None,
            'melhor_metodo': None
        }

        if seq.get('makespan_minutos') and otim.get('makespan_minutos'):
            makespan_seq = seq['makespan_minutos']
            makespan_otim = otim['makespan_minutos']

            comp['speedup_makespan'] = makespan_seq / makespan_otim if makespan_otim > 0 else None
            comp['reducao_makespan_pct'] = ((makespan_seq - makespan_otim) / makespan_seq * 100) if makespan_seq > 0 else None
            comp['melhor_metodo'] = 'otimizado' if makespan_otim < makespan_seq else 'sequencial'

        if seq.get('tempo_execucao') and otim.get('tempo_execucao'):
            comp['diferenca_tempo_execucao'] = otim['tempo_execucao'] - seq['tempo_execucao']

        if seq.get('total_ocupacoes') and otim.get('total_ocupacoes'):
            comp['diferenca_ocupacoes'] = otim['total_ocupacoes'] - seq['total_ocupacoes']

        if seq.get('equipamentos_utilizados') and otim.get('equipamentos_utilizados'):
            comp['diferenca_equipamentos'] = len(otim['equipamentos_utilizados']) - len(seq['equipamentos_utilizados'])

        self.resultados['comparacao'] = comp

        # Exibir resumo
        print("\n📈 RESUMO COMPARATIVO:")
        print(f"\n{'Métrica':<40} | {'Sequencial':>15} | {'Otimizado':>15} | {'Diferença':>15}")
        print("-" * 90)

        print(f"{'Tempo de execução (s)':<40} | {seq.get('tempo_execucao', 0):>15.2f} | {otim.get('tempo_execucao', 0):>15.2f} | {comp.get('diferenca_tempo_execucao', 0):>15.2f}")
        print(f"{'Makespan (min)':<40} | {seq.get('makespan_minutos', 0):>15.2f} | {otim.get('makespan_minutos', 0):>15.2f} | {otim.get('makespan_minutos', 0) - seq.get('makespan_minutos', 0):>15.2f}")
        print(f"{'Total de ocupações':<40} | {seq.get('total_ocupacoes', 0):>15} | {otim.get('total_ocupacoes', 0):>15} | {comp.get('diferenca_ocupacoes', 0):>15}")
        print(f"{'Equipamentos utilizados':<40} | {len(seq.get('equipamentos_utilizados', [])):>15} | {len(otim.get('equipamentos_utilizados', [])):>15} | {comp.get('diferenca_equipamentos', 0):>15}")
        print(f"{'Pedidos executados':<40} | {len(seq.get('pedidos_executados', [])):>15} | {len(otim.get('pedidos_executados', [])):>15} | {len(otim.get('pedidos_executados', [])) - len(seq.get('pedidos_executados', [])):>15}")
        print(f"{'Atividades executadas':<40} | {seq.get('atividades_executadas', 0):>15} | {otim.get('atividades_executadas', 0):>15} | {otim.get('atividades_executadas', 0) - seq.get('atividades_executadas', 0):>15}")

        if comp.get('speedup_makespan'):
            print(f"\n🚀 Speedup (makespan): {comp['speedup_makespan']:.2f}x")

        if comp.get('reducao_makespan_pct'):
            print(f"📉 Redução de makespan: {comp['reducao_makespan_pct']:.2f}%")

        if comp.get('melhor_metodo'):
            print(f"\n🏆 Melhor método (makespan): {comp['melhor_metodo'].upper()}")

    def salvar_resultados(self, arquivo_saida: str = 'data/metricas_comparacao.json'):
        """Salva resultados em arquivo JSON"""
        print(f"\n💾 Salvando resultados em: {arquivo_saida}")

        # Adicionar metadados
        self.resultados['metadados'] = {
            'arquivo_csv': self.arquivo_csv,
            'timestamp_execucao': datetime.now().isoformat(),
            'dir_logs_sequencial': self.dir_logs_sequencial,
            'dir_logs_otimizado': self.dir_logs_otimizado
        }

        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, indent=2, ensure_ascii=False)

        print(f"✅ Resultados salvos!")

    def executar_comparacao(self):
        """Executa comparação completa"""
        print("\n" + "="*80)
        print("🎯 COMPARAÇÃO DE MÉTODOS: SEQUENCIAL vs OTIMIZADO (PL)")
        print("="*80)
        print(f"📄 Arquivo CSV: {self.arquivo_csv}")
        print(f"⏰ Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        # Carregar pedidos
        pedidos = self.carregar_pedidos_csv()

        # Executar sequencial
        self.resultados['sequencial'] = self.executar_sequencial(pedidos)

        # Pausa entre execuções
        print("\n⏸️ Aguardando 3 segundos entre execuções...")
        time.sleep(3)

        # Executar otimizado
        self.resultados['otimizado'] = self.executar_otimizado(pedidos)

        # Comparar
        self.comparar_resultados()

        # Salvar
        self.salvar_resultados()

        print("\n" + "="*80)
        print("✅ COMPARAÇÃO CONCLUÍDA!")
        print("="*80)


def main():
    """Função principal"""
    arquivo_csv = 'data/csv/exemplo_pedidos.csv'

    if not os.path.exists(arquivo_csv):
        print(f"❌ Arquivo não encontrado: {arquivo_csv}")
        sys.exit(1)

    comparador = ComparadorMetodos(arquivo_csv)
    comparador.executar_comparacao()

    print("\n📝 Próximos passos:")
    print("   1. Verificar logs preservados")
    print("   2. Analisar data/metricas_comparacao.json")
    print("   3. Gerar relatório acadêmico")


if __name__ == '__main__':
    main()
