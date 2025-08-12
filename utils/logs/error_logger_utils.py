# utils/logs/error_logger.py
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from utils.logs.logger_factory import setup_logger

logger = setup_logger('ErrorLogger')


class ErrorLogger:
    """
    Sistema centralizado para logging estruturado de erros do sistema de produção.
    Integra com a estrutura existente de logs e permite expansão para novos tipos de erro.
    """
    
    def __init__(self, base_dir: str = "logs/erros"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def log_structured_error(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_atividade: str,
        tipo_erro: str,
        erro_detalhes: Dict[str, Any],
        nivel_impacto: str = "ALTO",
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Registra erro estruturado com contexto completo.
        
        Args:
            id_ordem: ID da ordem de produção
            id_pedido: ID do pedido
            id_atividade: ID da atividade que falhou
            nome_atividade: Nome descritivo da atividade
            tipo_erro: Tipo/categoria do erro
            erro_detalhes: Detalhes específicos do erro
            nivel_impacto: CRÍTICO, ALTO, MÉDIO, BAIXO
            contexto_adicional: Informações extras opcionais
            
        Returns:
            Caminho do arquivo de log criado
        """
        timestamp = datetime.now()
        
        erro_data = {
            "timestamp": timestamp.isoformat(),
            "identificacao": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_atividade": id_atividade,
                "nome_atividade": nome_atividade
            },
            "erro": {
                "tipo": tipo_erro,
                "detalhes": erro_detalhes,
                "nivel_impacto": nivel_impacto
            },
            "contexto": contexto_adicional or {},
            "sistema": {
                "versao_log": "2.0",
                "gerado_por": "ErrorLogger"
            }
        }
        
        # Salvar em arquivo JSON estruturado
        arquivo_json = self._salvar_erro_json(erro_data, tipo_erro)
        
        # Manter compatibilidade com sistema existente (arquivo .log)
        self._salvar_erro_compatibilidade(erro_data)
        
        # Log no console
        logger.error(
            f"🚨 [{tipo_erro}] Atividade {id_atividade} ({nome_atividade}) "
            f"falhou no pedido {id_pedido}. Detalhes salvos em: {arquivo_json}"
        )
        
        return str(arquivo_json)
        
    def _salvar_erro_json(self, erro_data: Dict[str, Any], tipo_erro: str) -> Path:
        """Salva erro em formato JSON estruturado."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # Nome do arquivo: tipo_ordem_pedido_atividade_timestamp.json
        filename = (
            f"{tipo_erro.lower()}_{erro_data['identificacao']['id_ordem']}_"
            f"{erro_data['identificacao']['id_pedido']}_"
            f"{erro_data['identificacao']['id_atividade']}_{timestamp_str}.json"
        )
        
        filepath = self.base_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(erro_data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"💾 Erro estruturado salvo: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Falha ao salvar erro estruturado: {e}")
            
        return filepath
        
    def _salvar_erro_compatibilidade(self, erro_data: Dict[str, Any]):
        """Mantém compatibilidade com sistema de logs existente."""
        try:
            from utils.logs.gerenciador_logs import salvar_erro_em_log
            
            # Criar exceção sintética para compatibilidade
            class ErroEstruturado(Exception):
                def __init__(self, erro_data):
                    self.erro_data = erro_data
                    msg = f"{erro_data['erro']['tipo']}: {erro_data['erro']['detalhes']}"
                    super().__init__(msg)
            
            id_ordem = erro_data['identificacao']['id_ordem']
            id_pedido = erro_data['identificacao']['id_pedido']
            
            salvar_erro_em_log(id_ordem, id_pedido, ErroEstruturado(erro_data))
            
        except Exception as e:
            logger.warning(f"⚠️ Falha ao manter compatibilidade com logs existentes: {e}")
    
    def listar_erros_por_pedido(self, id_ordem: int, id_pedido: int) -> List[Dict[str, Any]]:
        """Lista todos os erros estruturados de um pedido específico."""
        erros = []
        pattern = f"*_{id_ordem}_{id_pedido}_*.json"
        
        for arquivo in self.base_dir.glob(pattern):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    erro_data = json.load(f)
                    erros.append({
                        "arquivo": arquivo.name,
                        "dados": erro_data
                    })
            except Exception as e:
                logger.error(f"⚠️ Erro ao ler arquivo {arquivo}: {e}")
                
        return sorted(erros, key=lambda x: x["dados"]["timestamp"])
    
    def listar_erros_por_tipo(self, tipo_erro: str, dias_recentes: int = 7) -> List[Dict[str, Any]]:
        """Lista erros de um tipo específico nos últimos N dias."""
        from datetime import timedelta
        
        data_limite = datetime.now() - timedelta(days=dias_recentes)
        erros = []
        pattern = f"{tipo_erro.lower()}_*.json"
        
        for arquivo in self.base_dir.glob(pattern):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    erro_data = json.load(f)
                    
                timestamp_erro = datetime.fromisoformat(erro_data["timestamp"])
                if timestamp_erro >= data_limite:
                    erros.append({
                        "arquivo": arquivo.name,
                        "dados": erro_data
                    })
                    
            except Exception as e:
                logger.error(f"⚠️ Erro ao processar arquivo {arquivo}: {e}")
                
        return sorted(erros, key=lambda x: x["dados"]["timestamp"], reverse=True)
    
    def gerar_relatorio_consolidado(self, periodo_dias: int = 7) -> Dict[str, Any]:
        """Gera relatório consolidado de todos os erros no período."""
        from datetime import timedelta
        
        data_limite = datetime.now() - timedelta(days=periodo_dias)
        erros_periodo = []
        
        for arquivo in self.base_dir.glob("*.json"):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    erro_data = json.load(f)
                    
                timestamp_erro = datetime.fromisoformat(erro_data["timestamp"])
                if timestamp_erro >= data_limite:
                    erros_periodo.append(erro_data)
                    
            except Exception as e:
                logger.error(f"⚠️ Erro ao processar arquivo {arquivo}: {e}")
                
        # Consolidar estatísticas
        estatisticas = self._calcular_estatisticas(erros_periodo)
        
        relatorio = {
            "periodo_analisado": f"Últimos {periodo_dias} dias",
            "data_geracao": datetime.now().isoformat(),
            "total_erros": len(erros_periodo),
            "estatisticas": estatisticas,
            "erros_criticos": [
                erro for erro in erros_periodo 
                if erro.get("erro", {}).get("nivel_impacto") == "CRÍTICO"
            ]
        }
        
        # Salvar relatório
        self._salvar_relatorio(relatorio)
        
        return relatorio
    
    def _calcular_estatisticas(self, erros: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estatísticas dos erros."""
        tipos_erro = {}
        erros_por_pedido = {}
        nivel_impacto = {"CRÍTICO": 0, "ALTO": 0, "MÉDIO": 0, "BAIXO": 0}
        atividades_mais_problematicas = {}
        
        for erro in erros:
            # Contar por tipo
            tipo = erro.get("erro", {}).get("tipo", "DESCONHECIDO")
            tipos_erro[tipo] = tipos_erro.get(tipo, 0) + 1
            
            # Contar por pedido
            id_ordem = erro.get("identificacao", {}).get("id_ordem", "N/A")
            id_pedido = erro.get("identificacao", {}).get("id_pedido", "N/A")
            pedido_key = f"{id_ordem}_{id_pedido}"
            erros_por_pedido[pedido_key] = erros_por_pedido.get(pedido_key, 0) + 1
            
            # Contar por nível de impacto
            nivel = erro.get("erro", {}).get("nivel_impacto", "MÉDIO")
            if nivel in nivel_impacto:
                nivel_impacto[nivel] += 1
                
            # Atividades mais problemáticas
            atividade = erro.get("identificacao", {}).get("nome_atividade", "Desconhecida")
            atividades_mais_problematicas[atividade] = atividades_mais_problematicas.get(atividade, 0) + 1
        
        return {
            "tipos_erro": tipos_erro,
            "erros_por_pedido": erros_por_pedido,
            "nivel_impacto": nivel_impacto,
            "atividades_mais_problematicas": dict(
                sorted(atividades_mais_problematicas.items(), key=lambda x: x[1], reverse=True)[:10]
            )
        }
    
    def _salvar_relatorio(self, relatorio: Dict[str, Any]):
        """Salva relatório consolidado."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relatorio_filename = f"relatorio_consolidado_{timestamp}.json"
        relatorio_path = self.base_dir / relatorio_filename
        
        try:
            with open(relatorio_path, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            logger.info(f"📊 Relatório consolidado salvo: {relatorio_path}")
        except Exception as e:
            logger.error(f"❌ Falha ao salvar relatório: {e}")


# Instância global para uso em todo o sistema
error_logger = ErrorLogger()


# Funções de conveniência para diferentes tipos de erro
def log_capacity_error(id_ordem: int, id_pedido: int, id_atividade: int, nome_atividade: str,
                      tipo_equipamento: str, quantidade_solicitada: float, 
                      capacidade_minima: float, capacidade_maxima: float,
                      equipamentos_disponiveis: List[Dict], motivo: str,
                      contexto_adicional: Optional[Dict] = None):
    """Registra erro específico de capacidade de equipamento."""
    
    erro_detalhes = {
        "tipo_equipamento": tipo_equipamento,
        "quantidade_solicitada": quantidade_solicitada,
        "capacidade_minima": capacidade_minima,
        "capacidade_maxima": capacidade_maxima,
        "equipamentos_disponiveis": equipamentos_disponiveis,
        "motivo": motivo,
        "sugestoes": [
            "Aumentar a quantidade do pedido para atingir o mínimo",
            "Verificar se há equipamentos com capacidade menor disponíveis",
            "Considerar produção em lotes maiores",
            "Revisar configuração de capacidades mínimas dos equipamentos"
        ]
    }
    
    return error_logger.log_structured_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        id_atividade=id_atividade,
        nome_atividade=nome_atividade,
        tipo_erro="CAPACIDADE_EQUIPAMENTO_INSUFICIENTE",
        erro_detalhes=erro_detalhes,
        nivel_impacto="CRÍTICO",
        contexto_adicional=contexto_adicional
    )


def log_dependency_error(id_ordem: int, id_pedido: int, id_atividade: int, nome_atividade: str,
                        tipo_item: str, atividades_executadas: List, motivo_falha: str,
                        contexto_adicional: Optional[Dict] = None):
    """Registra erro de dependência crítica entre atividades."""
    
    erro_detalhes = {
        "tipo_item_falhado": tipo_item,
        "motivo_falha": motivo_falha,
        "atividades_ja_executadas": [
            {
                "id_atividade": ativ.id_atividade,
                "nome": ativ.nome_atividade,
                "tipo_item": ativ.tipo_item.name,
                "inicio_real": ativ.inicio_real.isoformat() if hasattr(ativ, 'inicio_real') and ativ.inicio_real else None,
                "fim_real": ativ.fim_real.isoformat() if hasattr(ativ, 'fim_real') and ativ.fim_real else None
            }
            for ativ in atividades_executadas
        ],
        "total_atividades_perdidas": len(atividades_executadas),
        "impacto_estimado": "Estado inconsistente - produto parcialmente executado sem dependência essencial"
    }
    
    return error_logger.log_structured_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        id_atividade=id_atividade,
        nome_atividade=nome_atividade,
        tipo_erro="FALHA_DEPENDENCIA_CRITICA",
        erro_detalhes=erro_detalhes,
        nivel_impacto="CRÍTICO",
        contexto_adicional=contexto_adicional
    )


def log_temporal_scheduling_error(id_ordem: int, id_pedido: int, id_atividade: int, nome_atividade: str,
                                 duracao: str, janela_disponivel: str, tentativas_realizadas: int,
                                 contexto_adicional: Optional[Dict] = None):
    """Registra erro de impossibilidade de agendamento temporal."""
    
    erro_detalhes = {
        "duracao_necessaria": duracao,
        "janela_disponivel": janela_disponivel,
        "tentativas_realizadas": tentativas_realizadas,
        "motivo": "Conflitos temporais com outras atividades ou restrições de horário",
        "sugestoes": [
            "Aumentar a janela temporal disponível",
            "Verificar conflitos com outras atividades",
            "Revisar restrições de tempo_maximo_de_espera",
            "Considerar flexibilização de horários obrigatórios"
        ]
    }
    
    return error_logger.log_structured_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        id_atividade=id_atividade,
        nome_atividade=nome_atividade,
        tipo_erro="CONFLITO_TEMPORAL_AGENDAMENTO",
        erro_detalhes=erro_detalhes,
        nivel_impacto="ALTO",
        contexto_adicional=contexto_adicional
    )


def log_generic_error(id_ordem: int, id_pedido: int, id_atividade: int, nome_atividade: str,
                     tipo_erro: str, descricao: str, detalhes: Dict[str, Any],
                     nivel_impacto: str = "MÉDIO", contexto_adicional: Optional[Dict] = None):
    """Registra erro genérico do sistema."""
    
    return error_logger.log_structured_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        id_atividade=id_atividade,
        nome_atividade=nome_atividade,
        tipo_erro=tipo_erro,
        erro_detalhes=detalhes,
        nivel_impacto=nivel_impacto,
        contexto_adicional=contexto_adicional
    )