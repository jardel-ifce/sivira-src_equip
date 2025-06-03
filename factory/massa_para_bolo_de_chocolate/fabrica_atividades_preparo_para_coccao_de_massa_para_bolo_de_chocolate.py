# fabrica_atividades_preparo_para_coccao_de_massa_para_bolo_de_chocolate.py

import sys
from datetime import datetime

# 🔧 Ajuste de path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

# ============================================
# 📦 Imports
# ============================================
from utils.logger_factory import setup_logger

from factory.fabrica_equipamentos import (
    bancada_4,
    bancada_5,
    bancada_6,
    armario_esqueleto_1,
    armario_esqueleto_2
)
from models.atividades.subproduto.massa_para_bolo_de_chocolate.preparo_para_coccao_de_massa_para_bolo_de_chocolate import (
    PreparoParaCoccaoDeMassaParaBoloDeChocolate,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_bancadas import GestorBancadas
from services.gestor_armarios_para_fermentacao import GestorArmariosParaFermentacao


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoPreparoCoccaoMassaBoloDeChocolate",
    arquivo="logs/simulacao_preparo_coccao_massa_bolo_de_chocolate.log"
)


# ============================================
# ⏰ Jornada de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 25, 8, 0)
fim_entrega = datetime(2025, 5, 25, 17, 0)


# ============================================
# 🛠️ Instanciar Gestores
# ============================================
gestor_bancadas = GestorBancadas([bancada_4, bancada_5, bancada_6])
gestor_armarios = GestorArmariosParaFermentacao([armario_esqueleto_1, armario_esqueleto_2])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [3000, 10000, 15000, 24000]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = PreparoParaCoccaoDeMassaParaBoloDeChocolate(
        id=i + 1,
        tipo_atividade=TipoAtividade.PREPARO_PARA_COCCAO_DE_MASSA_PARA_BOLO_DE_CHOCOLATE,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[
            bancada_4, bancada_5, bancada_6,
            armario_esqueleto_1, armario_esqueleto_2
        ],
        quantidade_produto=quantidade,
        fips_equipamentos={
            bancada_4: 3,
            bancada_5: 2,
            bancada_6: 1,
            armario_esqueleto_1: 1,
            armario_esqueleto_2: 2
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de preparo para cocção da massa de bolo de chocolate criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_bancadas=gestor_bancadas,
        gestor_armarios=gestor_armarios,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_entrega,
        fracoes_necessarias=1  # Ocupa 1 fração da bancada
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada com sucesso: "
            f"Bancada {atividade.bancada_alocada.nome} de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')} "
            f"e Armário {atividade.armario_alocado.nome}."
        )
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada na janela entre "
            f"{inicio_jornada.strftime('%H:%M')} e {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
gestor_bancadas.mostrar_agenda()
gestor_armarios.mostrar_agenda()
