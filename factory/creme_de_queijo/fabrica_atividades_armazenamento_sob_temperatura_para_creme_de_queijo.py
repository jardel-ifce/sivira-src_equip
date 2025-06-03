# fabrica_atividades_armazenamento_sob_temperatura_para_creme_de_queijo.py

# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import camara_refrigerada_2
from models.atividades.subproduto.creme_de_queijo.armazenamento_sob_temperatura_para_creme_de_queijo import (
    ArmazenamentoSobTemperaturaParaCremeDeQueijo,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoArmazenamentoCremeDeQueijo",
    arquivo="logs/simulacao_armazenamento_creme_de_queijo.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 24, 8, 0)
fim_entrega = datetime(2025, 5, 24, 17, 0)


# ============================================
# 🧊 Instanciar Gestor da Câmara
# ============================================
gestor_camaras = GestorRefrigeracaoCongelamento([camara_refrigerada_2])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [
    5000, 12000, 25000, 7000, 9000, 11000, 15000, 20000,
    18000, 14000, 17000, 13000, 23000, 10000, 8000, 16000,
    21000, 22000, 24000, 5000, 12000, 18000, 25000, 7000,
    9000, 11000, 15000, 20000, 18000
]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = ArmazenamentoSobTemperaturaParaCremeDeQueijo(
        id=i + 1,
        tipo_atividade=TipoAtividade.ARMAZENAMENTO_SOB_TEMPERATURA_PARA_CREME_DE_QUEIJO,
        tipos_profissionais_permitidos=[TipoProfissional.ALMOXARIFE],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[camara_refrigerada_2],
        quantidade_produto=quantidade,
        fips_equipamentos={camara_refrigerada_2: 1},
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
