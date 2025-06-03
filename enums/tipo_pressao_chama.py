from enum import Enum

class TipoPressaoChama(Enum): 
    """
    Enumeração que representa os tipos de pressão de chama.
    """
    BAIXA_PRESSAO = "Baixa Pressão"
    ALTA_PRESSAO = "Alta Pressão"
    CHAMA_UNICA = "Chama Única"
    CHAMA_DUPLA = "Chama Dupla"

    def __str__(self) -> str:
        """
        Retorna uma representação em string do tipo de pressão de chama.
        """
        return self.value