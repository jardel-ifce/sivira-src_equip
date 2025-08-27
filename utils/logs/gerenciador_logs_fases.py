#!/usr/bin/env python3
"""
📂 Gerenciador de Logs por Fases
Controla onde os logs de equipamentos são salvos baseado na fase do pedido
"""

import os
from typing import Optional
from utils.logs.logger_factory import setup_logger

logger = setup_logger("GerenciadorLogsFases")

class GerenciadorLogsFases:
    """
    Gerencia logs separados por fases:
    - ETAPA 2 (Reserva): logs/equipamentos_reservados/
    - ETAPA 4 (Execução): logs/equipamentos/
    """
    
    # Diretórios base
    DIR_LOGS_RESERVADOS = "logs/equipamentos_reservados"
    DIR_LOGS_EXECUTADOS = "logs/equipamentos"
    
    @classmethod
    def criar_diretorios(cls):
        """Cria os diretórios necessários se não existirem"""
        os.makedirs(cls.DIR_LOGS_RESERVADOS, exist_ok=True)
        os.makedirs(cls.DIR_LOGS_EXECUTADOS, exist_ok=True)
        logger.debug("Diretórios de logs criados/verificados")
    
    @classmethod
    def obter_caminho_log_reserva(cls, id_ordem: int, id_pedido: int) -> str:
        """Retorna o caminho para log de reserva"""
        cls.criar_diretorios()
        nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
        return os.path.join(cls.DIR_LOGS_RESERVADOS, nome_arquivo)
    
    @classmethod
    def obter_caminho_log_execucao(cls, id_ordem: int, id_pedido: int) -> str:
        """Retorna o caminho para log de execução"""
        cls.criar_diretorios()
        nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
        return os.path.join(cls.DIR_LOGS_EXECUTADOS, nome_arquivo)
    
    @classmethod
    def mover_log_para_execucao(cls, id_ordem: int, id_pedido: int) -> bool:
        """
        Move log de reserva para execução quando pedido é confirmado
        
        Returns:
            bool: True se moveu com sucesso, False se não encontrou arquivo
        """
        caminho_reserva = cls.obter_caminho_log_reserva(id_ordem, id_pedido)
        caminho_execucao = cls.obter_caminho_log_execucao(id_ordem, id_pedido)
        
        if os.path.exists(caminho_reserva):
            try:
                # Ler conteúdo do log de reserva
                with open(caminho_reserva, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                
                # Adicionar header indicando mudança de fase
                header_execucao = (
                    f"=== PEDIDO CONFIRMADO PARA EXECUÇÃO ===\n"
                    f"Ordem: {id_ordem} | Pedido: {id_pedido}\n"
                    f"Movido de: {caminho_reserva}\n"
                    f"===================================\n\n"
                )
                
                # Escrever no diretório de execução
                with open(caminho_execucao, 'w', encoding='utf-8') as f:
                    f.write(header_execucao + conteudo)
                
                # Remover arquivo de reserva
                os.remove(caminho_reserva)
                
                logger.info(f"Log movido para execução: ordem {id_ordem}, pedido {id_pedido}")
                return True
                
            except Exception as e:
                logger.error(f"Erro ao mover log: {e}")
                return False
        else:
            logger.warning(f"Log de reserva não encontrado para mover: {caminho_reserva}")
            return False
    
    @classmethod
    def remover_log_reserva(cls, id_ordem: int, id_pedido: int) -> bool:
        """
        Remove log de reserva (quando pedido é cancelado)
        
        Returns:
            bool: True se removeu com sucesso, False se não encontrou arquivo
        """
        caminho_reserva = cls.obter_caminho_log_reserva(id_ordem, id_pedido)
        
        if os.path.exists(caminho_reserva):
            try:
                os.remove(caminho_reserva)
                logger.info(f"Log de reserva removido: ordem {id_ordem}, pedido {id_pedido}")
                return True
            except Exception as e:
                logger.error(f"Erro ao remover log de reserva: {e}")
                return False
        else:
            logger.debug(f"Log de reserva não encontrado para remover: {caminho_reserva}")
            return False
    
    @classmethod
    def listar_logs_reservados(cls) -> list:
        """Lista todos os logs na pasta de reservados"""
        cls.criar_diretorios()
        try:
            arquivos = []
            for arquivo in os.listdir(cls.DIR_LOGS_RESERVADOS):
                if arquivo.endswith('.log'):
                    caminho_completo = os.path.join(cls.DIR_LOGS_RESERVADOS, arquivo)
                    arquivos.append({
                        'nome': arquivo,
                        'caminho': caminho_completo,
                        'tamanho': os.path.getsize(caminho_completo)
                    })
            return sorted(arquivos, key=lambda x: x['nome'])
        except Exception as e:
            logger.error(f"Erro ao listar logs reservados: {e}")
            return []
    
    @classmethod
    def listar_logs_executados(cls) -> list:
        """Lista todos os logs na pasta de executados"""
        cls.criar_diretorios()
        try:
            arquivos = []
            for arquivo in os.listdir(cls.DIR_LOGS_EXECUTADOS):
                if arquivo.endswith('.log'):
                    caminho_completo = os.path.join(cls.DIR_LOGS_EXECUTADOS, arquivo)
                    arquivos.append({
                        'nome': arquivo,
                        'caminho': caminho_completo,
                        'tamanho': os.path.getsize(caminho_completo)
                    })
            return sorted(arquivos, key=lambda x: x['nome'])
        except Exception as e:
            logger.error(f"Erro ao listar logs executados: {e}")
            return []
    
    @classmethod
    def obter_estatisticas(cls) -> dict:
        """Retorna estatísticas dos logs por fase"""
        logs_reservados = cls.listar_logs_reservados()
        logs_executados = cls.listar_logs_executados()
        
        return {
            'reservados': {
                'total': len(logs_reservados),
                'tamanho_total': sum(log['tamanho'] for log in logs_reservados)
            },
            'executados': {
                'total': len(logs_executados),
                'tamanho_total': sum(log['tamanho'] for log in logs_executados)
            }
        }