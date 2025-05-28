# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

# 🔧 Ajuste de path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import (
    bancada_4,
    bancada_5,
    bancada_6,
    balanca_digital_2
)
from models.atividades.subproduto.creme_de_limao.preparo_para_armazenamento_de_creme_de_limao import (
    PreparoParaArmazenamentoDeCremeDeLimao,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_bancadas import GestorBancadas
from services.gestor_balancas import GestorBalancas


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoPreparoArmazenamentoCremeDeLimao",
    arquivo="logs/simulacao_preparo_armazenamento_creme_de_limao.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 24, 8, 0)
fim_entrega = datetime(2025, 5, 24, 17, 0)


# ============================================
# 🛠️ Instanciar Gestores
# ============================================
gestor_bancadas = GestorBancadas([bancada_4, bancada_5, bancada_6])
gestor_balancas = GestorBalancas([balanca_digital_2])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 12000, 18000, 25000]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = PreparoParaArmazenamentoDeCremeDeLimao(
        id=i + 1,
        tipo_atividade=TipoAtividade.PREPARO_PARA_ARMAZENAMENTO_DE_CREME_DE_LIMAO,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[bancada_4, bancada_5, bancada_6, balanca_digital_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            bancada_4: 3,
            bancada_5: 1,
            bancada_6: 2,
            balanca_digital_2: 1
        },
    )
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de preparo para armazenamento de creme de limão criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_bancadas=gestor_bancadas,
        gestor_balancas=gestor_balancas,
        inicio_janela=inicio_jornada,
        horario_limite=fim_entrega,
        fracao_bancada=(1, 4)  # Pode ser ajustável conforme estratégia
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada com sucesso: "
            f"Bancada {atividade.bancada_alocada.nome} de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')} "
            f"e Balança {atividade.balanca_alocada.nome} de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')}."
        )
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada dentro da janela "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
logger.info("📅 Agenda final dos equipamentos:")

gestor_bancadas.mostrar_agenda()
gestor_balancas.mostrar_agenda()
