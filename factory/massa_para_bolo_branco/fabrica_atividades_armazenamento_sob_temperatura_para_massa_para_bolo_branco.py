
# fabrica_atividades_armazenamento_sob_temperatura_para_massa_de_bolo_branco.py

# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import camara_refrigerada_1
from models.atividades.subproduto.massa_para_bolo_branco.armazenamento_sob_temperatura_para_massa_para_bolo_branco import (
    ArmazenamentoSobTemperaturaParaMassaDeBoloBranco,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoArmazenamentoMassaDeBoloBranco",
    arquivo="logs/simulacao_armazenamento_massa_de_bolo_branco.log"
)


# ============================================
# ⏰ Jornada de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 25, 8, 0)
fim_jornada = datetime(2025, 5, 25, 17, 0)


# ============================================
# 🧊 Instanciar Gestor de Câmara
# ============================================
gestor_camaras = GestorRefrigeracaoCongelamento(camara_refrigerada_1)


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [
    5000, 6000, 8000, 12000, 15000, 18000, 20000,
    3000, 4000, 5000, 7000, 9000, 10000, 13000, 16000, 19000
]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = ArmazenamentoSobTemperaturaParaMassaDeBoloBranco(
        id=i + 1,
        tipo_atividade=TipoAtividade.ARMAZENAMENTO_SOB_TEMPERATURA_PARA_MASSA_PARA_BOLO_BRANCO,
        tipos_profissionais_permitidos=[
            TipoProfissional.ALMOXARIFE
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[camara_refrigerada_1],
        quantidade_produto=quantidade,
        fips_equipamentos={camara_refrigerada_1: 1},
    )
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de armazenamento de massa de bolo branco criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} | Quantidade: {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_refrigeracao=gestor_camaras,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada na {atividade.equipamento_alocado.nome} "
            f"de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')}."
        )
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"na janela de {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agenda Final
# ============================================
gestor_camaras.mostrar_agenda()
