"""
Aplicador Flexivel
==================

Executa pedidos na ordem otimizada com suporte a janelas flexiveis.
Permite retry dentro das janelas temporais definidas por tau_max.

Criado em: 23/12/2025
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.logs.logger_factory import setup_logger

logger = setup_logger('AplicadorFlexivel')


class AplicadorFlexivel:
    """
    Executa pedidos usando janelas flexiveis.

    Diferenca do AplicadorOrdenacao (v2):
    - Suporta janelas temporais [inicio_min, inicio_max]
    - Permite retry dentro da janela se alocacao falhar
    - Respeita tau_max entre atividades
    """

    def __init__(self, janelas: Dict[int, Dict] = None):
        """
        Inicializa aplicador flexivel.

        Args:
            janelas: Dict {id_pedido: {id_atividade: JanelaFlexivel}}
        """
        self.janelas = janelas or {}
        self.pedidos_executados = []
        self.pedidos_com_erro = []
        self.logger = setup_logger('AplicadorFlexivel')
        self.estatisticas = {
            'tentativas_totais': 0,
            'alocacoes_com_retry': 0,
            'alocacoes_diretas': 0
        }

    def executar_pedidos(self, pedidos: List, ordem_execucao: List[int]) -> Dict:
        """
        Executa pedidos na ordem especificada com suporte a janelas.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            ordem_execucao: Lista de IDs na ordem de execucao

        Returns:
            Dict com resultado da execucao
        """
        self.logger.info(f"Executando {len(ordem_execucao)} pedidos com suporte a janelas flexiveis...")

        mapa_pedidos = {p.id_pedido: p for p in pedidos}
        tempo_inicio = datetime.now()

        for posicao, id_pedido in enumerate(ordem_execucao, 1):
            pedido = mapa_pedidos.get(id_pedido)

            if not pedido:
                self.logger.warning(f"   Pedido {id_pedido} nao encontrado!")
                self.pedidos_com_erro.append(id_pedido)
                continue

            self.logger.info(f"   [{posicao}/{len(ordem_execucao)}] Executando pedido {id_pedido}...")

            # Obter janelas deste pedido
            janelas_pedido = self.janelas.get(id_pedido, {})

            # Executar com janelas
            sucesso = self._executar_pedido_flexivel(pedido, janelas_pedido)

            if sucesso:
                self.pedidos_executados.append(id_pedido)
                self.logger.info(f"   Pedido {id_pedido}: SUCESSO")
            else:
                self.pedidos_com_erro.append(id_pedido)
                self.logger.warning(f"   Pedido {id_pedido}: FALHA")

        tempo_fim = datetime.now()
        tempo_total = (tempo_fim - tempo_inicio).total_seconds()

        taxa_sucesso = (
            len(self.pedidos_executados) / len(ordem_execucao) * 100
            if ordem_execucao else 0
        )

        self.logger.info(f"Execucao concluida: {len(self.pedidos_executados)}/{len(ordem_execucao)} pedidos")
        self.logger.info(f"Taxa de sucesso: {taxa_sucesso:.1f}%")
        self.logger.info(f"Tempo total: {tempo_total:.2f}s")

        return {
            "pedidos_executados": self.pedidos_executados,
            "pedidos_com_erro": self.pedidos_com_erro,
            "taxa_sucesso": taxa_sucesso,
            "tempo_total": tempo_total,
            "estatisticas": self.estatisticas
        }

    def _executar_pedido_flexivel(self, pedido, janelas: Dict) -> bool:
        """
        Executa um pedido individual usando janelas flexiveis.

        Args:
            pedido: Objeto PedidoDeProducao
            janelas: Dict {id_atividade: JanelaFlexivel}

        Returns:
            bool: True se sucesso
        """
        from otimizador.executor_pedido_flexivel import ExecutorPedidoFlexivel

        try:
            executor = ExecutorPedidoFlexivel(pedido, janelas)
            resultado = executor.executar()

            # Atualizar estatisticas
            self.estatisticas['tentativas_totais'] += resultado.get('tentativas', 0)
            if resultado.get('usou_retry', False):
                self.estatisticas['alocacoes_com_retry'] += 1
            else:
                self.estatisticas['alocacoes_diretas'] += 1

            return resultado.get('sucesso', False)

        except Exception as e:
            self.logger.error(f"Erro no pedido {pedido.id_pedido}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def imprimir_resumo(self):
        """Imprime resumo da execucao."""
        print("\n" + "=" * 60)
        print("RESUMO DA EXECUCAO FLEXIVEL")
        print("=" * 60)

        print(f"\nPedidos executados: {len(self.pedidos_executados)}")
        if self.pedidos_executados:
            print(f"   IDs: {', '.join(map(str, self.pedidos_executados))}")

        print(f"\nPedidos com erro: {len(self.pedidos_com_erro)}")
        if self.pedidos_com_erro:
            print(f"   IDs: {', '.join(map(str, self.pedidos_com_erro))}")

        print(f"\nEstatisticas:")
        print(f"   Tentativas totais: {self.estatisticas['tentativas_totais']}")
        print(f"   Alocacoes diretas: {self.estatisticas['alocacoes_diretas']}")
        print(f"   Alocacoes com retry: {self.estatisticas['alocacoes_com_retry']}")

        print("\n" + "=" * 60)
