# fabrica_atividades_preparo_para_coccao_de_frango_cozido_pronto.py

# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from factory.fabrica_equipamentos import bancada_7
from models.atividades.subproduto.frango_refogado.preparo_para_coccao_de_frango_cozido_pronto import (
    PreparoParaCoccaoDeFrangoCozidoPronto,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_bancadas import GestorBancadas
from utils.logger_factory import setup_logger


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoPreparoCoccaoFrangoCozido",
    arquivo="logs/simulacao_preparo_coccao_frango_cozido.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 24, 8, 0)
fim_jornada = datetime(2025, 5, 24, 17, 0)


# ============================================
# 🏗️ Instanciar Gestor de Bancadas
# ============================================
gestor_bancadas = GestorBancadas([bancada_7])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 12000, 25000, 50000]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = PreparoParaCoccaoDeFrangoCozidoPronto(
        id=i + 1,
        tipo_atividade=TipoAtividade.PREPARO_PARA_COCCAO_DE_FRANGO_COZIDO_PRONTO,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
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
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_bancadas=gestor_bancadas,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada,
        porcoes_bancada=1
    )

    if sucesso:
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"dentro da janela {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
gestor_bancadas.mostrar_agenda()
