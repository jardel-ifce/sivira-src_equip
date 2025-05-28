import sys
from datetime import datetime
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

# ============================================
# 📦 Imports
# ============================================
from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import bancada_4, bancada_5, bancada_6
from models.atividades.subproduto.massa_para_folhados.laminacao_1_de_massas_para_folhados import (
    Laminacao1DeMassasParaFolhados,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_bancadas import GestorBancadas


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoDebugLaminacao",
    arquivo="logs/simulacao_debug_laminacao.log"
)


# ============================================
# ⏰ Jornada de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 25, 8, 0)
fim_jornada = datetime(2025, 5, 25, 17, 0)


# ============================================
# 🛠️ Instanciar Gestor de Bancadas
# ============================================
gestor_bancadas = GestorBancadas([bancada_4, bancada_5, bancada_6])

# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 15000, 25000, 30000]  # 🔥 Aqui você adiciona as quantidades que quiser


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = Laminacao1DeMassasParaFolhados(
        id=i + 1,
        tipo_atividade=TipoAtividade.LAMINACAO_1_DE_MASSAS_PARA_FOLHADOS,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[bancada_4, bancada_5, bancada_6],
        quantidade_produto=quantidade,
        fips_equipamentos={
            bancada_4: 1,
            bancada_5: 2,
            bancada_6: 3
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de laminação 1 de massas para folhados criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_bancadas=gestor_bancadas,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada,
        porcoes=4  # 🔥 Sempre ocupa 4 porções da bancada
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada na Bancada {atividade.bancada_alocada.nome} "
            f"de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')}."
        )
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada na jornada "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agenda Final
# ============================================
gestor_bancadas.mostrar_agenda()
