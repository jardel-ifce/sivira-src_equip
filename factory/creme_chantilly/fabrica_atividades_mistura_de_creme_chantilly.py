import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from datetime import datetime
from utils.logger_factory import setup_logger

from factory.fabrica_equipamentos import batedeira_planetaria_1, batedeira_planetaria_2
from models.atividades.subproduto.creme_chantilly.mistura_de_creme_chantilly import (
    MisturaDeCremeChantilly,)

from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_batedeiras import GestorBatedeiras


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoMisturaCremeChantilly",
    arquivo="logs/simulacao_mistura_creme_chantilly.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 23, 8, 0)
fim_entrega = datetime(2025, 5, 23, 17, 0)


# ============================================
# 🛠️ Instanciar Gestor de Batedeiras
# ============================================
gestor_batedeiras = GestorBatedeiras([batedeira_planetaria_1, batedeira_planetaria_2])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [4000, 4000, 3000, 500, 2500, 2100, 500, 5000]  # 🏗️ Ajuste aqui os lotes de produção


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = MisturaDeCremeChantilly(
        id=i + 1,
        tipo_atividade=TipoAtividade.MISTURA_DE_CREME_CHANTILLY,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[batedeira_planetaria_1, batedeira_planetaria_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            batedeira_planetaria_1: 1,
            batedeira_planetaria_2: 2,
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de mistura de creme chantilly criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    sucesso, equipamento, inicio_real, fim_real = gestor_batedeiras.alocar(
        inicio=inicio_jornada,
        fim=fim_entrega,
        atividade=atividade,
        quantidade=atividade.quantidade_produto
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada na {equipamento.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}."
        )
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada até {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
gestor_batedeiras.mostrar_agenda()
