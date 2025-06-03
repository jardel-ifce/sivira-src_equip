# fabrica_atividades_armazenamento_sob_temperatura_para_ganache_de_chocolate.py

import sys
from datetime import datetime

# 🔧 Ajuste de path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import camara_refrigerada_1
from models.atividades.subproduto.ganache_de_chocolate.armazenamento_sob_temperatura_para_ganache_de_chocolate import (
    ArmazenamentoSobTemperaturaParaGanacheDeChocolate,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoArmazenamentoGanacheChocolate",
    arquivo="logs/simulacao_armazenamento_ganache_chocolate.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 6, 1, 8, 0)
fim_entrega = datetime(2025, 6, 1, 17, 0)


# ============================================
# 🧊 Instanciar Gestor da Câmara
# ============================================
gestor_camaras = GestorRefrigeracaoCongelamento([camara_refrigerada_1])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [
    5000, 8000, 10000, 12000, 15000,
    18000, 20000, 22000, 25000, 28000,
    3000, 4000, 6000, 9000, 11000,
    13000, 16000, 19000, 21000, 23000
]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = ArmazenamentoSobTemperaturaParaGanacheDeChocolate(
        id=i + 1,
        tipo_atividade=TipoAtividade.ARMAZENAMENTO_SOB_TEMPERATURA_PARA_GANACHE_DE_CHOCOLATE,
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
        f"🚀 Tentando alocar atividade {atividade.id} | Quantidade: {atividade.quantidade_produto}g."
    )

    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_refrigeracao=gestor_camaras,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_entrega
    )

    if sucesso:
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada dentro da janela "
            f"{inicio_jornada.strftime('%H:%M')} até {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agenda Final
# ============================================
gestor_camaras.mostrar_agenda()
