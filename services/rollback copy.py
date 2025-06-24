import os
from typing import List
from models.funcionarios.funcionario import Funcionario
from utils.logger_factory import setup_logger

logger = setup_logger("Rollback")


def rollback_equipamentos(equipamentos_alocados, atividade_id, ordem_id):
    for equipamento in [e[1] for e in equipamentos_alocados]:
        try:
            if hasattr(equipamento, "liberar_por_atividade"):
                equipamento.liberar_por_atividade(atividade_id, ordem_id)
                logger.info(f"↩️ Rollback: desalocada atividade {atividade_id} de {equipamento.nome}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao desalocar de {equipamento.nome}: {e}")


def rollback_funcionarios(funcionarios: List[Funcionario], ordem_id: int):
    for funcionario in funcionarios:
        try:
            funcionario.liberar_por_ordem(ordem_id)
            logger.info(f"↩️ Rollback: funcionário {funcionario.nome} liberado da ordem {ordem_id}")
        except Exception as e:
            logger.warning(f"⚠️ Falha ao liberar funcionário {funcionario.nome}: {e}")


def remover_log_funcionarios(ordem_id: int):
    caminho = f"logs/funcionarios_{ordem_id}.log"
    try:
        if os.path.exists(caminho):
            os.remove(caminho)
            logger.info(f"🗑️ Arquivo de log removido: {caminho}")
    except Exception as e:
        logger.warning(f"⚠️ Falha ao remover log da ordem {ordem_id}: {e}")


def remover_log_equipamentos(ordem_id):
    caminho = f"logs/funcionarios_{ordem_id}.log"
    try:
        if os.path.exists(caminho):
            os.remove(caminho)
            logger.info(f"🗑️ Arquivo de log removido: {caminho}")
    except Exception as e:
        logger.warning(f"⚠️ Falha ao remover log da ordem: {e}")