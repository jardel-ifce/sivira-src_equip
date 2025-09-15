"""
Agente Monitor de Logs - Sistema SIVIRA
Um agente de IA simples para monitorar e analisar logs do sistema
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
from pathlib import Path


class AgenteMonitorLogs:
    """Agente inteligente para monitoramento e análise de logs"""
    
    def __init__(self, pasta_logs: str = "logs"):
        self.pasta_logs = pasta_logs
        self.padroes_erro = {
            'falta_material': r'(?i)(falta|insuficiente|sem estoque|material)',
            'equipamento_falha': r'(?i)(falha|erro|quebr|manutencao|parad)',
            'timeout': r'(?i)(timeout|tempo excedido|demorou)',
            'conexao': r'(?i)(conexao|rede|comunicacao)',
            'permissao': r'(?i)(permissao|acesso negado|nao autorizado)'
        }
        self.estatisticas = defaultdict(int)
        self.alertas = []
        
    def analisar_logs(self) -> Dict:
        """Analisa todos os logs e retorna insights"""
        resultados = {
            'total_arquivos': 0,
            'erros_por_tipo': Counter(),
            'padroes_detectados': [],
            'alertas_criticos': [],
            'recomendacoes': []
        }
        
        # Percorre todas as pastas de logs
        for pasta in ['erros', 'equipamentos', 'execucoes']:
            caminho = Path(self.pasta_logs) / pasta
            if caminho.exists():
                for arquivo in caminho.glob('*.log'):
                    resultados['total_arquivos'] += 1
                    self._analisar_arquivo(arquivo, resultados)
        
        # Gera recomendações baseadas nos padrões encontrados
        resultados['recomendacoes'] = self._gerar_recomendacoes(resultados)
        
        return resultados
    
    def _analisar_arquivo(self, arquivo: Path, resultados: Dict):
        """Analisa um arquivo de log específico"""
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
                # Detecta padrões de erro
                for tipo_erro, padrao in self.padroes_erro.items():
                    matches = re.findall(padrao, conteudo)
                    if matches:
                        resultados['erros_por_tipo'][tipo_erro] += len(matches)
                        
                # Detecta linhas com ERROR ou ERRO
                erros_criticos = re.findall(r'.*(?:ERROR|ERRO).*', conteudo)
                if erros_criticos:
                    resultados['alertas_criticos'].append({
                        'arquivo': str(arquivo.name),
                        'quantidade': len(erros_criticos),
                        'amostra': erros_criticos[0] if erros_criticos else None
                    })
                    
        except Exception as e:
            print(f"Erro ao analisar {arquivo}: {e}")
    
    def _gerar_recomendacoes(self, resultados: Dict) -> List[str]:
        """Gera recomendações baseadas nos padrões detectados"""
        recomendacoes = []
        
        erros = resultados['erros_por_tipo']
        
        if erros.get('falta_material', 0) > 5:
            recomendacoes.append(
                "🔴 CRÍTICO: Múltiplas faltas de material detectadas. "
                "Revisar níveis de estoque e pontos de reposição."
            )
            
        if erros.get('equipamento_falha', 0) > 3:
            recomendacoes.append(
                "⚠️ ATENÇÃO: Falhas recorrentes em equipamentos. "
                "Agendar manutenção preventiva urgente."
            )
            
        if erros.get('timeout', 0) > 0:
            recomendacoes.append(
                "⏱️ PERFORMANCE: Timeouts detectados. "
                "Verificar gargalos no processo e otimizar tempos de ciclo."
            )
            
        if len(resultados['alertas_criticos']) > 10:
            recomendacoes.append(
                "🚨 QUALIDADE: Alto volume de erros críticos. "
                "Realizar análise de causa raiz imediata."
            )
            
        if not recomendacoes:
            recomendacoes.append("✅ Sistema operando dentro dos parâmetros normais.")
            
        return recomendacoes
    
    def monitorar_tempo_real(self, intervalo_segundos: int = 60):
        """Monitora logs em tempo real (simulado para demonstração)"""
        import time
        
        print("🤖 Agente Monitor iniciado...")
        print(f"Monitorando pasta: {self.pasta_logs}")
        print("-" * 50)
        
        while True:
            try:
                resultados = self.analisar_logs()
                self._exibir_dashboard(resultados)
                
                # Aguarda próximo ciclo
                print(f"\n⏳ Próxima análise em {intervalo_segundos} segundos...")
                time.sleep(intervalo_segundos)
                
            except KeyboardInterrupt:
                print("\n👋 Monitor encerrado pelo usuário.")
                break
            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                time.sleep(5)
    
    def _exibir_dashboard(self, resultados: Dict):
        """Exibe dashboard com os resultados da análise"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("=" * 60)
        print("📊 DASHBOARD - AGENTE MONITOR DE LOGS")
        print("=" * 60)
        print(f"📁 Arquivos analisados: {resultados['total_arquivos']}")
        print(f"⏰ Última análise: {datetime.now().strftime('%H:%M:%S')}")
        
        print("\n📈 DISTRIBUIÇÃO DE ERROS:")
        print("-" * 40)
        for tipo, quantidade in resultados['erros_por_tipo'].items():
            barra = "█" * min(quantidade, 20)
            print(f"{tipo:20} | {barra} ({quantidade})")
        
        if resultados['alertas_criticos']:
            print("\n🚨 ALERTAS CRÍTICOS:")
            print("-" * 40)
            for alerta in resultados['alertas_criticos'][:5]:  # Top 5
                print(f"• {alerta['arquivo']}: {alerta['quantidade']} erros")
        
        print("\n💡 RECOMENDAÇÕES DO AGENTE:")
        print("-" * 40)
        for rec in resultados['recomendacoes']:
            print(f"• {rec}")
        
        print("=" * 60)
    
    def gerar_relatorio_json(self, arquivo_saida: str = "relatorio_agente.json"):
        """Gera relatório em formato JSON para integração com outros sistemas"""
        resultados = self.analisar_logs()
        
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'analise': resultados,
            'metricas': {
                'total_erros': sum(resultados['erros_por_tipo'].values()),
                'tipos_erro_unicos': len(resultados['erros_por_tipo']),
                'arquivos_com_erro': len(resultados['alertas_criticos'])
            }
        }
        
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Relatório salvo em: {arquivo_saida}")
        return relatorio


# Exemplo de uso
if __name__ == "__main__":
    print("🚀 Iniciando Agente Monitor de Logs...")
    
    agente = AgenteMonitorLogs()
    
    # Análise única
    print("\n📋 Executando análise inicial...")
    resultados = agente.analisar_logs()
    agente._exibir_dashboard(resultados)
    
    # Pergunta se deseja monitoramento contínuo
    resposta = input("\n🔄 Deseja iniciar monitoramento contínuo? (s/n): ")
    if resposta.lower() == 's':
        agente.monitorar_tempo_real(intervalo_segundos=30)