import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from datetime import datetime
from utils.logger_factory import setup_logger

from factory.fabrica_equipamentos import camara_refrigerada_1
from models.atividades.subproduto.creme_chantilly.armazenamento_sob_temperatura_para_creme_chantilly import (
    ArmazenamentoSobTemperaturaParaCremeChantilly,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoArmazenamentoCremeChantilly",
    arquivo="logs/simulacao_armazenamento_creme_chantilly.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 23, 8, 0)
fim_entrega = datetime(2025, 5, 23, 17, 0)


# ============================================
# 🛠️ Instanciar Gestor de Câmara
# ============================================
gestor_camaras = GestorRefrigeracaoCongelamento([camara_refrigerada_1])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [
    5000, 12000, 18000, 25000,  # Atividade 4
    7000, 12000, 24000, 18000,  # Atividade 5 usa temperatura 7°C
    22000, 12000,              # Atividade 10 usa temperatura 1°C
    17000, 9000, 25000, 8000,  # Atividade 15 usa temperatura 5°C
    10000, 13000, 15000, 23000,  # Atividade 20 também a 1°C
    5000, 19000, 21000, 17000,
    11000, 9000, 13000, 15000,
    20000, 18000
]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = ArmazenamentoSobTemperaturaParaCremeChantilly(
        id=i + 1,
        tipo_atividade=TipoAtividade.ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CREME_CHANTILLY,
        tipos_profissionais_permitidos=[TipoProfissional.ALMOXARIFE],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[camara_refrigerada_1],
        quantidade_produto=quantidade,
        fips_equipamentos={camara_refrigerada_1: 1},
    )
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de armazenamento criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )

    # 🎯 Definir temperatura específica para atividades 5, 10, 15 e 20
    if atividade.id == 5:
        temperatura = 7
    elif atividade.id in [10, 20]:
        temperatura = 1
    elif atividade.id == 15:
        temperatura = 5
    else:
        temperatura = 4  # Temperatura padrão

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_refrigeracao=gestor_camaras,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_entrega,
        temperatura_desejada=temperatura
    )

    if sucesso:
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"até {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
gestor_camaras.mostrar_agenda()
