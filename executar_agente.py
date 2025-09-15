"""
Executa o agente monitor e exibe resultados detalhados
"""

from agentes.monitor_logs import AgenteMonitorLogs
import json

print("=" * 70)
print("🤖 EXECUÇÃO DO AGENTE MONITOR DE LOGS - ANÁLISE COMPLETA")
print("=" * 70)

# Cria e executa o agente
agente = AgenteMonitorLogs()
resultados = agente.analisar_logs()

# Exibe estatísticas gerais
print(f"\n📊 ESTATÍSTICAS GERAIS:")
print(f"  • Total de arquivos analisados: {resultados['total_arquivos']}")
print(f"  • Total de erros detectados: {sum(resultados['erros_por_tipo'].values())}")
print(f"  • Arquivos com alertas críticos: {len(resultados['alertas_criticos'])}")

# Detalhamento dos tipos de erro
print(f"\n🔍 ANÁLISE DETALHADA POR TIPO DE ERRO:")
print("-" * 50)
for tipo_erro, quantidade in sorted(resultados['erros_por_tipo'].items(), key=lambda x: x[1], reverse=True):
    percentual = (quantidade / sum(resultados['erros_por_tipo'].values())) * 100 if resultados['erros_por_tipo'] else 0
    print(f"  {tipo_erro:20} : {quantidade:3} ocorrências ({percentual:.1f}%)")

# Lista todos os arquivos com erros críticos
if resultados['alertas_criticos']:
    print(f"\n🚨 ARQUIVOS COM ERROS CRÍTICOS ({len(resultados['alertas_criticos'])} arquivos):")
    print("-" * 50)
    for idx, alerta in enumerate(resultados['alertas_criticos'], 1):
        print(f"  {idx}. {alerta['arquivo']}")
        print(f"     Quantidade de erros: {alerta['quantidade']}")
        if alerta.get('amostra'):
            # Limita o tamanho da amostra para exibição
            amostra = alerta['amostra'][:100] + "..." if len(alerta['amostra']) > 100 else alerta['amostra']
            print(f"     Amostra: {amostra}")
        print()

# Recomendações do agente
print(f"\n💡 DIAGNÓSTICO E RECOMENDAÇÕES DO AGENTE:")
print("-" * 50)
for idx, rec in enumerate(resultados['recomendacoes'], 1):
    print(f"  {idx}. {rec}")

# Gera e salva relatório completo
print(f"\n📄 GERANDO RELATÓRIO DETALHADO...")
relatorio = agente.gerar_relatorio_json("relatorio_completo_agente.json")

# Resumo final
print(f"\n" + "=" * 70)
print("📈 RESUMO EXECUTIVO:")
print(f"  • Severidade: {'CRÍTICA' if len(resultados['alertas_criticos']) > 10 else 'MODERADA' if len(resultados['alertas_criticos']) > 5 else 'BAIXA'}")
print(f"  • Ação recomendada: {'Intervenção imediata necessária' if len(resultados['alertas_criticos']) > 10 else 'Monitorar e planejar manutenção' if len(resultados['alertas_criticos']) > 5 else 'Sistema operacional'}")
print(f"  • Relatório salvo em: relatorio_completo_agente.json")
print("=" * 70)