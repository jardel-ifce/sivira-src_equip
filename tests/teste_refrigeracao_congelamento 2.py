from datetime import datetime
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividades.atividade_modular import AtividadeModular

# 🔧 Logger principal
logger = setup_logger("MainTest")

# 📅 Janela da jornada
inicio_jornada = datetime(2025, 6, 3, 8, 0)
fim_jornada = datetime(2025, 6, 3, 18, 0)

# 🎯 Quantidades fixas de teste (ajustáveis)
quantidades = [int(x) for x in range(3000, 20001, int((20000 - 3000) / 29))]

# 🧾 Execução de atividades com diferentes IDs
atividades_alocadas = []


contador_global = 1

# 🧪 10 atividades com id = 9
for i in range(10):
    logger.info("==============================================")
    logger.info(f"▶️ Execução #{contador_global} | Quantidade: {quantidades[i % len(quantidades)]}g")
    try:
        atividade = AtividadeModular(
            id=contador_global,
            id_atividade=9,
            quantidade_produto=quantidades[i % len(quantidades)]
        )
        sucesso = atividade.tentar_alocar_e_iniciar(inicio_jornada, fim_jornada)
        if sucesso:
            atividades_alocadas.append(atividade)
            logger.info(f"✅ Alocada de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')}")
        else:
            logger.warning(f"⚠️ Atividade #{contador_global} não pôde ser alocada.")
    except Exception as e:
        logger.error(f"❌ Erro na execução #{contador_global}: {e}")
    contador_global += 1


# 📋 Exibe agendas
if atividades_alocadas:
    logger.info("📋 Exibindo agendas após todas as execuções válidas:")
    atividades_alocadas[-1].mostrar_agendas_dos_gestores()
