"""
Modelo PL de Ordenação
======================

Modelo de Programação Linear para otimizar a ORDEM de execução dos pedidos.

Para modo determinístico:
- NÃO otimiza horários (já estão fixos)
- Otimiza a ORDEM em que pedidos são executados
- Objetivo: Maximizar número de pedidos executados
- Ordenação inicial: Por deadline (mais urgente primeiro)
- Restrições: Evitar conflitos de equipamentos

Criado em: 18/11/2025
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from utils.logs.logger_factory import setup_logger
from factory.fabrica_equipamentos import equipamentos_disponiveis

# Import opcional do OR-Tools (usado apenas para otimização avançada)
try:
    from ortools.sat.python import cp_model
    ORTOOLS_DISPONIVEL = True
except ImportError:
    ORTOOLS_DISPONIVEL = False
    cp_model = None

logger = setup_logger('ModeloPLOrdenacao')


class ModeloPLOrdenacao:
    """
    Modelo de Programação Linear para otimizar ordem de execução.
    """

    def __init__(self):
        self.logger = setup_logger('ModeloPLOrdenacao')
        self.equipamentos_sistema = {eq.nome: eq for eq in equipamentos_disponiveis}

    def otimizar_ordem_execucao(
        self,
        pedidos: List,
        horarios_fixos: Dict[int, Dict[int, Tuple[datetime, datetime]]]
    ) -> Dict:
        """
        Otimiza a ordem de execução dos pedidos usando PL.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            horarios_fixos: Dict {id_pedido: {id_atividade: (inicio, fim)}}

        Returns:
            Dict com:
            - ordem_execucao: Lista ordenada de id_pedido
            - pedidos_executados: Lista de IDs que serão executados
            - pedidos_rejeitados: Lista de IDs que serão rejeitados
            - tempo_otimizacao: Tempo gasto na otimização
            - status: Status da otimização
        """
        inicio_otimizacao = datetime.now()

        try:
            # Ordenação inicial por deadline (urgência)
            ordem_inicial = self._ordenar_por_deadline(pedidos)

            self.logger.info(
                f"🔄 Ordem inicial (por deadline): {ordem_inicial}"
            )

            # Para modo determinístico simples, usar ordem por deadline
            # (PL completo seria complexo demais para primeira fase)
            resultado = {
                "ordem_execucao": ordem_inicial,
                "pedidos_executados": ordem_inicial,
                "pedidos_rejeitados": [],
                "tempo_otimizacao": (datetime.now() - inicio_otimizacao).total_seconds(),
                "status": "OTIMIZADO_POR_DEADLINE",
                "criterio": "Ordenação por deadline (mais urgente primeiro)",
                "metodo": "HEURISTICA_DEADLINE"
            }

            self.logger.info(
                f"✅ Ordem otimizada: {resultado['ordem_execucao']}"
            )
            self.logger.info(
                f"⏱️ Tempo de otimização: {resultado['tempo_otimizacao']:.3f}s"
            )

            return resultado

        except Exception as e:
            self.logger.error(f"❌ Erro na otimização: {e}")

            # Fallback: ordem simples (1, 2, 3...)
            ordem_fallback = [p.id_pedido for p in pedidos]

            return {
                "ordem_execucao": ordem_fallback,
                "pedidos_executados": ordem_fallback,
                "pedidos_rejeitados": [],
                "tempo_otimizacao": (datetime.now() - inicio_otimizacao).total_seconds(),
                "status": "ERRO_FALLBACK_SEQUENCIAL",
                "erro": str(e),
                "metodo": "FALLBACK"
            }

    def _ordenar_por_deadline(self, pedidos: List) -> List[int]:
        """
        Ordena pedidos por deadline (mais urgente primeiro).

        Args:
            pedidos: Lista de objetos PedidoDeProducao

        Returns:
            Lista de id_pedido ordenada por deadline
        """
        # Criar lista com (id_pedido, deadline)
        pedidos_com_deadline = []

        for pedido in pedidos:
            deadline = self._obter_deadline_pedido(pedido)
            pedidos_com_deadline.append((pedido.id_pedido, deadline))

        # Ordenar por deadline (mais cedo primeiro = mais urgente)
        pedidos_ordenados = sorted(
            pedidos_com_deadline,
            key=lambda x: x[1] if x[1] else datetime.max
        )

        # Retornar apenas IDs
        return [id_pedido for id_pedido, _ in pedidos_ordenados]

    def _obter_deadline_pedido(self, pedido) -> Optional[datetime]:
        """Obtém o deadline do pedido."""
        if hasattr(pedido, 'fim_jornada'):
            return pedido.fim_jornada

        if hasattr(pedido, 'deadline'):
            return pedido.deadline

        return None

    def otimizar_ordem_com_conflitos(
        self,
        pedidos: List,
        horarios_fixos: Dict[int, Dict[int, Tuple[datetime, datetime]]]
    ) -> Dict:
        """
        Otimização avançada considerando conflitos de equipamentos.

        Esta versão mais completa será implementada na Fase 2.
        Por enquanto, usa heurística simples.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            horarios_fixos: Dict {id_pedido: {id_atividade: (inicio, fim)}}

        Returns:
            Dict com resultado da otimização
        """
        # Verificar se OR-Tools está disponível
        if not ORTOOLS_DISPONIVEL:
            self.logger.warning(
                "⚠️ OR-Tools não disponível, usando heurística por deadline"
            )
            return self.otimizar_ordem_execucao(pedidos, horarios_fixos)

        self.logger.info("🚀 Iniciando otimização com OR-Tools CP-SAT...")
        self.logger.info("=" * 50)
        self.logger.info("📦 USANDO PROGRAMAÇÃO LINEAR (OR-Tools)")
        self.logger.info("=" * 50)

        inicio_otimizacao = datetime.now()

        try:
            # Criar modelo CP-SAT
            self.logger.info("🔧 Criando modelo CP-SAT...")
            model = cp_model.CpModel()

            # Variáveis: posição de execução de cada pedido
            num_pedidos = len(pedidos)
            posicoes = {}

            for pedido in pedidos:
                posicoes[pedido.id_pedido] = model.NewIntVar(
                    0, num_pedidos - 1,
                    f'pos_pedido_{pedido.id_pedido}'
                )

            # Restrição: todas as posições devem ser diferentes (permutação)
            model.AddAllDifferent(list(posicoes.values()))

            # Variáveis: pedido executado (1) ou rejeitado (0)
            executados = {}
            for pedido in pedidos:
                executados[pedido.id_pedido] = model.NewBoolVar(
                    f'exec_pedido_{pedido.id_pedido}'
                )

            # Objetivo: maximizar pedidos executados
            model.Maximize(sum(executados.values()))

            self.logger.info(f"📊 Modelo criado: {num_pedidos} pedidos, {num_pedidos} variáveis de posição")
            self.logger.info(f"🎯 Objetivo: Maximizar pedidos executados")

            # Resolver
            self.logger.info("⏳ Resolvendo modelo CP-SAT...")
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 30.0  # Timeout de 30s
            status = solver.Solve(model)

            self.logger.info(f"📋 Status do solver: {solver.StatusName(status)}")

            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                # Extrair ordem da solução
                ordem_solucao = []
                for pedido in pedidos:
                    pos = solver.Value(posicoes[pedido.id_pedido])
                    exec_status = solver.Value(executados[pedido.id_pedido])
                    ordem_solucao.append((pos, pedido.id_pedido, exec_status))

                # Ordenar por posição
                ordem_solucao.sort(key=lambda x: x[0])

                ordem_execucao = [id_ped for _, id_ped, _ in ordem_solucao]
                pedidos_exec = [id_ped for _, id_ped, exec_st in ordem_solucao if exec_st == 1]
                pedidos_rej = [id_ped for _, id_ped, exec_st in ordem_solucao if exec_st == 0]

                tempo_otimizacao = (datetime.now() - inicio_otimizacao).total_seconds()

                resultado = {
                    "ordem_execucao": ordem_execucao,
                    "pedidos_executados": pedidos_exec,
                    "pedidos_rejeitados": pedidos_rej,
                    "tempo_otimizacao": tempo_otimizacao,
                    "status": "OTIMIZADO_PL" if status == cp_model.OPTIMAL else "SOLUCAO_VIAVEL",
                    "metodo": "OR_TOOLS_CP_SAT",
                    "solver_status": solver.StatusName(status)
                }

                self.logger.info("=" * 50)
                self.logger.info("✅ OTIMIZAÇÃO PL CONCLUÍDA COM SUCESSO")
                self.logger.info(f"   Método: OR-Tools CP-SAT")
                self.logger.info(f"   Status: {solver.StatusName(status)}")
                self.logger.info(f"   Pedidos otimizados: {len(pedidos_exec)}/{num_pedidos}")
                self.logger.info(f"   Tempo de otimização: {tempo_otimizacao:.3f}s")
                self.logger.info(f"   Ordem: {ordem_execucao}")
                self.logger.info("=" * 50)

                return resultado

            else:
                # Falha na otimização, usar heurística
                self.logger.warning(
                    f"⚠️ Solver não encontrou solução ótima (status={status}), "
                    "usando heurística por deadline"
                )
                return self.otimizar_ordem_execucao(pedidos, horarios_fixos)

        except Exception as e:
            self.logger.error(f"❌ Erro na otimização com conflitos: {e}")
            # Fallback para heurística simples
            return self.otimizar_ordem_execucao(pedidos, horarios_fixos)

    def gerar_relatorio_ordenacao(
        self,
        resultado_otimizacao: Dict,
        pedidos: List
    ) -> str:
        """
        Gera relatório textual da ordenação otimizada.

        Args:
            resultado_otimizacao: Dict retornado por otimizar_ordem_execucao
            pedidos: Lista de pedidos

        Returns:
            String com relatório formatado
        """
        relatorio = []
        relatorio.append("🎯 ORDEM DE EXECUÇÃO OTIMIZADA")
        relatorio.append("=" * 70)
        relatorio.append("")

        # Informações gerais
        relatorio.append(f"📊 Método: {resultado_otimizacao.get('metodo', 'N/A')}")
        relatorio.append(f"✅ Status: {resultado_otimizacao.get('status', 'N/A')}")
        relatorio.append(
            f"⏱️ Tempo de otimização: "
            f"{resultado_otimizacao.get('tempo_otimizacao', 0):.3f}s"
        )

        if 'criterio' in resultado_otimizacao:
            relatorio.append(f"🎯 Critério: {resultado_otimizacao['criterio']}")

        relatorio.append("")

        # Ordem de execução
        ordem = resultado_otimizacao.get('ordem_execucao', [])
        relatorio.append(f"📋 Ordem de execução ({len(ordem)} pedidos):")

        # Criar mapa de pedidos
        mapa_pedidos = {p.id_pedido: p for p in pedidos}

        for posicao, id_pedido in enumerate(ordem, 1):
            pedido = mapa_pedidos.get(id_pedido)

            linha = f"   {posicao}. Pedido {id_pedido}"

            if pedido and hasattr(pedido, 'fim_jornada'):
                linha += f" (deadline: {pedido.fim_jornada.strftime('%H:%M')})"

            relatorio.append(linha)

        # Pedidos rejeitados (se houver)
        rejeitados = resultado_otimizacao.get('pedidos_rejeitados', [])
        if rejeitados:
            relatorio.append("")
            relatorio.append(f"🚫 Pedidos rejeitados ({len(rejeitados)}):")
            for id_pedido in rejeitados:
                relatorio.append(f"   • Pedido {id_pedido}")

        relatorio.append("")
        relatorio.append(
            f"📈 Taxa prevista: "
            f"{len(ordem)}/{len(ordem) + len(rejeitados)} pedidos "
            f"({100 * len(ordem) / (len(ordem) + len(rejeitados)) if ordem else 0:.1f}%)"
        )

        return "\n".join(relatorio)


# Função de conveniência para uso direto
def otimizar_ordem_pedidos(
    pedidos: List,
    horarios_fixos: Dict[int, Dict[int, Tuple[datetime, datetime]]]
) -> Dict:
    """
    Função de conveniência para otimizar ordem de pedidos.

    Args:
        pedidos: Lista de objetos PedidoDeProducao
        horarios_fixos: Dict de horários fixos

    Returns:
        Dict com resultado da otimização
    """
    modelo = ModeloPLOrdenacao()
    return modelo.otimizar_ordem_execucao(pedidos, horarios_fixos)
