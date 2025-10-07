"""
Enumeração de status de pedidos.

Define os estados possíveis de um pedido no sistema.
"""

from enum import Enum


class StatusPedido(Enum):
    """
    Estados possíveis de um pedido.

    Attributes:
        PENDENTE: Pedido aguardando início da produção
        EM_PRODUCAO: Pedido sendo executado
        FINALIZADO: Pedido concluído com sucesso
        CANCELADO: Pedido cancelado
    """
    PENDENTE = "Pendente"
    EM_PRODUCAO = "Em Produção"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"

    def __str__(self):
        """
        Retorna a representação textual do status.

        Returns:
            str: Descrição do status
        """
        return self.value