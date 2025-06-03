# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

# 🔧 Ajuste de path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import bancada_4, bancada_5, bancada_6, fogao_2
from models.atividades.subproduto.ganache_de_chocolate.preparo_para_coccao_de_ganache_de_chocolate import (
    PreparoParaCoccaoDeGanacheDeChocolate,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_bancadas import GestorBancadas
from services.gestor_fogoes import GestorFogoes


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoPreparoCoccaoGanache",
    arquivo="logs/simulacao_preparo_coccao_ganache_de_chocolate.log"
)


# ============================================
# ⏰ Janela de producao
# ============================================
inicio_jornada = datetime(2025, 6, 1, 8, 0)
fim_jornada = datetime(2025, 6, 1, 17, 0)


# ============================================
# 🛠️ Instanciar Gestores
# ============================================
gestor_bancadas = GestorBancadas([bancada_5, bancada_6, bancada_4])  # FIPs: 1, 2, 3
gestor_fogoes = GestorFogoes([fogao_2])  # FIP: 1


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 15000, 25000, 30000, 25000]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = PreparoParaCoccaoDeGanacheDeChocolate(
        id=i + 1,
        tipo_atividade=TipoAtividade.PREPARO_PARA_COCCAO_DE_GANACHE_DE_CHOCOLATE,
        tipos_profissionais_permitidos=[TipoProfissional.CONFEITEIRO],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[bancada_5, bancada_6, bancada_4, fogao_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            bancada_5: 1,
            bancada_6: 2,
            bancada_4: 3,
            fogao_2: 1
        },
    )
    atividades.append(atividade)

logger.info(
    f"🛠️ {len(atividades)} atividades de preparo para cocção de ganache criadas."
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
        gestor_fogoes=gestor_fogoes,
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

logger.info("📅 Agenda final dos fogões:")
gestor_fogoes.mostrar_agenda()
