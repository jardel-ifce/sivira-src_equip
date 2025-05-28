import logging
import os
from datetime import datetime


def setup_logger(nome_logger: str, arquivo: str = None, nivel=logging.INFO):
    """
    Cria e retorna um logger configurado.

    :param nome_logger: Nome do logger (ex.: 'Equipamento', 'GestorRefrigeracao')
    :param arquivo: Caminho do arquivo para salvar os logs (opcional)
    :param nivel: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :return: Logger configurado
    """
    logger = logging.getLogger(nome_logger)
    logger.setLevel(nivel)

    # Se já tem handlers, não adicionar novamente
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 🔧 Handler para Console (aparece no terminal)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 🔧 Handler para Arquivo (opcional)
    if arquivo:
        # Cria a pasta se não existir
        os.makedirs(os.path.dirname(arquivo), exist_ok=True)

        file_handler = logging.FileHandler(arquivo, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
