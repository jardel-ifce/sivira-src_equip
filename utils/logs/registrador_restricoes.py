#!/usr/bin/env python3
"""
Registrador de Restrições de Capacidade
======================================

Módulo responsável por registrar alocações que foram feitas abaixo da capacidade mínima
dos equipamentos e gerenciar o processo de validação posterior.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from utils.logs.logger_factory import setup_logger

logger = setup_logger("RegistradorRestricoes")

class RegistradorRestricoes:
    """
    Gerencia o registro e validação de alocações com restrição de capacidade.
    """

    def __init__(self):
        self.diretorio_restricoes = "logs/restricoes"
        self._garantir_diretorio_existe()

    def _garantir_diretorio_existe(self):
        """Garante que o diretório de restrições existe."""
        if not os.path.exists(self.diretorio_restricoes):
            os.makedirs(self.diretorio_restricoes, exist_ok=True)
            logger.info(f"📁 Diretório criado: {self.diretorio_restricoes}")

    def registrar_restricao(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        equipamento_nome: str,
        capacidade_atual: float,
        capacidade_minima: float,
        inicio: datetime,
        fim: datetime,
        detalhes_extras: Dict[str, Any] = None
    ):
        """
        Registra uma alocação que foi feita abaixo da capacidade mínima.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            id_atividade: ID da atividade
            id_item: ID do item/produto
            equipamento_nome: Nome do equipamento
            capacidade_atual: Capacidade alocada (abaixo do mínimo)
            capacidade_minima: Capacidade mínima requerida
            inicio: Horário de início da alocação
            fim: Horário de fim da alocação
            detalhes_extras: Informações adicionais opcionais
        """
        # Garantir que o diretório existe antes de criar o arquivo
        self._garantir_diretorio_existe()

        arquivo_restricoes = os.path.join(
            self.diretorio_restricoes,
            f"ordem_{id_ordem}_restricoes.json"
        )

        # Carregar restrições existentes ou criar novo arquivo
        restricoes_data = self._carregar_restricoes_existentes(arquivo_restricoes)

        # Criar registro da nova restrição
        nova_restricao = {
            "id_atividade": id_atividade,
            "id_pedido": id_pedido,
            "id_item": id_item,
            "equipamento": equipamento_nome,
            "status": "PEDIDO_COM_RESTRICAO",
            "capacidade_atual": capacidade_atual,
            "capacidade_minima": capacidade_minima,
            "diferenca": capacidade_minima - capacidade_atual,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "timestamp_registro": datetime.now().isoformat(),
            "detalhes_extras": detalhes_extras or {}
        }

        # Adicionar à lista de atividades com restrição
        restricoes_data["atividades_com_restricao"].append(nova_restricao)
        restricoes_data["total_restricoes"] = len(restricoes_data["atividades_com_restricao"])
        restricoes_data["ultima_atualizacao"] = datetime.now().isoformat()

        # Salvar arquivo
        with open(arquivo_restricoes, 'w', encoding='utf-8') as f:
            json.dump(restricoes_data, f, indent=2, ensure_ascii=False)

        logger.warning(
            f"⚠️ RESTRIÇÃO REGISTRADA: Atividade {id_atividade} em {equipamento_nome} "
            f"alocada com {capacidade_atual}g (mín: {capacidade_minima}g) - "
            f"Déficit: {capacidade_minima - capacidade_atual}g"
        )

        return arquivo_restricoes

    def _carregar_restricoes_existentes(self, arquivo_restricoes: str) -> Dict[str, Any]:
        """Carrega restrições existentes ou cria estrutura nova."""
        if os.path.exists(arquivo_restricoes):
            try:
                with open(arquivo_restricoes, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ Erro ao carregar {arquivo_restricoes}: {e}")

        # Estrutura padrão para nova ordem
        return {
            "ordem": int(arquivo_restricoes.split('_')[1]),
            "timestamp_criacao": datetime.now().isoformat(),
            "status_geral": "EM_ANALISE",
            "total_restricoes": 0,
            "atividades_com_restricao": [],
            "atividades_validadas": [],
            "ultima_atualizacao": datetime.now().isoformat()
        }

    def obter_restricoes_ordem(self, id_ordem: int) -> Dict[str, Any]:
        """Obtém todas as restrições de uma ordem específica."""
        arquivo_restricoes = os.path.join(
            self.diretorio_restricoes,
            f"ordem_{id_ordem}_restricoes.json"
        )

        if os.path.exists(arquivo_restricoes):
            with open(arquivo_restricoes, 'r', encoding='utf-8') as f:
                return json.load(f)

        return {"atividades_com_restricao": [], "total_restricoes": 0}

    def listar_todas_restricoes(self) -> List[Dict[str, Any]]:
        """Lista todas as restrições de todas as ordens."""
        todas_restricoes = []

        if not os.path.exists(self.diretorio_restricoes):
            return todas_restricoes

        for arquivo in os.listdir(self.diretorio_restricoes):
            if arquivo.endswith('_restricoes.json'):
                caminho_arquivo = os.path.join(self.diretorio_restricoes, arquivo)
                try:
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        restricoes = json.load(f)
                        restricoes['arquivo'] = arquivo
                        todas_restricoes.append(restricoes)
                except Exception as e:
                    logger.error(f"❌ Erro ao ler {arquivo}: {e}")

        return todas_restricoes

    def atualizar_status_restricao(
        self,
        id_ordem: int,
        id_atividade: int,
        novo_status: str,
        motivo: str = None
    ):
        """
        Atualiza o status de uma restrição específica.

        Args:
            id_ordem: ID da ordem
            id_atividade: ID da atividade
            novo_status: Novo status ('PEDIDO_OK', 'PEDIDO_CANCELADO', etc.)
            motivo: Motivo da mudança de status
        """
        arquivo_restricoes = os.path.join(
            self.diretorio_restricoes,
            f"ordem_{id_ordem}_restricoes.json"
        )

        if not os.path.exists(arquivo_restricoes):
            logger.warning(f"⚠️ Arquivo de restrições não encontrado: {arquivo_restricoes}")
            return False

        # Carregar dados
        with open(arquivo_restricoes, 'r', encoding='utf-8') as f:
            restricoes_data = json.load(f)

        # Encontrar e atualizar a restrição
        restricao_encontrada = False
        for restricao in restricoes_data["atividades_com_restricao"]:
            if restricao["id_atividade"] == id_atividade:
                restricao["status"] = novo_status
                restricao["timestamp_atualizacao"] = datetime.now().isoformat()
                if motivo:
                    restricao["motivo_mudanca"] = motivo
                restricao_encontrada = True
                break

        if restricao_encontrada:
            # Atualizar metadados gerais
            restricoes_data["ultima_atualizacao"] = datetime.now().isoformat()

            # Salvar arquivo atualizado
            with open(arquivo_restricoes, 'w', encoding='utf-8') as f:
                json.dump(restricoes_data, f, indent=2, ensure_ascii=False)

            logger.info(
                f"✅ Status da atividade {id_atividade} atualizado para {novo_status}"
                + (f" - Motivo: {motivo}" if motivo else "")
            )
            return True
        else:
            logger.warning(f"⚠️ Atividade {id_atividade} não encontrada nas restrições")
            return False

# Instância singleton
registrador_restricoes = RegistradorRestricoes()