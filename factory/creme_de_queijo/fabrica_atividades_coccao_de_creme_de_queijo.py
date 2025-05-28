# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from factory.fabrica_equipamentos import fogao_1, fogao_2
from models.atividades.subproduto.creme_de_queijo.coccao_de_creme_de_queijo import (
    CoccaoDeCremeDeQueijo,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_fogoes import GestorFogoes
from utils.logger_factory import setup_logger


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoCoccaoCremeDeQueijo",
    arquivo="logs/simulacao_coccao_creme_de_queijo.log"
)


# ============================================
# ⏰ Janela de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 24, 8, 0)
fim_entrega = datetime(2025, 5, 24, 17, 0)


# ============================================
# 🛠️ Instanciar Gestor de Fogões
# ============================================
gestor_fogoes = GestorFogoes([fogao_1, fogao_2])


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 15000, 22000, 45000, 60000]


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = CoccaoDeCremeDeQueijo(
        id=i + 1,
        tipo_atividade=TipoAtividade.COCCAO_DE_CREME_DE_QUEIJO,
        tipos_profissionais_permitidos=[TipoProfissional.COZINHEIRO],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[fogao_1, fogao_2],
        quantidade_produto=quantidade,
        fips_equipamentos={
            fogao_1: 1,  # ✅ Prioridade para Fogão 1
            fogao_2: 2,  # ✅ Fogão 2 é a segunda opção
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de cocção de creme de queijo criadas.")


# ============================================
# 🔥 Tentar Alocar e Iniciar Atividades
# ============================================
for atividade in atividades:
    sucesso, fogao, inicio_real, fim_real = gestor_fogoes.alocar(
        inicio=inicio_jornada,
        fim=fim_entrega,
        atividade=atividade
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada no {fogao.nome} "
            f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}."
        )
        atividade.inicio_real = inicio_real
        atividade.fim_real = fim_real
        atividade.fogao_alocado = fogao
        atividade.alocada = True
        atividade.iniciar()
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada até {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
gestor_fogoes.mostrar_agenda()
