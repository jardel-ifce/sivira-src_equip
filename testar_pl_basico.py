"""
Teste Básico do Método Otimizado com PL
========================================

Testa a execução do método otimizado usando apenas 2 pedidos simples
para verificar se a integração com OtimizadorIntegrado está funcionando.
"""

from menu.gerenciador_pedidos import GerenciadorPedidos
from services.gestores.producao.gestor_producao import GestorProducao
from datetime import datetime


def testar_pl_basico():
    """Teste básico com 2 pedidos"""

    print("=" * 80)
    print("TESTE BÁSICO: Método Otimizado com PL (2 pedidos)")
    print("=" * 80)

    # Limpar logs antigos
    import os
    import shutil
    if os.path.exists('logs/equipamentos'):
        shutil.rmtree('logs/equipamentos')
    if os.path.exists('data/comandas'):
        shutil.rmtree('data/comandas')

    # Registrar 2 pedidos simples
    gerenciador = GerenciadorPedidos()

    print("\n📋 Registrando pedidos de teste...")

    # Pedido 1: ID 1004 (20 unidades)
    sucesso1, msg1 = gerenciador.registrar_pedido(
        id_item=1004,
        tipo_item='PRODUTO',
        quantidade=20,
        fim_jornada=datetime(2024, 12, 31, 7, 0, 0)
    )
    print(f"   Pedido 1004: {'✅' if sucesso1 else '❌'} {msg1}")

    # Pedido 2: ID 1005 (15 unidades)
    sucesso2, msg2 = gerenciador.registrar_pedido(
        id_item=1005,
        tipo_item='PRODUTO',
        quantidade=15,
        fim_jornada=datetime(2024, 12, 31, 7, 0, 0)
    )
    print(f"   Pedido 1005: {'✅' if sucesso2 else '❌'} {msg2}")

    if not (sucesso1 and sucesso2):
        print("\n❌ Falha ao registrar pedidos!")
        return False

    # Obter pedidos registrados
    pedidos_registrados = gerenciador.obter_pedidos_ordem_atual()
    print(f"\n✅ {len(pedidos_registrados)} pedidos registrados")

    # Executar com método otimizado
    print("\n" + "=" * 80)
    print("EXECUTANDO MÉTODO OTIMIZADO (PL)")
    print("=" * 80 + "\n")

    gestor = GestorProducao()
    sucesso = gestor.executar_otimizado(pedidos_registrados)

    print("\n" + "=" * 80)
    if sucesso:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")

        # Verificar logs gerados
        logs_dir = 'logs/equipamentos'
        if os.path.exists(logs_dir):
            logs = os.listdir(logs_dir)
            print(f"\n📝 Logs gerados: {len(logs)} arquivo(s)")
            for log in sorted(logs):
                print(f"   - {log}")

        # Verificar comandas geradas
        comandas_dir = 'data/comandas'
        if os.path.exists(comandas_dir):
            comandas = os.listdir(comandas_dir)
            print(f"\n📋 Comandas geradas: {len(comandas)} arquivo(s)")
            for comanda in sorted(comandas):
                print(f"   - {comanda}")

        # Mostrar estatísticas
        if hasattr(gestor.executor_pedidos, 'estatisticas_execucao'):
            stats = gestor.executor_pedidos.estatisticas_execucao
            print(f"\n📊 ESTATÍSTICAS:")
            print(f"   Modo: {stats.get('modo', 'N/A')}")
            print(f"   Total pedidos: {stats.get('total_pedidos', 0)}")
            print(f"   Pedidos otimizados (PL): {stats.get('pedidos_otimizados', 0)}")
            print(f"   Pedidos sequenciais: {stats.get('pedidos_sequenciais', 0)}")
            print(f"   Status solver: {stats.get('status_solver', 'N/A')}")
            print(f"   Tempo otimização: {stats.get('tempo_otimizacao', 0):.2f}s")
            print(f"   Tempo total: {stats.get('tempo_execucao', 0):.2f}s")
            if stats.get('funcao_objetivo'):
                print(f"   Makespan: {stats.get('funcao_objetivo')}min")

    else:
        print("❌ TESTE FALHOU!")

    print("=" * 80)

    return sucesso


if __name__ == "__main__":
    sucesso = testar_pl_basico()
    exit(0 if sucesso else 1)
