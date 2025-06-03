# fabrica_atividades_coccao_de_massas_para_brownie.py

import sys
from datetime import datetime

# 🔧 Ajuste do path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

# ============================================
# 📦 Imports
# ============================================
from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import forno_3, forno_4
from models.atividades.subproduto.massa_pra_brownie.coccao_de_massas_para_brownie import (
    CoccaoDeMassasParaBrownie,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_fornos import GestorFornos

# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoCoccaoMassasBrownie",
    arquivo="logs/simulacao_coccao_massas_brownie.log"
)

# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 21, 8, 0)
fim_entrega = datetime(2025, 5, 21, 17, 0)

# ============================================
# 🚀 Instanciar Gestor de Fornos
# ============================================
gestor_fornos = GestorFornos([forno_3, forno_4])

# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [1500, 1500, 4000, 1500]

# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = CoccaoDeMassasParaBrownie(
        id=i + 1,
        tipo_atividade=TipoAtividade.COCCAO_DE_MASSAS_PARA_BROWNIE,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[forno_4, forno_3],
        quantidade_produto=quantidade,
        fips_equipamentos={
            forno_4: 1,  # 🔥 Maior prioridade
            forno_3: 2,  # 🔥 Segunda prioridade
        },
    )
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de cocção de massas para brownie criadas.")

# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_fornos=gestor_fornos,
        inicio_janela=inicio_jornada,
        horario_limite=fim_entrega,
        temperatura_desejada=180,   # ✅ Brownie a 180°C
        vaporizacao_desejada=None,  # ✅ Não usa vaporização
        velocidade_desejada=None    # ✅ Sem controle de velocidade
    )

    if sucesso:
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"dentro da janela até {fim_entrega.strftime('%H:%M')}."
        )

# ============================================
# 📅 Mostrar Agendas Finais dos Fornos
# ============================================
gestor_fornos.mostrar_agenda()
