# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

# 🔧 Ajuste de path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import bancada_7
from models.atividades.subproduto.creme_de_frango.preparo_para_coccao_de_creme_de_frango import (
    PreparoParaCoccaoDeCremeDeFrango,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_bancadas import GestorBancadas


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoPreparoCoccaoCremeDeFrango",
    arquivo="logs/simulacao_preparo_coccao_creme_de_frango.log"
)


# ============================================
# ⏰ Janela de producao
# ============================================
inicio_jornada = datetime(2025, 5, 23, 8, 0)
fim_jornada = datetime(2025, 5, 23, 17, 0)


# ============================================
# 🛠️ Instanciar Gestor de Bancadas
# ============================================
gestor_bancadas = GestorBancadas([bancada_7])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 15000, 25000, 50000, 60000, 5000, 15000, 25000, 50000, 60000]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = PreparoParaCoccaoDeCremeDeFrango(
        id=i + 1,
        tipo_atividade=TipoAtividade.PREPARO_PARA_COCCAO_DE_CREME_DE_FRANGO,
        tipos_profissionais_permitidos=[TipoProfissional.COZINHEIRO],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[bancada_7],
        quantidade_produto=quantidade,
        fips_equipamentos={bancada_7: 1},  # fator de importância padrão
    )
    atividades.append(atividade)

logger.info(
    f"🛠️ {len(atividades)} atividades de preparo para cocção de creme de frango criadas."
)


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
        fracoes_necessarias=1  # 🪵 Ocupação padrão de uma fração
    )

    if sucesso:
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada entre "
            f"{inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
logger.info("📅 Agenda final das bancadas:")
gestor_bancadas.mostrar_agenda()
