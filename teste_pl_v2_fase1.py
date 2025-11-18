"""
Script de Teste - PL v2.0 Fase 1 (Modo Determinístico)
======================================================

Testa a implementação do PL v2.0 com o dataset atual (gaps=0).

Esperado:
- Detectar modo DETERMINISTICO
- Calcular horários fixos
- Otimizar ordem de execução
- Taxa de sucesso ~84.6% (similar ao Sequencial)

Criado em: 18/11/2025
"""

import sys
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from otimizador_v2.executor_unificado import ExecutorUnificadoPL
from services.gestores.producao.executor_pedidos import ExecutorPedidos
from models.pedidos.pedido_producao import PedidoDeProducao
from utils.logs.logger_factory import setup_logger

logger = setup_logger('TestePLv2')


def carregar_pedidos_do_menu():
    """
    Carrega pedidos usando a mesma abordagem do menu principal.
    Busca pedidos salvos ou cria pedidos de exemplo.
    """
    import json
    from pathlib import Path

    # Tentar carregar pedidos salvos
    arquivo_pedidos = "data/pedidos_salvos.json"

    if Path(arquivo_pedidos).exists():
        try:
            with open(arquivo_pedidos, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            pedidos = []
            for dados_pedido in dados.get('pedidos', []):
                pedido = PedidoDeProducao.from_dict(dados_pedido)
                pedidos.append(pedido)

            logger.info(f"✅ {len(pedidos)} pedidos carregados de {arquivo_pedidos}")
            return pedidos
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar pedidos salvos: {e}")

    # Se não conseguiu carregar, retornar lista vazia
    logger.warning("⚠️ Nenhum pedido salvo encontrado")
    return []


def main():
    """Executa teste do PL v2.0."""
    print("=" * 70)
    print("🧪 TESTE: PL v2.0 - Fase 1 (Modo Determinístico)")
    print("=" * 70)
    print()

    try:
        # Carregar pedidos
        logger.info("📦 Carregando pedidos...")
        pedidos = carregar_pedidos_do_menu()

        if not pedidos:
            logger.error("❌ Nenhum pedido carregado!")
            logger.info("💡 Execute o menu principal e crie pedidos primeiro")
            return

        logger.info(f"✅ {len(pedidos)} pedidos carregados")
        print()

        # Criar executor PL v2.0
        executor = ExecutorUnificadoPL()

        # Executar otimização e execução
        inicio_jornada = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)

        logger.info("🚀 Iniciando execução do PL v2.0...")
        print()

        resultado = executor.otimizar_e_executar(pedidos, inicio_jornada)

        print()
        print("=" * 70)
        print("📊 RESULTADOS")
        print("=" * 70)
        print()

        # Exibir resultados
        if resultado.get('status') == 'CONCLUIDO':
            stats = resultado['estatisticas_gerais']

            print(f"✅ Status: {resultado['status']}")
            print(f"🔍 Modo detectado: {resultado['modo']}")
            print()
            print(f"📊 Total de pedidos: {stats['total_pedidos']}")
            print(f"✅ Executados com sucesso: {stats['pedidos_sucesso']}")
            print(f"❌ Com erro: {stats['pedidos_erro']}")
            print(f"📈 Taxa de sucesso: {stats['taxa_sucesso']:.1f}%")
            print()
            print(f"⏱️ Tempo total: {stats['tempo_total']:.2f}s")
            print(f"   • Otimização: {stats['tempo_otimizacao']:.3f}s")
            print(f"   • Execução: {stats['tempo_execucao']:.2f}s")
            print()

            # Ordem de execução
            if 'otimizacao' in resultado:
                ordem = resultado['otimizacao']['ordem_execucao']
                print(f"🎯 Ordem de execução otimizada:")
                print(f"   {' → '.join(map(str, ordem))}")
                print()

            # Pedidos executados
            if 'execucao' in resultado:
                exec_result = resultado['execucao']
                print(f"✅ Pedidos executados:")
                print(f"   {', '.join(map(str, exec_result['pedidos_executados']))}")

                if exec_result['pedidos_com_erro']:
                    print()
                    print(f"❌ Pedidos com erro:")
                    print(f"   {', '.join(map(str, exec_result['pedidos_com_erro']))}")

            print()
            print("=" * 70)

            # Gerar e salvar relatório completo
            relatorio = executor.gerar_relatorio_completo(resultado)

            arquivo_relatorio = "logs/relatorio_pl_v2_teste.txt"
            Path("logs").mkdir(exist_ok=True)

            with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
                f.write(relatorio)
                f.write("\n\n")
                f.write("RESULTADO COMPLETO (JSON):\n")
                f.write("=" * 70 + "\n")
                import json
                f.write(json.dumps(resultado, indent=2, default=str, ensure_ascii=False))

            logger.info(f"📄 Relatório completo salvo em: {arquivo_relatorio}")

            # Comparação com Sistema Sequencial
            print()
            print("=" * 70)
            print("📊 COMPARAÇÃO COM SISTEMA SEQUENCIAL")
            print("=" * 70)
            print()

            # Nota: Comparação com Sequencial não disponível neste teste
            # (requer recarregar pedidos com estado limpo)
            print()
            print("=" * 70)
            print("📊 RESULTADO FINAL")
            print("=" * 70)
            print()
            print(f"Taxa de sucesso PL v2.0: {stats['taxa_sucesso']:.1f}%")
            print(f"Taxa esperada (similar ao Sequencial): ~84.6%")
            print()

            diferenca = stats['taxa_sucesso'] - 84.6
            if diferenca >= 0:
                print(f"✅ Resultado ACIMA do esperado (+{diferenca:.1f} pontos)")
            elif diferenca >= -5:
                print(f"✅ Resultado PRÓXIMO do esperado ({diferenca:.1f} pontos)")
            else:
                print(f"⚠️ Resultado ABAIXO do esperado ({diferenca:.1f} pontos)")

            print()
            print("=" * 70)

        else:
            print(f"❌ Status: {resultado['status']}")
            if 'erro' in resultado:
                print(f"❌ Erro: {resultado['erro']}")

    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
