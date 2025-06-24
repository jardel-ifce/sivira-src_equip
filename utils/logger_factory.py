import logging
import os
from datetime import datetime


def setup_logger(nome_logger: str, arquivo: str = None, nivel=logging.INFO):
    logger = logging.getLogger(nome_logger)
    logger.setLevel(nivel)
    logger.propagate = False  # ⛔ Impede que o log suba para o root logger

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(nivel)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if arquivo:
            os.makedirs(os.path.dirname(arquivo), exist_ok=True)
            file_handler = logging.FileHandler(arquivo, encoding='utf-8')
            file_handler.setLevel(nivel)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
