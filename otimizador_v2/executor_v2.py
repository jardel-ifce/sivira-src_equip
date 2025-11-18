"""
ExecutorV2 - Adaptador de Compatibilidade
==========================================

Adaptador que mantém a interface do ExecutorV2 original (esperada pelo menu)
mas usa o novo ExecutorUnificadoPL internamente.

Interface compatível com:
- executor.inicializar()
- executor.configurador.gestor_almoxarifado
- executor.otimizar_pedidos(pedidos, timeout_segundos)
- executor.imprimir_resumo_solucao(solucao, pedidos)
- executor.comparar_com_baseline(solucao, num_pedidos)

Criado em: 18/11/2025
"""

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from utils.logs.logger_factory import setup_logger
from otimizador_v2.executor_unificado import ExecutorUnificadoPL

logger = setup_logger('ExecutorV2')


@dataclass
class SolucaoPLCompleta:
    """Classe de solução compatível com interface antiga."""
    status_solver: str
    pedidos_atendidos: int
    tempo_resolucao: float
    makespan_minutos: float
    estatisticas: dict
    pedidos_executados: List[int]
    pedidos_com_erro: List[int]


class ConfiguradorMock:
    """Mock do configurador para compatibilidade."""
    def __init__(self):
        self.gestor_almoxarifado = None
        self._inicializado = False

    def inicializar_almoxarifado(self):
        """Inicializa gestor de almoxarifado com dados reais."""
        try:
            from parser.parser_almoxarifado import ParserAlmoxarifado

            # Caminho para arquivo de itens
            caminho_itens = "data/almoxarifado/itens_almoxarifado.json"

            # Parser de almoxarifado
            parser_almoxarifado = ParserAlmoxarifado(caminho_itens)

            # Criar gestor completo (já cria almoxarifado e carrega itens)
            self.gestor_almoxarifado = parser_almoxarifado.criar_gestor()
            self._inicializado = True

            # Contar itens carregados
            num_itens = len(self.gestor_almoxarifado.almoxarifado.itens)
            logger.info(f"✅ Almoxarifado inicializado com {num_itens} itens")

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar almoxarifado: {e}")
            import traceback
            traceback.print_exc()
            return False


class ExecutorV2:
    """
    Adaptador de compatibilidade para o ExecutorUnificadoPL.

    Mantém a interface esperada pelo menu mas usa o novo sistema internamente.
    """

    def __init__(self):
        self.logger = setup_logger('ExecutorV2')

        # Executor unificado (novo sistema)
        self.executor_unificado = ExecutorUnificadoPL()

        # Configurador mock para compatibilidade
        self.configurador = ConfiguradorMock()

        # Estado
        self._inicializado = False
        self.ultimo_resultado = None

    def inicializar(self) -> bool:
        """
        Inicializa o executor (compatibilidade com interface antiga).

        Returns:
            True se inicializado com sucesso, False caso contrário
        """
        if self._inicializado:
            return True

        try:
            self.logger.info("🔧 Inicializando ExecutorV2 (usando ExecutorUnificadoPL)...")

            # Inicializar almoxarifado
            if not self.configurador.inicializar_almoxarifado():
                return False

            self._inicializado = True
            self.logger.info("✅ ExecutorV2 inicializado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar ExecutorV2: {e}")
            return False

    def otimizar_pedidos(
        self,
        pedidos: List,
        timeout_segundos: int = 600
    ) -> Optional[SolucaoPLCompleta]:
        """
        Otimiza e executa pedidos usando o ExecutorUnificadoPL.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            timeout_segundos: Timeout para otimização (ignorado por enquanto)

        Returns:
            SolucaoPLCompleta com resultados da execução
        """
        if not self._inicializado:
            self.logger.error("❌ ExecutorV2 não foi inicializado!")
            return None

        try:
            self.logger.info(f"🚀 Otimizando {len(pedidos)} pedidos com ExecutorUnificadoPL...")

            # Executar usando o novo sistema
            inicio_jornada = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
            resultado = self.executor_unificado.otimizar_e_executar(pedidos, inicio_jornada)

            # Guardar para uso posterior
            self.ultimo_resultado = resultado

            # Verificar se houve sucesso
            if resultado.get('status') != 'CONCLUIDO':
                self.logger.error(f"❌ Otimização falhou: {resultado.get('status')}")

                # Retornar solução vazia indicando falha
                return SolucaoPLCompleta(
                    status_solver="FALHA",
                    pedidos_atendidos=0,
                    tempo_resolucao=resultado.get('estatisticas_gerais', {}).get('tempo_total', 0),
                    makespan_minutos=0,
                    estatisticas={},
                    pedidos_executados=[],
                    pedidos_com_erro=[p.id_pedido for p in pedidos]
                )

            # Extrair dados da execução
            stats = resultado['estatisticas_gerais']
            exec_result = resultado['execucao']

            # Calcular makespan (tempo total usado)
            # Para modo determinístico, é a diferença entre o último fim e primeiro início
            makespan_minutos = 0
            if resultado.get('horarios_calculados'):
                todos_horarios = []
                for horarios_pedido in resultado['horarios_calculados'].values():
                    for horario_info in horarios_pedido.values():
                        # horario_info é dict com 'inicio', 'fim', 'duracao_min'
                        if isinstance(horario_info, dict):
                            duracao = horario_info.get('duracao_min', 0)
                            todos_horarios.append(duracao)

                if todos_horarios:
                    makespan_minutos = sum(todos_horarios)

            # Criar solução compatível
            solucao = SolucaoPLCompleta(
                status_solver="OTIMO" if stats['taxa_sucesso'] > 80 else "VIAVEL",
                pedidos_atendidos=stats['pedidos_sucesso'],
                tempo_resolucao=stats['tempo_total'],
                makespan_minutos=makespan_minutos if makespan_minutos > 0 else stats['tempo_execucao'] * 60,
                estatisticas={
                    'modo_detectado': resultado['modo'],
                    'metodo_otimizacao': resultado['otimizacao'].get('metodo', 'N/A'),
                    'tempo_otimizacao': stats['tempo_otimizacao'],
                    'tempo_execucao': stats['tempo_execucao'],
                    'taxa_sucesso': stats['taxa_sucesso']
                },
                pedidos_executados=exec_result['pedidos_executados'],
                pedidos_com_erro=exec_result['pedidos_com_erro']
            )

            self.logger.info(
                f"✅ Otimização concluída: {solucao.pedidos_atendidos}/{len(pedidos)} pedidos "
                f"({stats['taxa_sucesso']:.1f}%)"
            )

            return solucao

        except Exception as e:
            self.logger.error(f"❌ Erro na otimização: {e}")
            import traceback
            traceback.print_exc()
            return None

    def imprimir_resumo_solucao(self, solucao: SolucaoPLCompleta, pedidos: List):
        """
        Imprime resumo da solução (compatibilidade com interface antiga).

        Args:
            solucao: Objeto SolucaoPLCompleta
            pedidos: Lista de pedidos
        """
        print("\n" + "=" * 70)
        print("📊 RESUMO DA SOLUÇÃO PL v2.0")
        print("=" * 70)

        print(f"\n✅ Pedidos executados com sucesso: {solucao.pedidos_atendidos}/{len(pedidos)}")

        if solucao.pedidos_executados:
            print(f"   IDs: {', '.join(map(str, solucao.pedidos_executados))}")

        if solucao.pedidos_com_erro:
            print(f"\n❌ Pedidos com erro: {len(solucao.pedidos_com_erro)}")
            print(f"   IDs: {', '.join(map(str, solucao.pedidos_com_erro))}")

        # Detalhes da otimização
        if 'modo_detectado' in solucao.estatisticas:
            print(f"\n🔍 Modo detectado: {solucao.estatisticas['modo_detectado']}")

        if 'metodo_otimizacao' in solucao.estatisticas:
            print(f"🎯 Método de otimização: {solucao.estatisticas['metodo_otimizacao']}")

        print("\n" + "=" * 70)

    def comparar_com_baseline(self, solucao: SolucaoPLCompleta, num_pedidos: int):
        """
        Compara resultado com baseline esperado (compatibilidade).

        Args:
            solucao: Objeto SolucaoPLCompleta
            num_pedidos: Número total de pedidos
        """
        print("\n" + "=" * 70)
        print("📊 COMPARAÇÃO COM BASELINE")
        print("=" * 70)

        # Baseline: Sistema Sequencial ~84.6%
        taxa_baseline = 84.6
        taxa_obtida = (solucao.pedidos_atendidos / num_pedidos * 100) if num_pedidos > 0 else 0

        print(f"\n📈 Sistema Sequencial (baseline): ~{taxa_baseline:.1f}%")
        print(f"🎯 PL v2.0 (obtido): {taxa_obtida:.1f}%")

        diferenca = taxa_obtida - taxa_baseline

        if diferenca >= 0:
            print(f"\n✅ Resultado ACIMA do baseline (+{diferenca:.1f} pontos percentuais)")
        elif diferenca >= -5:
            print(f"\n✅ Resultado PRÓXIMO do baseline ({diferenca:.1f} pontos)")
        else:
            print(f"\n⚠️ Resultado ABAIXO do baseline ({diferenca:.1f} pontos)")

        print("\n💡 Nota: PL v2.0 Fase 1 usa ordenação por deadline (modo determinístico)")
        print("   Resultados similares ao Sequencial são esperados nesta fase.")

        print("\n" + "=" * 70)


# Função de conveniência para criação rápida
def criar_executor_v2() -> ExecutorV2:
    """
    Cria e inicializa um ExecutorV2.

    Returns:
        ExecutorV2 inicializado
    """
    executor = ExecutorV2()
    executor.inicializar()
    return executor
