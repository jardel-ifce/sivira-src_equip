from enum import Enum

class TipoChama(Enum):
   """"
    Enumeração para os tipos de chama de um equipamento.
   """
   BAIXA = "Baixa"
   MEDIA = "Média"
   ALTA = "Alta"    

   def __str__(self):
        return self.value