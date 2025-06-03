# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

# 🔧 Ajuste do path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import forno_3, forno_4
from models.atividades.subproduto.massa_para_bolo_branco.coccao_de_massa_para_bolo_branco import (
    CoccaoDeMassaParaBoloBranco,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_fornos import GestorFornos


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoCoccaoMassasBoloBranco",
    arquivo="logs/simulacao_coccao_massas_bolo_branco.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 6, 1, 8, 0)
fim_entrega = datetime(2025, 6, 1, 17, 0)


# ============================================
# 🚀 Instanciar Gestor de Fornos
# ============================================
gestor_fornos = GestorFornos([forno_4, forno_3])  # 🔥 Prioriza forno_4


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [4000, 3500, 3800, 3000, 3700]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = CoccaoDeMassaParaBoloBranco(
        id=i + 1,
        tipo_atividade=TipoAtividade.COCCAO_DE_MASSAS_PARA_BOLO_BRANCO,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[forno_4, forno_3],
        quantidade_produto=quantidade,
        fips_equipamentos={
            forno_4: 1,
            forno_3: 2,
        },
    )
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de cocção de massa de bolo branco criadas.")


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
        temperatura_desejada=160,   # ✅ Temperatura padrão para bolo branco
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
