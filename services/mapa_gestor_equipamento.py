
from enums.tipo_equipamento import TipoEquipamento
from services.gestor_armarios_para_fermentacao import GestorArmariosParaFermentacao
from services.gestor_balancas import GestorBalancas
from services.gestor_bancadas import GestorBancadas
from services.gestor_batedeiras import GestorBatedeiras
from services.gestor_fogoes import GestorFogoes
from services.gestor_fornos import GestorFornos
from services.gestor_misturadoras_com_coccao import GestorMisturadorasComCoccao
from services.gestor_misturadoras import GestorMisturadoras
from services.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento


# Adicione mais gestores conforme necessário

MAPA_GESTOR = {
    TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: GestorArmariosParaFermentacao,
    TipoEquipamento.BALANCAS: GestorBalancas,
    TipoEquipamento.BANCADAS: GestorBancadas,
    TipoEquipamento.BATEDEIRAS: GestorBatedeiras,
    TipoEquipamento.FOGOES: GestorFogoes,
    TipoEquipamento.FORNOS: GestorFornos,
    TipoEquipamento.MISTURADORAS_COM_COCCAO: GestorMisturadorasComCoccao,
    TipoEquipamento.MISTURADORAS: GestorMisturadoras,
    TipoEquipamento.REFRIGERACAO_CONGELAMENTO: GestorRefrigeracaoCongelamento
}