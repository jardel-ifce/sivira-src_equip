# utils/logs/timing_logger.py
"""
Sistema de logs específico para erros de tempo/sequenciamento.
Integra com o sistema de logs existente.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from utils.logs.logger_factory import setup_logger

logger = setup_logger('TimingLogger')


class TimingLogger:
    """
    Logger especializado para erros de tempo e sequenciamento.
    Integra com o sistema de logs existente.
    """
    
    def __init__(self, base_dir: str = "logs/erros"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def log_intra_activity_timing_error(self, id_ordem: int, id_pedido: int, 
                                        activity_id: int, activity_name: str,
                                        current_equipment: str, successor_equipment: str,
                                        timing_error):
        """
        Registra erro de tempo DENTRO de uma atividade (entre equipamentos sequenciais).
        
        Args:
            id_ordem: ID da ordem de produção
            id_pedido: ID do pedido
            activity_id: ID da atividade onde ocorreu o erro
            activity_name: Nome da atividade
            current_equipment: Nome do equipamento atual
            successor_equipment: Nome do equipamento sucessor
            timing_error: Instância de IntraActivityTimingError
            
        Returns:
            Caminho do arquivo de log criado
        """
        timestamp = datetime.now()
        
        error_data = {
            "timestamp": timestamp.isoformat(),
            "identificacao": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "atividade": {
                    "id": activity_id,
                    "nome": activity_name
                },
                "equipamento_atual": current_equipment,
                "equipamento_sucessor": successor_equipment
            },
            "erro_tempo": timing_error.to_dict(),
            "sistema": {
                "tipo_validacao": "SEQUENCIAMENTO_INTRA_ATIVIDADE",
                "backward_scheduling_executado": True,
                "impacto_estimado": "Atividade pode falhar ou necessitar replanejamento"
            }
        }
        
        # Salvar em arquivo JSON estruturado
        arquivo_json = self._salvar_erro_json(error_data, timing_error.error_type)
        
        # Manter compatibilidade com sistema existente
        self._salvar_erro_compatibilidade(error_data)
        
        logger.error(
            f"🔧 ERRO DE TEMPO INTRA-ATIVIDADE: {timing_error.error_type} - "
            f"Atividade {activity_id} ({activity_name}): {current_equipment} → {successor_equipment} "
            f"no pedido {id_pedido}. Log salvo: {arquivo_json.name}"
        )
        
        return str(arquivo_json)

    def log_inter_activity_timing_error(self, id_ordem: int, id_pedido: int, 
                                       current_activity_id: int, current_activity_name: str,
                                       successor_activity_id: int, successor_activity_name: str,
                                       timing_error):
        """
        Registra erro de tempo ENTRE atividades diferentes.
        
        Args:
            id_ordem: ID da ordem de produção
            id_pedido: ID do pedido
            current_activity_id: ID da atividade atual
            current_activity_name: Nome da atividade atual
            successor_activity_id: ID da atividade sucessora
            successor_activity_name: Nome da atividade sucessora
            timing_error: Instância de InterActivityTimingError
            
        Returns:
            Caminho do arquivo de log criado
        """
        timestamp = datetime.now()
        
        error_data = {
            "timestamp": timestamp.isoformat(),
            "identificacao": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "atividade_atual": {
                    "id": current_activity_id,
                    "nome": current_activity_name
                },
                "atividade_sucessora": {
                    "id": successor_activity_id,
                    "nome": successor_activity_name
                }
            },
            "erro_tempo": timing_error.to_dict(),
            "sistema": {
                "tipo_validacao": "SEQUENCIAMENTO_INTER_ATIVIDADE",
                "backward_scheduling_executado": True,
                "impacto_estimado": "Pedido pode ser cancelado ou replanejado"
            }
        }
        
        # Salvar em arquivo JSON estruturado
        arquivo_json = self._salvar_erro_json(error_data, timing_error.error_type)
        
        # Manter compatibilidade com sistema existente
        self._salvar_erro_compatibilidade(error_data)
        
        logger.error(
            f"🔄 ERRO DE TEMPO INTER-ATIVIDADE: {timing_error.error_type} - "
            f"Entre atividades {current_activity_id} ({current_activity_name}) → "
            f"{successor_activity_id} ({successor_activity_name}) no pedido {id_pedido}. "
            f"Log salvo: {arquivo_json.name}"
        )
        
        return str(arquivo_json)
        
    def log_sequencing_error(self, id_ordem: int, id_pedido: int, 
                           atividades_afetadas: list, timing_error):
        """
        Registra erro de sequenciamento geral envolvendo múltiplas atividades.
        """
        timestamp = datetime.now()
        
        error_data = {
            "timestamp": timestamp.isoformat(),
            "identificacao": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "atividades_afetadas": atividades_afetadas,
                "total_atividades": len(atividades_afetadas)
            },
            "erro_tempo": timing_error.to_dict(),
            "sistema": {
                "tipo_validacao": "SEQUENCIAMENTO_MULTIPLO",
                "backward_scheduling_executado": True,
                "impacto_estimado": "Replanejamento completo necessário"
            }
        }
        
        # Salvar em arquivo JSON estruturado
        arquivo_json = self._salvar_erro_json(error_data, timing_error.error_type)
        
        # Manter compatibilidade com sistema existente
        self._salvar_erro_compatibilidade(error_data)
        
        logger.error(
            f"🔄 ERRO DE SEQUENCIAMENTO: {timing_error.error_type} - "
            f"Afetando {len(atividades_afetadas)} atividades no pedido {id_pedido}. "
            f"Log salvo: {arquivo_json.name}"
        )
        
        return str(arquivo_json)
        
    def _salvar_erro_json(self, error_data: dict, error_type: str) -> Path:
        """Salva erro em formato JSON estruturado."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # Nome do arquivo: timing_tipo_ordem_pedido_timestamp.json
        filename = (
            f"timing_{error_type.lower()}_{error_data['identificacao']['id_ordem']}_"
            f"{error_data['identificacao']['id_pedido']}_{timestamp_str}.json"
        )
        
        filepath = self.base_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"💾 Erro de tempo salvo: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Falha ao salvar erro de tempo: {e}")
            
        return filepath
        
    def _salvar_erro_compatibilidade(self, error_data: dict):
        """Mantém compatibilidade com gerenciador_logs.py existente."""
        try:
            from utils.logs.gerenciador_logs import salvar_erro_em_log
            
            # Criar exceção sintética para compatibilidade
            class ErroTempo(Exception):
                def __init__(self, error_data):
                    self.error_data = error_data
                    erro_tempo = error_data.get('erro_tempo', {})
                    msg = f"ERRO DE TEMPO: {erro_tempo.get('error_type', 'DESCONHECIDO')} - {erro_tempo.get('message', '')}"
                    super().__init__(msg)
            
            id_ordem = error_data['identificacao']['id_ordem']
            id_pedido = error_data['identificacao']['id_pedido']
            
            salvar_erro_em_log(id_ordem, id_pedido, ErroTempo(error_data))
            
        except Exception as e:
            logger.warning(f"⚠️ Falha ao manter compatibilidade com logs existentes: {e}")
    
    def listar_erros_tempo_por_pedido(self, id_ordem: int, id_pedido: int) -> list:
        """Lista todos os erros de tempo de um pedido específico."""
        erros = []
        pattern = f"timing_*_{id_ordem}_{id_pedido}_*.json"
        
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
    
    def gerar_relatorio_tempo(self, periodo_dias: int = 7) -> dict:
        """Gera relatório específico de erros de tempo."""
        from datetime import timedelta as td
        
        data_limite = datetime.now() - td(days=periodo_dias)
        erros_tempo = []
        
        for arquivo in self.base_dir.glob("timing_*.json"):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    erro_data = json.load(f)
                    
                timestamp_erro = datetime.fromisoformat(erro_data["timestamp"])
                if timestamp_erro >= data_limite:
                    erros_tempo.append(erro_data)
                    
            except Exception as e:
                logger.error(f"⚠️ Erro ao processar arquivo {arquivo}: {e}")
        
        # Estatísticas específicas de tempo
        tipos_erro_tempo = {}
        pedidos_afetados = set()
        tempo_excesso_total = 0
        atividades_com_problemas = set()
        
        for erro in erros_tempo:
            erro_temp = erro.get('erro_tempo', {})
            tipo = erro_temp.get('error_type', 'DESCONHECIDO')
            detalhes = erro_temp.get('details', {})
            
            # Contar por tipo
            tipos_erro_tempo[tipo] = tipos_erro_tempo.get(tipo, 0) + 1
            
            # Contar pedidos únicos afetados
            id_ordem = erro.get('identificacao', {}).get('id_ordem')
            id_pedido = erro.get('identificacao', {}).get('id_pedido')
            if id_ordem and id_pedido:
                pedidos_afetados.add(f"{id_ordem}_{id_pedido}")
            
            # Calcular excesso de tempo total
            timing_violation = detalhes.get('timing_violation', {})
            if 'excess_time_seconds' in timing_violation:
                tempo_excesso_total += timing_violation['excess_time_seconds']
            
            # Contar atividades com problemas
            ativ_atual = erro.get('identificacao', {}).get('atividade_atual', {})
            ativ_sucess = erro.get('identificacao', {}).get('atividade_sucessora', {})
            if ativ_atual.get('id'):
                atividades_com_problemas.add(ativ_atual['id'])
            if ativ_sucess.get('id'):
                atividades_com_problemas.add(ativ_sucess['id'])
        
        relatorio = {
            "periodo_analisado": f"Últimos {periodo_dias} dias",
            "data_geracao": datetime.now().isoformat(),
            "total_erros_tempo": len(erros_tempo),
            "pedidos_afetados": len(pedidos_afetados),
            "atividades_com_problemas": len(atividades_com_problemas),
            "estatisticas": {
                "tipos_erro_tempo": tipos_erro_tempo,
                "tempo_excesso_total_horas": round(tempo_excesso_total / 3600, 2),
                "tempo_excesso_medio_minutos": round((tempo_excesso_total / len(erros_tempo) / 60), 2) if erros_tempo else 0,
                "impacto_estimado": f"{len(pedidos_afetados)} pedidos requerem replanejamento"
            },
            "erros_detalhados": erros_tempo
        }
        
        # Salvar relatório
        self._salvar_relatorio_tempo(relatorio)
        
        return relatorio
    
    def _salvar_relatorio_tempo(self, relatorio: dict):
        """Salva relatório de tempo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relatorio_filename = f"relatorio_tempo_{timestamp}.json"
        relatorio_path = self.base_dir / relatorio_filename
        
        try:
            with open(relatorio_path, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            logger.info(f"📊 Relatório de tempo salvo: {relatorio_path}")
        except Exception as e:
            logger.error(f"❌ Falha ao salvar relatório de tempo: {e}")


# Instância global para uso em todo o sistema
timing_logger = TimingLogger()


# Funções de conveniência para uso direto
def log_intra_activity_timing_error(id_ordem: int, id_pedido: int,
                                   activity_id: int, activity_name: str,
                                   current_equipment: str, successor_equipment: str,
                                   current_end_time: datetime, successor_start_time: datetime,
                                   maximum_wait_time: timedelta):
    """Função de conveniência para log de erro de tempo DENTRO de atividade."""
    from utils.logs.timing_exceptions import IntraActivityTimingError
    
    actual_delay = successor_start_time - current_end_time
    
    error = IntraActivityTimingError(
        activity_id=activity_id,
        activity_name=activity_name,
        current_equipment=current_equipment,
        successor_equipment=successor_equipment,
        current_end_time=current_end_time,
        successor_start_time=successor_start_time,
        maximum_wait_time=maximum_wait_time,
        actual_delay=actual_delay
    )
    
    return timing_logger.log_intra_activity_timing_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        activity_id=activity_id,
        activity_name=activity_name,
        current_equipment=current_equipment,
        successor_equipment=successor_equipment,
        timing_error=error
    )


def log_inter_activity_timing_error(id_ordem: int, id_pedido: int,
                                   current_activity_id: int, current_activity_name: str,
                                   successor_activity_id: int, successor_activity_name: str,
                                   current_end_time: datetime, successor_start_time: datetime,
                                   maximum_wait_time: timedelta):
    """Função de conveniência para log de erro de tempo ENTRE atividades."""
    from utils.logs.timing_exceptions import InterActivityTimingError
    
    actual_delay = successor_start_time - current_end_time
    
    error = InterActivityTimingError(
        current_activity_id=current_activity_id,
        current_activity_name=current_activity_name,
        successor_activity_id=successor_activity_id,
        successor_activity_name=successor_activity_name,
        current_end_time=current_end_time,
        successor_start_time=successor_start_time,
        maximum_wait_time=maximum_wait_time,
        actual_delay=actual_delay
    )
    
    return timing_logger.log_inter_activity_timing_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        current_activity_id=current_activity_id,
        current_activity_name=current_activity_name,
        successor_activity_id=successor_activity_id,
        successor_activity_name=successor_activity_name,
        timing_error=error
    )


# Manter compatibilidade com código existente
def log_maximum_wait_time_exceeded(id_ordem: int, id_pedido: int,
                                  current_activity_id: int, current_activity_name: str,
                                  successor_activity_id: int, successor_activity_name: str,
                                  current_end_time: datetime, successor_start_time: datetime,
                                  maximum_wait_time: timedelta):
    """Função de conveniência para compatibilidade - redireciona para inter_activity."""
    return log_inter_activity_timing_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        current_activity_id=current_activity_id,
        current_activity_name=current_activity_name,
        successor_activity_id=successor_activity_id,
        successor_activity_name=successor_activity_name,
        current_end_time=current_end_time,
        successor_start_time=successor_start_time,
        maximum_wait_time=maximum_wait_time
    )


def log_sequencing_conflict(id_ordem: int, id_pedido: int, 
                          atividades_afetadas: list, conflict_details: dict):
    """Função de conveniência para log de conflito de sequenciamento."""
    from utils.logs.timing_exceptions import SequencingConflictError
    
    error = SequencingConflictError(
        activity_sequence=atividades_afetadas,
        conflict_details=conflict_details
    )
    
    return timing_logger.log_sequencing_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        atividades_afetadas=atividades_afetadas,
        timing_error=error
    )