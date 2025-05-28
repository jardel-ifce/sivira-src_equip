from enums.tipo_equipamento import TipoEquipamento
from services.gestor_fogoes import GestorFogoes
from services.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento


class GestorEquipamento:
    """
    Orquestrador que delega operações de alocação e verificação
    para gestores especializados de cada tipo de equipamento.
    """

    def __init__(self):
        pass

    def obter_gestor(self, equipamento):
        """
        Retorna o gestor específico para o tipo de equipamento.
        """
        if equipamento.tipo_equipamento == TipoEquipamento.FOGOES:
            return GestorFogoes(equipamento)

        elif equipamento.tipo_equipamento in (
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO
        ):
            return GestorRefrigeracaoCongelamento(equipamento)

        else:
            raise NotImplementedError(
                f"❌ Gestor não implementado para {equipamento.tipo_equipamento.name}"
            )
