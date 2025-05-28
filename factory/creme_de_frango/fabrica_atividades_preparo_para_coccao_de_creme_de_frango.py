import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from datetime import datetime
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
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 23, 8, 0)
fim_entrega = datetime(2025, 5, 23, 17, 0)


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
        fips_equipamentos={bancada_7: 1},
    )
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de preparo para cocção criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_bancadas=gestor_bancadas,
        inicio_janela=inicio_jornada,
        horario_limite=fim_entrega,
        fracao_bancada=(1, 6)
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada com sucesso na Bancada {atividade.bancada_alocada.nome} "
            f"de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')}."
        )
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada na janela "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
gestor_bancadas.mostrar_agenda()
