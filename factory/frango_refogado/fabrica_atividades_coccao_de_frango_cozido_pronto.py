# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

# 🔧 Ajuste de path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import fogao_1, fogao_2
from models.atividades.subproduto.frango_refogado.coccao_de_frango_cozido_pronto import (
    CoccaoDeFrangoCozidoPronto,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_fogoes import GestorFogoes


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoCoccaoFrangoCozidoPronto",
    arquivo="logs/simulacao_coccao_frango_cozido_pronto.log"
)


# ============================================
# ⏰ Jornada de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 25, 8, 0)
fim_entrega = datetime(2025, 5, 25, 17, 0)


# ============================================
# 🔥 Instanciar Gestor de Fogões
# ============================================
gestor_fogoes = GestorFogoes([fogao_1, fogao_2])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 15000, 20000, 30000, 40000, 45000, 60000]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = CoccaoDeFrangoCozidoPronto(
        id=i + 1,
        tipo_atividade=TipoAtividade.COCCAO_DE_FRANGO_COZIDO_PRONTO,
        tipos_profissionais_permitidos=[TipoProfissional.COZINHEIRO],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[fogao_1, fogao_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            fogao_1: 1,
            fogao_2: 2,
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🔥 {len(atividades)} atividades de cocção de frango cozido pronto criadas.")


# ============================================
# 🚀 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_fogoes=gestor_fogoes,
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
logger.info("📅 Agenda final dos fogões:")
gestor_fogoes.mostrar_agenda()
