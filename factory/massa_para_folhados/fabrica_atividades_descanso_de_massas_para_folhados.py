# fabrica_atividades_descanso_massas_para_folhados.py

# =========================================
# 🔧 Ajuste de path conforme seu ambiente
# =========================================
import sys
from datetime import datetime

sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

# =========================================
# 📦 Imports
# =========================================
from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import camara_refrigerada_1, freezer_2
from models.atividades.subproduto.massa_para_folhados.descanso_de_massas_para_folhados import (
    DescansoDeMassasParaFolhados,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_refrigeracao_congelamento import GestorRefrigeracaoCongelamento

# =========================================
# 🔥 Logger
# =========================================
logger = setup_logger(
    "SimulacaoDescansoMassasFolhadas",
    arquivo="logs/simulacao_descanso_massas_folhadas.log"
)

# =========================================
# ⏰ Janela de Produção
# =========================================
inicio_jornada = datetime(2025, 5, 25, 8, 0)
fim_jornada = datetime(2025, 5, 25, 17, 0)

# =========================================
# ❄️ Instanciar Gestor de Câmara/Freezer
# =========================================
gestor_camaras = GestorRefrigeracaoCongelamento([
    camara_refrigerada_1,
    freezer_2
])

# =========================================
# 📦 Quantidades simuladas
# =========================================
quantidades = [5000, 12000, 18000, 4000, 5000, 12000, 18000, 4000]

# =========================================
# 🏗️ Criar Atividades
# =========================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = DescansoDeMassasParaFolhados(
        id=i + 1,
        tipo_atividade=TipoAtividade.DESCANSO_DE_MASSAS_PARA_FOLHADOS,
        tipos_profissionais_permitidos=[
            TipoProfissional.CONFEITEIRO,
            TipoProfissional.AUXILIAR_DE_CONFEITEIRO
        ],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[camara_refrigerada_1, freezer_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            camara_refrigerada_1: 2,
            freezer_2: 1,
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de descanso de massas para folhados criadas.")

# =========================================
# ❄️ Tentar Alocar e Iniciar Atividades
# =========================================
for atividade in atividades:
    sucesso = atividade.tentar_alocar_e_iniciar(
        gestor_refrigeracao=gestor_camaras,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada,
        temperatura_desejada=-18
    )

    if sucesso:
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada dentro da janela "
            f"{inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}."
        )

# ============================================
# 📅 Mostrar Agenda Final
# ============================================
gestor_camaras.mostrar_agenda()
