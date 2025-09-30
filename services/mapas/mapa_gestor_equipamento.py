from enums.equipamentos.tipo_equipamento import TipoEquipamento
from services.gestores.equipamentos.gestor_armarios_para_fermentacao import GestorArmariosParaFermentacao
from services.gestores.equipamentos.gestor_balancas import GestorBalancas
from services.gestores.equipamentos.gestor_bancadas import GestorBancadas
from services.gestores.equipamentos.gestor_batedeiras import GestorBatedeiras
from services.gestores.equipamentos.gestor_fogoes import GestorFogoes
from services.gestores.equipamentos.gestor_fornos import GestorFornos
from services.gestores.equipamentos.gestor_misturadoras_com_coccao import GestorMisturadorasComCoccao
from services.gestores.equipamentos.gestor_misturadoras import GestorMisturadoras
from services.gestores.equipamentos.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento
from services.gestores.equipamentos.gestor_modeladoras import GestorModeladoras
from services.gestores.equipamentos.gestor_divisoras_boleadoras import GestorDivisorasBoleadoras
from services.gestores.equipamentos.gestor_embaladoras import GestorEmbaladoras
from services.gestores.equipamentos.gestor_fritadeiras import GestorFritadeiras


# Adicione mais gestores conforme necessário

MAPA_GESTOR = {
    TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: GestorArmariosParaFermentacao,
    TipoEquipamento.BALANCAS: GestorBalancas,
    TipoEquipamento.BANCADAS: GestorBancadas,
    TipoEquipamento.BATEDEIRAS: GestorBatedeiras,
    TipoEquipamento.FOGOES: GestorFogoes,
    TipoEquipamento.FORNOS: GestorFornos,
    TipoEquipamento.FRITADEIRAS: GestorFritadeiras,
    TipoEquipamento.MISTURADORAS_COM_COCCAO: GestorMisturadorasComCoccao,
    TipoEquipamento.MISTURADORAS: GestorMisturadoras,
    TipoEquipamento.REFRIGERACAO_CONGELAMENTO: GestorRefrigeracaoCongelamento,
    TipoEquipamento.MODELADORAS: GestorModeladoras,
    TipoEquipamento.DIVISORAS_BOLEADORAS: GestorDivisorasBoleadoras,
    TipoEquipamento.EMBALADORAS: GestorEmbaladoras
}