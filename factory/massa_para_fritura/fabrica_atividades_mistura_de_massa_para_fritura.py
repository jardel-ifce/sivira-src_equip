# fabrica_atividades_mistura_massas_para_frituras.py

import sys
from datetime import datetime

# 🔧 Ajuste do path
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

# ============================================
# 📦 Imports
# ============================================
from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import hotmix_1, hotmix_2
from models.atividades.subproduto.massa_para_frituras.mistura_de_massas_para_frituras import (
    MisturaDeMassasParaFrituras,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_misturadoras_com_coccao import GestorMisturadorasComCoccao

# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoMisturaMassasParaFrituras",
    arquivo="logs/simulacao_mistura_massas_para_frituras.log"
)

# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 6, 1, 8, 0)
fim_entrega = datetime(2025, 6, 1, 17, 0)

# ============================================
# 🛠️ Gestor das HotMix
# ============================================
gestor_hotmix = GestorMisturadorasComCoccao([hotmix_1, hotmix_2])

# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 15000, 25000, 30000, 5000, 15000, 25000, 30000, ]

# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = MisturaDeMassasParaFrituras(
        id=i + 1,
        tipo_atividade=TipoAtividade.MISTURA_DE_MASSAS_PARA_FRITURAS,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[hotmix_1, hotmix_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            hotmix_1: 1,
            hotmix_2: 2
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de mistura de massas para frituras criadas.")

# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_misturadoras=gestor_hotmix,
        inicio_janela=inicio_jornada,
        horario_limite=fim_entrega
    )

    if sucesso:
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada entre "
            f"{inicio_jornada.strftime('%H:%M')} e {fim_entrega.strftime('%H:%M')}."
        )

# ============================================
# 📅 Mostrar Agenda Final
# ============================================
gestor_hotmix.mostrar_agenda()
