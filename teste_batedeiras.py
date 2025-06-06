from datetime import datetime
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividades.atividade_modular import AtividadeModular

# 🔧 Logger principal
logger = setup_logger("MainTest")

# 📅 Janela da jornada
inicio_jornada = datetime(2025, 6, 3, 8, 0)
fim_jornada = datetime(2025, 6, 3, 18, 0)

# 🎯 ID da atividade genérica
id_atividade = 6

# 🧪 15 quantidades entre 3.000g e 20.000g (crescimento progressivo)
quantidades = list(range(3000, 20001, 1200))[:15]  # Gera: [3000, 4200, 5400, ..., 19800]

# 🧾 Executa 15 instâncias da atividade
atividades_alocadas = []

for i, quantidade in enumerate(quantidades, start=1):
    logger.info("==============================================")
    logger.info(f"▶️ Execução #{i} | Quantidade: {quantidade}g")

    try:
        atividade = AtividadeModular(id=i, id_atividade=id_atividade, quantidade_produto=quantidade)
        sucesso = atividade.tentar_alocar_e_iniciar(inicio_jornada=inicio_jornada, fim_jornada=fim_jornada)

        if sucesso:
            atividades_alocadas.append(atividade)
            logger.info(f"✅ Alocada de {atividade.inicio_real.strftime('%H:%M')} até {atividade.fim_real.strftime('%H:%M')}")
        else:
            logger.warning(f"⚠️ Atividade #{i} não pôde ser alocada.")
            break

    except Exception as e:
        logger.error(f"❌ Erro na execução #{i}: {e}")
        break

# 📅 Exibe agenda da última atividade que teve sucesso
if atividades_alocadas:
    logger.info("📋 Exibindo agendas após todas as execuções válidas:")
    atividades_alocadas[-1].mostrar_agendas_dos_gestores()
