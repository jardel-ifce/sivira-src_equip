#!/usr/bin/env python3
"""
Registrador de Requisitos de Funcionários
=========================================

Módulo responsável por registrar os tipos de funcionários necessários
para cada atividade, similar ao sistema de logs de equipamentos.
"""

import os
from datetime import datetime
from typing import Set, Dict, Any
from enums.funcionarios.tipo_profissional import TipoProfissional
from utils.logs.logger_factory import setup_logger

logger = setup_logger("RegistradorFuncionarios")


class RegistradorFuncionarios:
    """
    Gerencia o registro de requisitos de funcionários em formato .log
    similar aos logs de equipamentos.
    """

    def __init__(self):
        self.diretorio_funcionarios = "logs/tipos_funcionarios_requeridos"
        self._garantir_diretorio_existe()
        # Contador por pedido para rastrear requisitos automaticamente
        self._contadores = {}

    def _garantir_diretorio_existe(self):
        """Garante que o diretório de tipos de funcionários existe."""
        if not os.path.exists(self.diretorio_funcionarios):
            os.makedirs(self.diretorio_funcionarios, exist_ok=True)
            logger.info(f"📁 Diretório criado: {self.diretorio_funcionarios}")

    def registrar_requisito_funcionario(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_atividade: str,
        tipos_profissionais: Set[TipoProfissional],
        inicio: datetime,
        fim: datetime,
        quantidade: int,
        fips: Dict[str, Any] = None
    ):
        """
        Registra um requisito de funcionário para uma atividade específica.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            id_atividade: ID da atividade
            nome_atividade: Nome da atividade
            tipos_profissionais: Conjunto de tipos profissionais permitidos
            inicio: Horário de início da atividade
            fim: Horário de fim da atividade
            quantidade: Quantidade de funcionários necessários
            fips: Fatores de prioridade por tipo
        """
        try:
            # Nome do arquivo no formato: ordem: X | pedido: Y.log
            nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
            caminho_arquivo = os.path.join(self.diretorio_funcionarios, nome_arquivo)

            # Verificar se arquivo já existe (modo append)
            modo = 'a' if os.path.exists(caminho_arquivo) else 'w'

            with open(caminho_arquivo, modo, encoding='utf-8') as f:
                if modo == 'w':
                    # Escrever cabeçalho apenas se for novo arquivo
                    self._escrever_cabecalho(f, id_ordem, id_pedido)

                # Registrar o requisito
                self._escrever_requisito(
                    f, id_atividade, nome_atividade, tipos_profissionais,
                    inicio, fim, quantidade, fips
                )

            logger.debug(
                f"📄 Requisito registrado: Atividade {id_atividade} "
                f"({len(tipos_profissionais)} tipos, {quantidade} funcionários) "
                f"em {nome_arquivo}"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao registrar requisito de funcionário: {e}")

    def _escrever_cabecalho(self, arquivo, id_ordem: int, id_pedido: int):
        """Escreve o cabeçalho do arquivo de log."""
        arquivo.write("=" * 80 + "\n")
        arquivo.write("📋 LOG DE TIPOS DE FUNCIONÁRIOS REQUERIDOS\n")
        arquivo.write("=" * 80 + "\n")
        arquivo.write(f"Ordem: {id_ordem}\n")
        arquivo.write(f"Pedido: {id_pedido}\n")
        arquivo.write(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        arquivo.write("=" * 80 + "\n\n")

    def _escrever_requisito(
        self,
        arquivo,
        id_atividade: int,
        nome_atividade: str,
        tipos_profissionais: Set[TipoProfissional],
        inicio: datetime,
        fim: datetime,
        quantidade: int,
        fips: Dict[str, Any] = None
    ):
        """Escreve um requisito específico no arquivo."""
        arquivo.write(f"🔸 ATIVIDADE {id_atividade}: {nome_atividade}\n")
        arquivo.write(f"   ⏰ Horário: {inicio.strftime('%H:%M')} [{inicio.strftime('%d/%m/%Y')}] - {fim.strftime('%H:%M')} [{fim.strftime('%d/%m/%Y')}]\n")
        arquivo.write(f"   👥 Funcionários necessários: {quantidade}\n")

        # Tipos profissionais
        tipos_str = ", ".join([tipo.name for tipo in tipos_profissionais])
        arquivo.write(f"   👨‍💼 Tipos permitidos: {tipos_str}\n")

        # FIPs se disponíveis
        if fips:
            fips_str = ", ".join([f"{k}:{v}" for k, v in fips.items()])
            arquivo.write(f"   🎯 Prioridades (FIPs): {fips_str}\n")

        arquivo.write(f"   📅 Registrado: {datetime.now().strftime('%H:%M:%S')}\n")
        arquivo.write("\n")

    def finalizar_log(self, id_ordem: int, id_pedido: int, total_requisitos: int = 0):
        """
        Finaliza o log com estatísticas finais.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            total_requisitos: Total de requisitos registrados
        """
        try:
            nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
            caminho_arquivo = os.path.join(self.diretorio_funcionarios, nome_arquivo)

            if os.path.exists(caminho_arquivo):
                with open(caminho_arquivo, 'a', encoding='utf-8') as f:
                    f.write("-" * 80 + "\n")
                    f.write("📊 RESUMO FINAL\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"Total de requisitos registrados: {total_requisitos}\n")
                    f.write(f"Finalizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n")

                logger.info(f"📄 Log finalizado: {nome_arquivo} ({total_requisitos} requisitos)")
            else:
                # Criar log vazio se nenhum requisito foi registrado
                with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                    self._escrever_cabecalho(f, id_ordem, id_pedido)
                    f.write("ℹ️ Nenhum requisito de funcionário foi coletado.\n")
                    f.write("   Possíveis causas:\n")
                    f.write("   - Atividades não requerem funcionários\n")
                    f.write("   - Falha na execução antes da coleta\n\n")
                    f.write("-" * 80 + "\n")
                    f.write("📊 RESUMO FINAL\n")
                    f.write("-" * 80 + "\n")
                    f.write("Total de requisitos registrados: 0\n")
                    f.write(f"Finalizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n")

                logger.info(f"📄 Log vazio criado: {nome_arquivo}")

        except Exception as e:
            logger.error(f"❌ Erro ao finalizar log: {e}")

    def obter_caminho_log(self, id_ordem: int, id_pedido: int) -> str:
        """
        Retorna o caminho completo do arquivo de log.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido

        Returns:
            Caminho completo do arquivo
        """
        nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
        return os.path.join(self.diretorio_funcionarios, nome_arquivo)

    def log_existe(self, id_ordem: int, id_pedido: int) -> bool:
        """
        Verifica se já existe um log para a ordem e pedido.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido

        Returns:
            True se o arquivo existe, False caso contrário
        """
        caminho = self.obter_caminho_log(id_ordem, id_pedido)
        return os.path.exists(caminho)


# Instância global para uso direto
registrador_funcionarios = RegistradorFuncionarios()


# Funções auxiliares para uso simplificado
def registrar_funcionario(
    id_ordem: int,
    id_pedido: int,
    id_atividade: int,
    nome_atividade: str,
    tipos_profissionais: Set[TipoProfissional],
    inicio: datetime,
    fim: datetime,
    quantidade: int,
    fips: Dict[str, Any] = None
):
    """
    Função auxiliar para registrar requisito de funcionário.

    Args:
        id_ordem: ID da ordem
        id_pedido: ID do pedido
        id_atividade: ID da atividade
        nome_atividade: Nome da atividade
        tipos_profissionais: Conjunto de tipos profissionais
        inicio: Horário de início
        fim: Horário de fim
        quantidade: Quantidade de funcionários
        fips: Fatores de prioridade
    """
    registrador_funcionarios.registrar_requisito_funcionario(
        id_ordem, id_pedido, id_atividade, nome_atividade,
        tipos_profissionais, inicio, fim, quantidade, fips
    )


def finalizar_log_funcionarios(id_ordem: int, id_pedido: int, total_requisitos: int = 0):
    """
    Função auxiliar para finalizar log de funcionários.

    Args:
        id_ordem: ID da ordem
        id_pedido: ID do pedido
        total_requisitos: Total de requisitos registrados
    """
    registrador_funcionarios.finalizar_log(id_ordem, id_pedido, total_requisitos)