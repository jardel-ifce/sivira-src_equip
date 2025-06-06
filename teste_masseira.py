from datetime import datetime
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividades.atividade_modular import AtividadeModular
from enums.tipo_equipamento import TipoEquipamento

# 🔧 Logger principal
logger = setup_logger("TesteMasseiras")

# 📅 Janela da jornada
inicio_jornada = datetime(2025, 6, 3, 8, 0)
fim_jornada = datetime(2025, 6, 3, 18, 0)

# 🧪 ID fictício da atividade (deve existir no JSON)
id_atividade = 5  # Exemplo: ID da "massa para coxinha" ou "massa crocante"

# 🎯 Geração das quantidades de teste entre 3.000g e 50.000g
quantidades = [3000, 60000] # Exemplo: [3000, 7700, 12400, ..., 50000]

atividades_alocadas = []

for i, quantidade in enumerate(quantidades, start=1):
    logger.info("==============================================")
    logger.info(f"▶️ Execução #{i} | Quantidade: {quantidade}g")

    try:
        atividade = AtividadeModular(
            id=i,
            id_atividade=id_atividade,
            quantidade_produto=quantidade
        )

        sucesso = atividade.tentar_alocar_e_iniciar(
            inicio_jornada=inicio_jornada,
            fim_jornada=fim_jornada
        )

        if sucesso:
            atividades_alocadas.append(atividade)
            logger.info(f"✅ Alocada de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')}")
        else:
            logger.warning(f"⚠️ Atividade #{i} não pôde ser alocada.")
            break

    except Exception as e:
        logger.error(f"❌ Erro na execução #{i}: {e}")
        break

# 📋 Exibe agenda final das masseiras se houver sucesso
if atividades_alocadas:
    logger.info("📋 Exibindo agendas após todas as execuções válidas:")
    atividades_alocadas[-1].mostrar_agendas_dos_gestores()
