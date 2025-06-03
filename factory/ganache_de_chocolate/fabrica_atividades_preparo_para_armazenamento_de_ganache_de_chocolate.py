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
from models.atividades.subproduto.ganache_de_chocolate.preparo_para_armazenamento_de_ganache_de_chocolate import (
    PreparoParaArmazenamentoDeGanacheDeChocolate,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_bancadas import GestorBancadas
from services.gestor_balancas import GestorBalancas


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoPreparoArmazenamentoGanacheDeChocolate",
    arquivo="logs/simulacao_preparo_armazenamento_ganache_de_chocolate.log"
)


# ============================================
# ⏰ Jornada de Produção
# ============================================
inicio_jornada = datetime(2025, 6, 1, 8, 0)
fim_entrega = datetime(2025, 6, 1, 17, 0)


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
    atividade = PreparoParaArmazenamentoDeGanacheDeChocolate(
        id=i + 1,
        tipo_atividade=TipoAtividade.PREPARO_PARA_ARMAZENAMENTO_DE_GANACHE_DE_CHOCOLATE,
        tipos_profissionais_permitidos=[TipoProfissional.CONFEITEIRO],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[bancada_4, bancada_5, bancada_6, balanca_digital_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            bancada_4: 1,
            bancada_5: 1,
            bancada_6: 1,
            balanca_digital_2: 1,
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de preparo para armazenamento de ganache de chocolate criadas.")


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
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_entrega,
        fracoes_necessarias=1
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada com sucesso:\n"
            f"🚵 Bancada: {atividade.bancada_alocada.nome} de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')}\n"
            f"⚖️ Balança: {atividade.balanca_alocada.nome} registrada com {atividade.quantidade_produto}g"
        )
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada na janela entre "
            f"{inicio_jornada.strftime('%H:%M')} e {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 🗓️ Mostrar Agendas Finais
# ============================================
logger.info("🗓️ Agenda final dos equipamentos:")
gestor_bancadas.mostrar_agenda()
gestor_balancas.mostrar_agenda()
