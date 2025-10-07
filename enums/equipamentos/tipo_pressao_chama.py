"""
Enumeração de tipos de pressão de chama.

Define as configurações de pressão e chama para equipamentos a gás.
"""

from enum import Enum


class TipoPressaoChama(Enum):
    """
    Tipos de pressão e configuração de chama.

    Attributes:
        BAIXA_PRESSAO: Operação com baixa pressão de gás
        ALTA_PRESSAO: Operação com alta pressão de gás
        CHAMA_UNICA: Sistema com queimador único
        CHAMA_DUPLA: Sistema com duplo queimador
    """
    BAIXA_PRESSAO = "Baixa Pressão"
    ALTA_PRESSAO = "Alta Pressão"
    CHAMA_UNICA = "Chama Única"
    CHAMA_DUPLA = "Chama Dupla"

    def __str__(self):
        """
        Retorna a representação textual do tipo de pressão de chama.

        Returns:
            str: Descrição do tipo de pressão de chama
        """
        return self.value
