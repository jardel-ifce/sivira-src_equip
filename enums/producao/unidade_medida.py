from enum import Enum

class UnidadeMedida(Enum):
    GRAMAS = "GRAMAS"
    LITROS = "LITROS"
    METROS = "METROS"
    CENTIMETROS = "CENTIMETROS"
    MILILITROS = "MILILITROS"
    UNIDADE = "UNIDADE"
    PORCOES = "PORCOES"
    FUNCIONARIOS = "FUNCIONARIOS"
    UNIDADES_POR_HORA = "UNIDADES_POR_HORA"
    COLHERES = "COLHERES"
    XICARAS = "XICARAS"


    def __str__(self):
        """
        Retorna uma representação textual da unidade de medida.
        """
        return self.value