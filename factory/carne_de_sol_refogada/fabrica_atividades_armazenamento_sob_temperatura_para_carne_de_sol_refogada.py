import sys
# 🔧 Ajuste do path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from datetime import datetime
from utils.logger_factory import setup_logger


# =========================================
# 📦 Imports
# =========================================
from factory.fabrica_equipamentos import camara_refrigerada_2
from models.atividades.subproduto.carne_de_sol_refogada.armazenamento_sob_temperatura_para_carne_de_sol_refogada import (
    ArmazenamentoSobTemperaturaParaCarneDeSolRefogada,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento


# =========================================
# 🔥 Logger
# =========================================
logger = setup_logger(
    "SimulacaoArmazenamentoCarneDeSol",
    arquivo="logs/simulacao_armazenamento_carne_de_sol.log"
)


# =========================================
# ⏰ Janela de Produção
# =========================================
inicio_jornada = datetime(2025, 5, 21, 8, 0)
fim_entrega = datetime(2025, 5, 21, 17, 0)


# =========================================
# 🚀 Instanciar Gestor de Câmara Refrigerada
# =========================================
gestor_camaras = GestorRefrigeracaoCongelamento(camara_refrigerada_2)


# =========================================
# 📦 Quantidades simuladas
# =========================================
quantidades = [12000, 12000, 25000, 40000]


# =========================================
# 🏗️ Criar Atividades
# =========================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = ArmazenamentoSobTemperaturaParaCarneDeSolRefogada(
        id=i + 1,
        tipo_atividade=TipoAtividade.ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CARNE_DE_SOL_REFOGADA,
        tipos_profissionais_permitidos=[TipoProfissional.ALMOXARIFE],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[camara_refrigerada_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            camara_refrigerada_2: 1,
        },
    )
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de armazenamento criadas.")


# =========================================
# ❄️ Tentar Alocar e Iniciar Atividades
# =========================================
count = 0
temperatura_desejada = -18
for atividade in atividades:
 
    logger.info(
        f"🚀 Tentando alocar atividade {atividade.id} com {atividade.quantidade_produto}g."
    )
    
    if count == 1:
        temperatura_desejada = -7
    else:
        temperatura_desejada = -18
    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_refrigeracao=gestor_camaras,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_entrega,
        temperatura_desejada=temperatura_desejada,
    )
    count += 1
    if sucesso:
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada "
            f"até {fim_entrega.strftime('%H:%M')}."
        )


# =========================================
# 📅 Mostrar Agenda Final da Câmara
# =========================================
gestor_camaras.mostrar_agenda()
