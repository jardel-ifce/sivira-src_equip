# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

# 🔧 Ajuste do path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from factory.fabrica_equipamentos import fogao_1, fogao_2
from models.atividades.subproduto.creme_de_queijo.coccao_de_creme_de_queijo import CoccaoDeCremeDeQueijo
from models.atividades.subproduto.carne_de_sol_refogada.coccao_de_carne_de_sol_cozida_pronta import CoccaoDeCarneDeSolCozidaPronta
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_fogoes import GestorFogoes
from utils.logger_factory import setup_logger


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoCoccaoMix",
    arquivo="logs/simulacao_coccao_mix.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 24, 8, 0)
fim_entrega = datetime(2025, 5, 24, 17, 0)


# ============================================
# 🛠️ Instanciar Gestor de Fogões
# ============================================
gestor_fogoes = GestorFogoes([fogao_1, fogao_2])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades_queijo = [30000]
quantidades_carne = [34000]


# ============================================
# 🏗️ Criar Atividades de Creme de Queijo
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades_queijo):
    atividade = CoccaoDeCremeDeQueijo(
        id=i + 1,
        tipo_atividade=TipoAtividade.COCCAO_DE_CREME_DE_QUEIJO,
        tipos_profissionais_permitidos=[TipoProfissional.COZINHEIRO],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[fogao_1, fogao_2],
        quantidade_produto=quantidade,
        fips_equipamentos={fogao_1: 1, fogao_2: 2},
    )
    atividades.append(atividade)


# ============================================
# 🏗️ Criar Atividades de Carne de Sol
# ============================================
for i, quantidade in enumerate(quantidades_carne):
    atividade = CoccaoDeCarneDeSolCozidaPronta(
        id=100 + i + 1,
        tipo_atividade=TipoAtividade.COCCAO_DE_CARNE_DE_SOL_COZIDA_PRONTA,
        tipos_profissionais_permitidos=[TipoProfissional.COZINHEIRO, TipoProfissional.ALMOXARIFE],
        quantidade_funcionarios=2,
        equipamentos_elegiveis=[fogao_1, fogao_2],
        quantidade_produto=quantidade,
        fips_equipamentos={fogao_1: 1, fogao_2: 2},
    )
    atividades.append(atividade)


logger.info(f"🛠️ {len(atividades)} atividades (mix de queijo + carne) criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} ({atividade.tipo_atividade.name}) "
        f"com {atividade.quantidade_produto}g."
    )
    sucesso, equipamento, inicio_real, fim_real = gestor_fogoes.alocar(
        inicio=inicio_jornada,
        fim=fim_entrega,
        atividade=atividade
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} ({atividade.tipo_atividade.name}) alocada no {equipamento.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}."
        )
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} ({atividade.tipo_atividade.name}) não pôde ser alocada "
            f"até {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais dos Fogões
# ============================================
gestor_fogoes.mostrar_agenda()
