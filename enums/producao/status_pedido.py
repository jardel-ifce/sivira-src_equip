from enum import Enum

class StatusPedido(Enum):
    PENDENTE = "Pendente"
    EM_PRODUCAO = "Em Produção"
    FINALIZADO = "Finalizado"
    CANCELADO = "Cancelado"
    
    def __str__(self):
        return self.value