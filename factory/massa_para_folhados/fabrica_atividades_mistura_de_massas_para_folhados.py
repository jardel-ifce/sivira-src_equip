import sys
from datetime import datetime
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

# ============================================
# 📦 Imports
# ============================================
from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import masseira_3
from models.atividades.subproduto.massa_para_folhados.mistura_de_massas_para_folhados import (
    MisturaDeMassasParaFolhados,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_misturadoras import GestorMisturadoras


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoMisturaMassasParaFolhados",
    arquivo="logs/simulacao_mistura_massas_para_folhados.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 25, 8, 0)
fim_entrega = datetime(2025, 5, 25, 17, 0)


# ============================================
# 🛠️ Instanciar Gestor de Misturadoras
# ============================================
gestor_misturadoras = GestorMisturadoras([masseira_3])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 15000, 18000, 20000]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = MisturaDeMassasParaFolhados(
        id=i + 1,
        tipo_atividade=TipoAtividade.MISTURA_DE_MASSAS_PARA_FOLHADOS,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[masseira_3],
        quantidade_produto=quantidade,
        fips_equipamentos={masseira_3: 1},
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de mistura de massas para folhados criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )
    sucesso, masseira, inicio_real, fim_real = gestor_misturadoras.alocar(
        inicio=inicio_jornada,
        fim=fim_entrega,
        atividade=atividade,
        quantidade=atividade.quantidade_produto
    )

    if sucesso:
        atividade.inicio_real = inicio_real
        atividade.fim_real = fim_real
        atividade.masseira_alocada = masseira
        atividade.alocada = True

        logger.info(
            f"✅ Atividade {atividade.id} alocada com sucesso na Masseira {masseira.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}."
        )
        atividade.iniciar()

    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada na janela "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
gestor_misturadoras.mostrar_agenda()
