"""
Executor Unificado PL v2.0
===========================

Orquestrador principal do sistema de otimização PL v2.0.

Fluxo de execução:
1. Detecta modo (DETERMINISTICO vs FLEXIVEL)
2. Calcula horários determinísticos (se aplicável)
3. Otimiza ordem de execução via PL
4. Executa pedidos na ordem otimizada
5. Retorna resultados consolidados

API pública:
- otimizar_e_executar(pedidos, inicio_jornada) -> Dict

Criado em: 18/11/2025
"""

from datetime import datetime
from typing import List, Dict, Optional
from utils.logs.logger_factory import setup_logger

# Importar componentes do PL v2.0
from otimizador_v2.detector_modo import (
    DetectorModo,
    ModoOtimizacao,
    detectar_modo_otimizacao
)
from otimizador_v2.calculador_horarios_deterministicos import (
    CalculadorHorariosDeterministicos,
    calcular_horarios_deterministicos
)
from otimizador_v2.modelo_pl_ordenacao import (
    ModeloPLOrdenacao,
    otimizar_ordem_pedidos
)
from otimizador_v2.aplicador_ordenacao import (
    AplicadorOrdenacao,
    executar_pedidos_ordenados
)

logger = setup_logger('ExecutorUnificadoPL')


class ExecutorUnificadoPL:
    """
    Executor unificado que coordena todo o fluxo de otimização e execução.
    """

    def __init__(self):
        self.logger = setup_logger('ExecutorUnificadoPL')

        # Componentes do sistema
        self.detector_modo = DetectorModo()
        self.calculador_horarios = CalculadorHorariosDeterministicos()
        self.modelo_pl = ModeloPLOrdenacao()
        self.aplicador = AplicadorOrdenacao()

        # Resultados intermediários (para debug/análise)
        self.modo_detectado = None
        self.estatisticas_modo = None
        self.horarios_calculados = None
        self.resultado_otimizacao = None
        self.resultado_execucao = None

    def otimizar_e_executar(
        self,
        pedidos: List,
        inicio_jornada: Optional[datetime] = None
    ) -> Dict:
        """
        API principal: otimiza e executa pedidos.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            inicio_jornada: Datetime do início da jornada (default: now)

        Returns:
            Dict com resultados completos:
            - modo: Modo detectado (DETERMINISTICO/FLEXIVEL)
            - horarios: Horários calculados (se deterministico)
            - ordem_otimizada: Ordem de execução otimizada
            - execucao: Resultados da execução
            - estatisticas: Estatísticas gerais
            - tempo_total: Tempo total do processo
        """
        self.logger.info("🚀 Iniciando ExecutorUnificadoPL v2.0")
        self.logger.info("=" * 70)

        tempo_inicio_total = datetime.now()

        if inicio_jornada is None:
            inicio_jornada = datetime.now()

        try:
            # FASE 1: Detecção de Modo
            self.logger.info("🔍 FASE 1: Detectando modo de otimização...")
            self.modo_detectado, self.estatisticas_modo = self.detector_modo.detectar_modo(
                pedidos
            )

            # FASE 2: Cálculo de Horários Determinísticos
            if self.modo_detectado == ModoOtimizacao.DETERMINISTICO:
                self.logger.info("📅 FASE 2: Calculando horários determinísticos...")
                self.horarios_calculados = self.calculador_horarios.calcular_horarios_fixos(
                    pedidos,
                    inicio_jornada
                )
            else:
                self.logger.info("⚠️ FASE 2: Modo FLEXIVEL - Fase 2 não implementada ainda")
                return {
                    "modo": self.modo_detectado.value,
                    "status": "ERRO",
                    "mensagem": "Modo FLEXIVEL não implementado na Fase 1",
                    "estatisticas_modo": self.estatisticas_modo
                }

            # FASE 3: Otimização da Ordem de Execução via PL (OR-Tools CP-SAT)
            self.logger.info("🎯 FASE 3: Otimizando ordem de execução via PL (OR-Tools)...")
            self.resultado_otimizacao = self.modelo_pl.otimizar_ordem_com_conflitos(
                pedidos,
                self.horarios_calculados
            )

            # FASE 4: Execução dos Pedidos
            self.logger.info("⚙️ FASE 4: Executando pedidos na ordem otimizada...")
            ordem_execucao = self.resultado_otimizacao['ordem_execucao']
            self.resultado_execucao = self.aplicador.executar_pedidos_em_ordem(
                pedidos,
                ordem_execucao
            )

            tempo_fim_total = datetime.now()
            tempo_total = (tempo_fim_total - tempo_inicio_total).total_seconds()

            # Consolidar resultados
            resultado_final = {
                "status": "CONCLUIDO",
                "modo": self.modo_detectado.value,
                "estatisticas_modo": self.estatisticas_modo,
                "horarios_calculados": self._serializar_horarios(self.horarios_calculados),
                "otimizacao": self.resultado_otimizacao,
                "execucao": self.resultado_execucao,
                "estatisticas_gerais": {
                    "total_pedidos": len(pedidos),
                    "pedidos_sucesso": self.resultado_execucao['pedidos_sucesso'],
                    "pedidos_erro": self.resultado_execucao['pedidos_erro'],
                    "taxa_sucesso": self.resultado_execucao['taxa_sucesso'],
                    "tempo_total": tempo_total,
                    "tempo_otimizacao": self.resultado_otimizacao.get('tempo_otimizacao', 0),
                    "tempo_execucao": self.resultado_execucao['tempo_total']
                },
                "inicio_processo": tempo_inicio_total,
                "fim_processo": tempo_fim_total
            }

            # Log final
            self.logger.info("=" * 70)
            self.logger.info("✅ PROCESSO CONCLUÍDO")
            self.logger.info(
                f"📊 Taxa de sucesso: {resultado_final['estatisticas_gerais']['taxa_sucesso']:.1f}%"
            )
            self.logger.info(
                f"⏱️ Tempo total: {tempo_total:.2f}s"
            )
            self.logger.info("=" * 70)

            return resultado_final

        except Exception as e:
            tempo_fim_total = datetime.now()
            tempo_total = (tempo_fim_total - tempo_inicio_total).total_seconds()

            self.logger.error(f"❌ Erro no ExecutorUnificadoPL: {e}")

            return {
                "status": "ERRO",
                "erro": str(e),
                "tipo_erro": type(e).__name__,
                "tempo_total": tempo_total,
                "modo": self.modo_detectado.value if self.modo_detectado else "NAO_DETECTADO",
                "estatisticas_modo": self.estatisticas_modo
            }

    def _serializar_horarios(self, horarios: Dict) -> Dict:
        """
        Serializa horários (datetime) para strings para facilitar logs/JSON.

        Args:
            horarios: Dict {id_pedido: {id_atividade: (inicio, fim)}}

        Returns:
            Dict com datetimes convertidos para strings
        """
        if not horarios:
            return {}

        horarios_serializados = {}

        for id_pedido, horarios_atividades in horarios.items():
            horarios_serializados[id_pedido] = {}

            for id_atividade, (inicio, fim) in horarios_atividades.items():
                horarios_serializados[id_pedido][id_atividade] = {
                    "inicio": inicio.strftime("%d/%m/%Y %H:%M:%S"),
                    "fim": fim.strftime("%d/%m/%Y %H:%M:%S"),
                    "duracao_min": int((fim - inicio).total_seconds() / 60)
                }

        return horarios_serializados

    def gerar_relatorio_completo(self, resultado: Dict) -> str:
        """
        Gera relatório textual completo do processo.

        Args:
            resultado: Dict retornado por otimizar_e_executar

        Returns:
            String com relatório completo formatado
        """
        relatorio = []
        relatorio.append("=" * 70)
        relatorio.append("📋 RELATÓRIO COMPLETO - PL v2.0")
        relatorio.append("=" * 70)
        relatorio.append("")

        # Status geral
        relatorio.append(f"✅ Status: {resultado.get('status', 'N/A')}")
        relatorio.append(f"🔍 Modo: {resultado.get('modo', 'N/A')}")
        relatorio.append("")

        # Estatísticas gerais
        if 'estatisticas_gerais' in resultado:
            stats = resultado['estatisticas_gerais']
            relatorio.append("📊 ESTATÍSTICAS GERAIS:")
            relatorio.append(f"   Total de pedidos: {stats.get('total_pedidos', 0)}")
            relatorio.append(f"   ✅ Sucesso: {stats.get('pedidos_sucesso', 0)}")
            relatorio.append(f"   ❌ Erro: {stats.get('pedidos_erro', 0)}")
            relatorio.append(f"   📈 Taxa de sucesso: {stats.get('taxa_sucesso', 0):.1f}%")
            relatorio.append(f"   ⏱️ Tempo total: {stats.get('tempo_total', 0):.2f}s")
            relatorio.append(f"      • Otimização: {stats.get('tempo_otimizacao', 0):.3f}s")
            relatorio.append(f"      • Execução: {stats.get('tempo_execucao', 0):.2f}s")
            relatorio.append("")

        # Informações sobre otimização
        if 'otimizacao' in resultado:
            otim = resultado['otimizacao']
            relatorio.append("🎯 OTIMIZAÇÃO:")
            relatorio.append(f"   Método: {otim.get('metodo', 'N/A')}")
            relatorio.append(f"   Status: {otim.get('status', 'N/A')}")
            relatorio.append(
                f"   Ordem: {', '.join(map(str, otim.get('ordem_execucao', [])))}"
            )
            relatorio.append("")

        # Resultados de execução
        if 'execucao' in resultado:
            exec_result = resultado['execucao']
            relatorio.append("⚙️ EXECUÇÃO:")
            relatorio.append(
                f"   Executados: {', '.join(map(str, exec_result.get('pedidos_executados', [])))}"
            )
            if exec_result.get('pedidos_com_erro'):
                relatorio.append(
                    f"   Com erro: {', '.join(map(str, exec_result.get('pedidos_com_erro', [])))}"
                )
            relatorio.append("")

        # Erro (se houver)
        if resultado.get('status') == 'ERRO' and 'erro' in resultado:
            relatorio.append("❌ ERRO:")
            relatorio.append(f"   {resultado['erro']}")
            relatorio.append("")

        relatorio.append("=" * 70)

        return "\n".join(relatorio)


# Função de conveniência para uso direto
def executar_pl_v2(
    pedidos: List,
    inicio_jornada: Optional[datetime] = None
) -> Dict:
    """
    Função de conveniência para executar PL v2.0.

    Args:
        pedidos: Lista de objetos PedidoDeProducao
        inicio_jornada: Datetime do início da jornada

    Returns:
        Dict com resultados completos
    """
    executor = ExecutorUnificadoPL()
    return executor.otimizar_e_executar(pedidos, inicio_jornada)
