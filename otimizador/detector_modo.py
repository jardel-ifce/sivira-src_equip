"""
Detector de Modo de Otimização
===============================

Detecta se os pedidos estão em modo:
- DETERMINISTICO: Todos tempo_maximo_espera = 0 (configuração única de horários)
- FLEXIVEL: Pelo menos um tempo_maximo_espera > 0 (múltiplas configurações possíveis)

Criado em: 18/11/2025
"""

from datetime import timedelta
from typing import List, Tuple
from enum import Enum
from utils.logs.logger_factory import setup_logger

logger = setup_logger('DetectorModo')


class ModoOtimizacao(Enum):
    """Tipos de modo de otimização."""
    DETERMINISTICO = "DETERMINISTICO"  # Todos gaps = 0, horários fixos
    FLEXIVEL = "FLEXIVEL"  # Algum gap > 0, horários flexíveis


class DetectorModo:
    """
    Detecta o modo de otimização baseado nos tempos máximos de espera dos pedidos.
    """

    def __init__(self):
        self.logger = setup_logger('DetectorModo')

    def detectar_modo(self, pedidos: List) -> Tuple[ModoOtimizacao, dict]:
        """
        Detecta se os pedidos estão em modo DETERMINISTICO ou FLEXIVEL.

        Args:
            pedidos: Lista de objetos PedidoDeProducao

        Returns:
            Tupla (modo, estatisticas) onde:
            - modo: ModoOtimizacao.DETERMINISTICO ou ModoOtimizacao.FLEXIVEL
            - estatisticas: Dict com informações sobre a análise
        """
        if not pedidos:
            self.logger.warning("⚠️ Lista de pedidos vazia")
            return ModoOtimizacao.DETERMINISTICO, {
                "total_pedidos": 0,
                "pedidos_deterministicos": 0,
                "pedidos_flexiveis": 0,
                "total_atividades_analisadas": 0
            }

        # Estatísticas de análise
        total_pedidos = len(pedidos)
        pedidos_deterministicos = 0
        pedidos_flexiveis = 0
        total_atividades_analisadas = 0
        detalhes_pedidos = []

        # Analisar cada pedido
        for pedido in pedidos:
            resultado_pedido = self._analisar_pedido(pedido)
            total_atividades_analisadas += resultado_pedido["total_atividades"]

            if resultado_pedido["modo"] == "DETERMINISTICO":
                pedidos_deterministicos += 1
            else:
                pedidos_flexiveis += 1

            detalhes_pedidos.append({
                "id_pedido": pedido.id_pedido,
                "modo": resultado_pedido["modo"],
                "total_atividades": resultado_pedido["total_atividades"],
                "atividades_com_gap": resultado_pedido["atividades_com_gap"]
            })

        # Determinar modo global
        modo_global = (
            ModoOtimizacao.DETERMINISTICO
            if pedidos_flexiveis == 0
            else ModoOtimizacao.FLEXIVEL
        )

        # Montar estatísticas
        estatisticas = {
            "modo_detectado": modo_global.value,
            "total_pedidos": total_pedidos,
            "pedidos_deterministicos": pedidos_deterministicos,
            "pedidos_flexiveis": pedidos_flexiveis,
            "total_atividades_analisadas": total_atividades_analisadas,
            "detalhes_por_pedido": detalhes_pedidos
        }

        # Log do resultado
        self.logger.info(f"🔍 Modo detectado: {modo_global.value}")
        self.logger.info(
            f"📊 Pedidos: {pedidos_deterministicos} determinísticos, "
            f"{pedidos_flexiveis} flexíveis (total: {total_pedidos})"
        )

        return modo_global, estatisticas

    def _analisar_pedido(self, pedido) -> dict:
        """
        Analisa um pedido individual para verificar seu modo.

        Args:
            pedido: Objeto PedidoDeProducao

        Returns:
            Dict com informações sobre o pedido:
            - modo: "DETERMINISTICO" ou "FLEXIVEL"
            - total_atividades: Número de atividades analisadas
            - atividades_com_gap: Número de atividades com gap > 0
        """
        total_atividades = 0
        atividades_com_gap = 0

        # Analisar atividades modulares
        if hasattr(pedido, 'atividades_modulares'):
            for atividade in pedido.atividades_modulares:
                total_atividades += 1

                # Verificar tempo_maximo_de_espera
                if hasattr(atividade, 'tempo_maximo_de_espera'):
                    tempo_max = atividade.tempo_maximo_de_espera

                    # Converter para timedelta se necessário
                    if not isinstance(tempo_max, timedelta):
                        try:
                            tempo_max = timedelta(seconds=float(tempo_max))
                        except (ValueError, TypeError):
                            tempo_max = timedelta(0)

                    # Verificar se há flexibilidade (gap > 0)
                    if tempo_max > timedelta(0):
                        atividades_com_gap += 1

        # Determinar modo do pedido
        modo_pedido = (
            "DETERMINISTICO"
            if atividades_com_gap == 0
            else "FLEXIVEL"
        )

        return {
            "modo": modo_pedido,
            "total_atividades": total_atividades,
            "atividades_com_gap": atividades_com_gap
        }


# Função de conveniência para uso direto
def detectar_modo_otimizacao(pedidos: List) -> Tuple[ModoOtimizacao, dict]:
    """
    Função de conveniência para detectar modo de otimização.

    Args:
        pedidos: Lista de objetos PedidoDeProducao

    Returns:
        Tupla (modo, estatisticas)
    """
    detector = DetectorModo()
    return detector.detectar_modo(pedidos)
