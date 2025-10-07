"""
Enumeração de status de ordens de produção.

Define os estados possíveis de uma ordem de produção no sistema.
"""

from enum import Enum


class StatusOrdem(Enum):
    """
    Estados possíveis de uma ordem de produção.

    Attributes:
        PENDENTE: Ordem aguardando início da produção
        EM_PRODUCAO: Ordem sendo executada
        FINALIZADO: Ordem concluída com sucesso
        CANCELADO: Ordem cancelada
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