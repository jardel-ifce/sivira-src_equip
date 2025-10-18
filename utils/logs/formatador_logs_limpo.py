# utils/logs/formatador_logs_limpo.py
"""
Formatador de logs limpos para o sistema de alocação de equipamentos.
Converte logs técnicos em formato legível e organizado.
"""

import re
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List


class FormatadorLogsLimpo:
    """
    Formatador responsável por converter logs técnicos em formato limpo e organizado.
    """
    
    @staticmethod
    def formatar_erro_execucao_pedido(id_ordem: int, id_pedido: int, erro: Exception) -> str:
        """
        Formata erro de execução de pedido no padrão limpo definido.
        
        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido  
            erro: Exceção capturada
            
        Returns:
            String formatada no padrão limpo
        """
        
        # Extrair informações do erro
        erro_info = FormatadorLogsLimpo._extrair_informacoes_erro(erro)
        
        # Montar cabeçalho
        log_formatado = "=" * 46 + "\n"
        log_formatado += f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_formatado += f"🧾 Ordem: {id_ordem} | Pedido: {id_pedido}\n"
        log_formatado += f"{erro_info['emoji']} Tipo de Erro: {erro_info['tipo']}\n"
        log_formatado += "-" * 50 + "\n\n"
        
        # Título do erro
        log_formatado += f"❌ {erro_info['titulo']}\n\n"
        
        # Problema principal
        log_formatado += f"Problema: {erro_info['problema']}\n\n"
        
        # Seções específicas baseadas no tipo
        if erro_info['tipo'] == 'TEMPO':
            log_formatado += FormatadorLogsLimpo._formatar_secao_tempo(erro_info)
        elif erro_info['tipo'] == 'QUANTIDADE':
            log_formatado += FormatadorLogsLimpo._formatar_secao_quantidade(erro_info)
        else:
            log_formatado += FormatadorLogsLimpo._formatar_secao_generica(erro_info)
        
        # Sugestões
        if erro_info.get('sugestoes'):
            log_formatado += "\n💡 Sugestões:\n"
            for sugestao in erro_info['sugestoes']:
                log_formatado += f"   • {sugestao}\n"
        
        log_formatado += "\n" + "=" * 46
        
        return log_formatado
    
    @staticmethod
    def _extrair_informacoes_erro(erro: Exception) -> Dict[str, Any]:
        """
        Extrai informações estruturadas da exceção para formatação.
        """
        erro_str = str(erro)
        erro_info = {
            'emoji': '⚠️',
            'tipo': 'GENERICO',
            'titulo': 'ERRO GENÉRICO',
            'problema': erro_str,
            'detalhes': {},
            'sugestoes': []
        }
        
        # Detectar tipo de erro baseado na mensagem
        if "Tempo máximo de espera excedido entre atividades" in erro_str:
            erro_info.update(FormatadorLogsLimpo._processar_erro_tempo_inter(erro_str))
        elif "Erro de tempo entre equipamentos" in erro_str:
            erro_info.update(FormatadorLogsLimpo._processar_erro_tempo_intra(erro_str))
        elif any(palavra in erro_str for palavra in ["quantidade", "capacidade", "QUANTIDADE"]):
            erro_info.update(FormatadorLogsLimpo._processar_erro_quantidade(erro_str))
        elif "Janela temporal completamente esgotada" in erro_str:
            erro_info.update(FormatadorLogsLimpo._processar_erro_janela_temporal(erro_str))
        
        return erro_info
    
    @staticmethod
    def _processar_erro_tempo_inter(erro_str: str) -> Dict[str, Any]:
        """Processa erros de tempo entre atividades."""
        
        # Extrair informações usando regex
        atividade_atual_match = re.search(r"Atividade atual: (\d+) \(([^)]+)\)", erro_str)
        atividade_sucessora_match = re.search(r"Atividade sucessora: (\d+) \(([^)]+)\)", erro_str)
        fim_atual_match = re.search(r"Fim da atual: ([^\n]+)", erro_str)
        inicio_sucessora_match = re.search(r"Início da sucessora: ([^\n]+)", erro_str)
        atraso_match = re.search(r"Atraso detectado: ([^\n]+)", erro_str)
        maximo_match = re.search(r"Máximo permitido: ([^\n]+)", erro_str)
        excesso_match = re.search(r"Excesso: ([^\n]+)", erro_str)
        
        atividade_atual = {}
        atividade_sucessora = {}
        conflito = {}
        
        if atividade_atual_match:
            atividade_atual = {
                'nome': atividade_atual_match.group(2),
                'termino': fim_atual_match.group(1) if fim_atual_match else 'N/A'
            }
        
        if atividade_sucessora_match:
            atividade_sucessora = {
                'nome': atividade_sucessora_match.group(2),
                'inicio_disponivel': inicio_sucessora_match.group(1) if inicio_sucessora_match else 'N/A'
            }
        
        if atraso_match and maximo_match and excesso_match:
            conflito = {
                'tempo_de_espera_maximo': maximo_match.group(1),
                'atraso_real': atraso_match.group(1),
                'excesso': excesso_match.group(1)
            }
        
        return {
            'emoji': '⚠️',
            'tipo': 'TEMPO',
            'titulo': 'ERRO DE TEMPO/CONFLITO',
            'problema': 'Tempo máximo de espera excedido entre atividades. ' + 
                       (f"Atraso de {atraso_match.group(1)} excede o máximo permitido." if atraso_match else ""),
            'atividade_atual': atividade_atual,
            'atividade_sucessora': atividade_sucessora,
            'conflito': conflito,
            'sugestoes': [
                'Verificar disponibilidade de equipamentos',
                'Ajustar sequenciamento das atividades',
                'Considerar recursos alternativos'
            ]
        }
    
    @staticmethod
    def _processar_erro_tempo_intra(erro_str: str) -> Dict[str, Any]:
        """Processa erros de tempo dentro de atividades."""
        return {
            'emoji': '🔧',
            'tipo': 'TEMPO',
            'titulo': 'ERRO DE TEMPO ENTRE EQUIPAMENTOS',
            'problema': 'Equipamentos da mesma atividade não conseguem executar em sequência dentro do tempo permitido.',
            'sugestoes': [
                'Verificar sincronização entre equipamentos',
                'Revisar configuração de timing da atividade',
                'Considerar equipamentos alternativos'
            ]
        }
    
    @staticmethod
    def _processar_erro_quantidade(erro_str: str) -> Dict[str, Any]:
        """Processa erros de quantidade/capacidade."""
        return {
            'emoji': '📊',
            'tipo': 'QUANTIDADE',
            'titulo': 'ERRO DE QUANTIDADE/CAPACIDADE',
            'problema': 'A quantidade solicitada não pode ser atendida pelos equipamentos disponíveis.',
            'sugestoes': [
                'Verificar capacidade dos equipamentos',
                'Considerar divisão em lotes menores',
                'Revisar especificações do pedido'
            ]
        }
    
    @staticmethod
    def _processar_erro_janela_temporal(erro_str: str) -> Dict[str, Any]:
        """Processa erros de janela temporal esgotada."""
        tentativas_match = re.search(r"após (\d+(?:,\d+)*) tentativas", erro_str)
        tentativas = tentativas_match.group(1) if tentativas_match else "muitas"
        
        return {
            'emoji': '⏰',
            'tipo': 'TEMPO',
            'titulo': 'JANELA TEMPORAL ESGOTADA',
            'problema': f'Impossível encontrar horário disponível após {tentativas} tentativas. Janela de produção insuficiente.',
            'sugestoes': [
                'Expandir janela temporal de produção',
                'Verificar conflitos de equipamentos',
                'Considerar replanejamento do pedido',
                'Revisar prioridades de produção'
            ]
        }
    
    @staticmethod
    def _formatar_secao_tempo(erro_info: Dict[str, Any]) -> str:
        """Formata seção específica para erros de tempo."""
        secao = ""
        
        if erro_info.get('atividade_atual'):
            secao += "📋 Atividade atual:\n"
            ativ = erro_info['atividade_atual']
            secao += f"   • Nome: {ativ.get('nome', 'N/A')}\n"
            if 'termino' in ativ:
                secao += f"   • Término: {ativ['termino']}\n"
            secao += "\n"
        
        if erro_info.get('atividade_sucessora'):
            secao += "📋 Atividade sucessora:\n"
            ativ = erro_info['atividade_sucessora']
            secao += f"   • Nome: {ativ.get('nome', 'N/A')}\n"
            if 'inicio_disponivel' in ativ:
                secao += f"   • Início disponível: {ativ['inicio_disponivel']}\n"
            secao += "\n"
        
        if erro_info.get('conflito'):
            secao += "⏱️ Conflito:\n"
            conf = erro_info['conflito']
            for chave, valor in conf.items():
                chave_limpa = chave.replace('_', ' ').title()
                secao += f"   • {chave_limpa}: {valor}\n"
            secao += "\n"
        
        return secao
    
    @staticmethod
    def _formatar_secao_quantidade(erro_info: Dict[str, Any]) -> str:
        """Formata seção específica para erros de quantidade."""
        secao = "📊 Detalhes do erro:\n"
        secao += f"   • Tipo: Incompatibilidade de capacidade\n"
        secao += f"   • Causa: {erro_info.get('problema', 'Erro de quantidade')}\n\n"
        return secao
    
    @staticmethod
    def _formatar_secao_generica(erro_info: Dict[str, Any]) -> str:
        """Formata seção genérica para outros tipos de erro."""
        secao = "ℹ️ Informações adicionais:\n"
        secao += f"   • Detalhes técnicos disponíveis nos logs do sistema\n\n"
        return secao


# Função de conveniência para integração com o sistema existente
def formatar_erro_para_log_limpo(id_ordem: int, id_pedido: int, erro: Exception) -> str:
    """
    Função de conveniência para formatar erro no padrão limpo.
    Pode ser usada diretamente no gerenciador_logs.py
    """
    return FormatadorLogsLimpo.formatar_erro_execucao_pedido(id_ordem, id_pedido, erro)


# Modificação para integrar com gerenciador_logs.py existente
def registrar_erro_execucao_pedido_limpo(id_ordem: int, id_pedido: int, erro: Exception):
    """
    Versão modificada da função original que gera logs limpos.
    Substitui a função existente em gerenciador_logs.py
    """
    from utils.logs.logger_factory import setup_logger
    import os
    
    logger = setup_logger("GerenciadorLogs")
    
    # Log no terminal (mantém funcionalidade original)
    logger.error(f"⚠️ Erro na execução do pedido {id_pedido}: {erro.__class__.__name__}: {erro}")
    
    # Gerar log limpo formatado
    log_limpo = FormatadorLogsLimpo.formatar_erro_execucao_pedido(id_ordem, id_pedido, erro)
    
    # Salvar em arquivo com formato limpo
    try:
        os.makedirs("logs/equipamentos/erros", exist_ok=True)
        nome_arquivo = f"logs/equipamentos/erros/ordem: {id_ordem} | pedido: {id_pedido}.log"
        
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(log_limpo)
            
        logger.info(f"📝 Log limpo salvo: {nome_arquivo}")
        
    except Exception as log_erro:
        logger.warning(f"⚠️ Falha ao salvar log limpo: {log_erro}")
