from datetime import datetime
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividades.atividade_modular import AtividadeModular
from enums.tipo_equipamento import TipoEquipamento

# 🔧 Logger principal
logger = setup_logger("TesteHotMix")

# 📅 Janela da jornada
inicio_jornada = datetime(2025, 6, 3, 8, 0)
fim_jornada = datetime(2025, 6, 3, 18, 0)

# 🧪 ID fictício da atividade (deve existir no JSON)
id_atividade = 7  # Exemplo: ID da "massa para coxinha" ou "massa crocante"

# 🎯 Geração das quantidades de teste entre 3.000g e 50.000g
quantidades = [
    2000, 2965, 3931, 4896, 5862, 6827, 7793, 8758, 9724, 10689,
    11655, 12620, 13586, 14551, 15517, 16482, 17448, 18413, 19379,
    20344, 21310, 22275, 23241, 24206, 25172, 26137, 27103, 28068,
    29034, 30000]

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
