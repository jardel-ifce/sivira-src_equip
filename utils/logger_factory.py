import logging
import os
from datetime import datetime


def setup_logger(nome_logger: str, arquivo: str = None, nivel=logging.INFO):
    logger = logging.getLogger(nome_logger)
    logger.setLevel(nivel)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 🔧 Handler para Console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(nivel)  # ✅ ESSA LINHA FAZ TUDO FUNCIONAR
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 🔧 Handler para Arquivo (opcional)
    if arquivo:
        os.makedirs(os.path.dirname(arquivo), exist_ok=True)
        file_handler = logging.FileHandler(arquivo, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(nivel)  # ✅ se quiser que o arquivo também registre debug
        logger.addHandler(file_handler)

    return logger
