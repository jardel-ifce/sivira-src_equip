import sys
from datetime import datetime

# 🔧 Ajuste do path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import fogao_1, fogao_2
from models.atividades.subproduto.carne_de_sol_refogada.coccao_de_carne_de_sol_cozida_pronta import (
    CoccaoDeCarneDeSolCozidaPronta,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_fogoes import GestorFogoes


# ================================================
# 🔥 Logger
# ================================================
logger = setup_logger(
    "SimulacaoCoccaoCarneDeSol",
    arquivo="logs/simulacao_coccao_carne_de_sol.log"
)


# ================================================
# ⏰ Janela de Produção
# ================================================
inicio_jornada = datetime(2025, 5, 21, 8, 0)
fim_entrega = datetime(2025, 5, 21, 17, 0)


# ================================================
# 🚀 Instanciar Gestor de Fogões
# ================================================
gestor_fogoes = GestorFogoes([fogao_1, fogao_2])


# ================================================
# 📦 Quantidades simuladas
# ================================================
quantidades = [30000, 45000, 34000, 60000, 20000, 10000, 40000, 45000, 25000, 35000]


# ================================================
# 🏗️ Criar Atividades
# ================================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = CoccaoDeCarneDeSolCozidaPronta(
        id=i + 1,
        tipo_atividade=TipoAtividade.COCCAO_DE_CARNE_DE_SOL_COZIDA_PRONTA,
        tipos_profissionais_permitidos=[TipoProfissional.COZINHEIRO, TipoProfissional.ALMOXARIFE],
        quantidade_funcionarios=2,
        equipamentos_elegiveis=[fogao_1, fogao_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            fogao_1: 1,
            fogao_2: 2,
        },
    )
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de cocção criadas.")


# ================================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ================================================
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
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"até {fim_entrega.strftime('%H:%M')}."
        )


# ================================================
# 📅 Mostrar Agendas Finais dos Fogões
# ================================================
gestor_fogoes.mostrar_agenda()
