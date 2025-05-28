# ============================================
# 📦 Imports
# ============================================
import sys
from datetime import datetime

# 🔧 Ajuste de path conforme seu ambiente
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/")

from utils.logger_factory import setup_logger
from factory.fabrica_equipamentos import bancada_7, balanca_digital_4
from models.atividades.subproduto.creme_de_queijo.preparo_para_armazenamento_creme_de_queijo import (
    PreparoParaArmazenamentoCremeDeQueijo,
)
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from services.gestor_bancadas import GestorBancadas
from services.gestor_balancas import GestorBalancas


# ============================================
# 🔥 Logger
# ============================================
logger = setup_logger(
    "SimulacaoPreparoArmazenamentoCremeDeQueijo",
    arquivo="logs/simulacao_preparo_armazenamento_creme_de_queijo.log"
)


# ============================================
# ⏰ Jornada de Produção
# ============================================
inicio_jornada = datetime(2025, 5, 25, 8, 0)
fim_entrega = datetime(2025, 5, 25, 17, 0)


# ============================================
# 🛠️ Instanciar Gestores
# ============================================
gestor_bancadas = GestorBancadas([bancada_7])
gestor_balancas = GestorBalancas([balanca_digital_4])

print("==== 🧠 Debug: Capacidade dos Equipamentos ====")
print(f"Bancada 7: {bancada_7.capacidade_fracionamento} -> {bancada_7.capacidade_total}")
print(f"Balança 4: Capacidade única (ocupação exclusiva no tempo)")
print("================================================\n")


# ============================================
# 📦 Quantidades simuladas
# ============================================
quantidades = [5000, 15000, 22000, 50000]  # 🔥 Pode ajustar conforme necessidade


# ============================================
# 🏗️ Criar Atividades
# ============================================
atividades = []

for i, quantidade in enumerate(quantidades):
    atividade = PreparoParaArmazenamentoCremeDeQueijo(
        id=i + 1,
        tipo_atividade=TipoAtividade.PREPARO_PARA_ARMAZENAMENTO_DE_CREME_DE_QUEIJO,
        tipos_profissionais_permitidos=[TipoProfissional.COZINHEIRO],
        quantidade_funcionarios=1,
        equipamentos_elegiveis=[bancada_7, balanca_digital_4],
        quantidade_produto=quantidade,
        fips_equipamentos={
            bancada_7: 1,
            balanca_digital_4: 1,
        },
    )
    atividade.calcular_duracao()
    atividades.append(atividade)

logger.info(f"🛠️ {len(atividades)} atividades de preparo para armazenamento criadas.")


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
        porcoes_bancada=3  # 🔥 Ocupa 3 porções da bancada
    )

    if sucesso:
        logger.info(
            f"✅ Atividade {atividade.id} alocada com sucesso: "
            f"Bancada {atividade.bancada_alocada.nome} de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')} "
            f"e Balança {atividade.balanca_alocada.nome}."
        )
    else:
        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada dentro da janela "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_entrega.strftime('%H:%M')}."
        )


# ============================================
# 📅 Mostrar Agendas Finais
# ============================================
gestor_bancadas.mostrar_agenda()
gestor_balancas.mostrar_agenda()
