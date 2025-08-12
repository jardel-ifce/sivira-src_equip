# ========================================
# ARQUIVO: utils/logs/timing_exceptions.py
# ========================================
"""
Exceções específicas para problemas de tempo entre atividades.
Sistema de logging para erros de sequenciamento temporal.
"""

from typing import List, Optional
from datetime import datetime, timedelta


class TimingError(Exception):
    """
    Classe base para erros relacionados a sequenciamento temporal de atividades.
    """
    
    def __init__(self, message: str, error_type: str, details: dict, suggestions: list = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details
        self.suggestions = suggestions or []
        
    def to_dict(self) -> dict:
        """Converte a exceção em dicionário para logging."""
        return {
            "message": str(self),
            "error_type": self.error_type,
            "details": self.details,
            "suggestions": self.suggestions
        }


class IntraActivityTimingError(TimingError):
    """
    Exceção para problemas de tempo entre equipamentos DENTRO da mesma atividade.
    """
    
    def __init__(self, activity_id: int, activity_name: str,
                 current_equipment: str, successor_equipment: str,
                 current_end_time: datetime, successor_start_time: datetime,
                 maximum_wait_time: timedelta, actual_delay: timedelta):
        
        details = {
            "activity": {
                "id": activity_id,
                "name": activity_name
            },
            "current_equipment": {
                "name": current_equipment,
                "end_time": current_end_time.isoformat(),
                "end_time_formatted": current_end_time.strftime('%d/%m %H:%M:%S')
            },
            "successor_equipment": {
                "name": successor_equipment,
                "start_time": successor_start_time.isoformat(),
                "start_time_formatted": successor_start_time.strftime('%d/%m %H:%M:%S')
            },
            "timing_violation": {
                "maximum_wait_time_seconds": maximum_wait_time.total_seconds(),
                "maximum_wait_time_formatted": str(maximum_wait_time),
                "actual_delay_seconds": actual_delay.total_seconds(),
                "actual_delay_formatted": str(actual_delay),
                "excess_time_seconds": (actual_delay - maximum_wait_time).total_seconds(),
                "excess_time_formatted": str(actual_delay - maximum_wait_time)
            },
            "context": "INTRA_ATIVIDADE"
        }
        
        suggestions = [
            "Verificar disponibilidade dos equipamentos para execução mais próxima",
            "Considerar equipamentos alternativos com menor tempo de espera",
            "Revisar sequenciamento interno da atividade",
            "Verificar se há conflitos de ocupação dos equipamentos"
        ]
        
        if maximum_wait_time == timedelta(0):
            suggestions.insert(0, "CRÍTICO: Equipamentos devem trabalhar consecutivamente (tempo máximo = 0)")
            suggestions.insert(1, "Verificar sincronização entre equipamentos da mesma linha")
        
        message = (
            f"Tempo máximo de espera excedido DENTRO da atividade {activity_id} ({activity_name}): "
            f"Equipamento '{current_equipment}' termina às {current_end_time.strftime('%d/%m %H:%M:%S')}, "
            f"mas '{successor_equipment}' só pode iniciar às {successor_start_time.strftime('%d/%m %H:%M:%S')}. "
            f"Atraso de {actual_delay} excede máximo permitido de {maximum_wait_time} "
            f"em {actual_delay - maximum_wait_time}."
        )
        
        super().__init__(
            message=message,
            error_type="TEMPO_MAXIMO_ESPERA_INTRA_ATIVIDADE",
            details=details,
            suggestions=suggestions
        )


class InterActivityTimingError(TimingError):
    """
    Exceção para problemas de tempo ENTRE atividades diferentes.
    """
    
    def __init__(self, current_activity_id: int, current_activity_name: str,
                 successor_activity_id: int, successor_activity_name: str,
                 current_end_time: datetime, successor_start_time: datetime,
                 maximum_wait_time: timedelta, actual_delay: timedelta):
        
        details = {
            "current_activity": {
                "id": current_activity_id,
                "name": current_activity_name,
                "end_time": current_end_time.isoformat(),
                "end_time_formatted": current_end_time.strftime('%d/%m %H:%M:%S')
            },
            "successor_activity": {
                "id": successor_activity_id,
                "name": successor_activity_name,
                "start_time": successor_start_time.isoformat(),
                "start_time_formatted": successor_start_time.strftime('%d/%m %H:%M:%S')
            },
            "timing_violation": {
                "maximum_wait_time_seconds": maximum_wait_time.total_seconds(),
                "maximum_wait_time_formatted": str(maximum_wait_time),
                "actual_delay_seconds": actual_delay.total_seconds(),
                "actual_delay_formatted": str(actual_delay),
                "excess_time_seconds": (actual_delay - maximum_wait_time).total_seconds(),
                "excess_time_formatted": str(actual_delay - maximum_wait_time)
            },
            "context": "INTER_ATIVIDADE"
        }
        
        suggestions = [
            "Verificar se há conflitos de equipamentos que impedem execução mais próxima",
            "Considerar ajustar o tempo máximo de espera permitido",
            "Revisar o sequenciamento das atividades",
            "Verificar disponibilidade de recursos alternativos"
        ]
        
        if maximum_wait_time == timedelta(0):
            suggestions.insert(0, "ATENÇÃO: Tempo máximo de espera = 0 - atividades devem ser executadas consecutivamente")
            suggestions.insert(1, "Verificar se há equipamentos disponíveis para execução imediata")
        
        excess_hours = (actual_delay - maximum_wait_time).total_seconds() / 3600
        if excess_hours > 24:
            suggestions.append("CRÍTICO: Excesso superior a 24 horas - revisar planejamento completo")
        
        message = (
            f"Tempo máximo de espera excedido ENTRE atividades: "
            f"Atividade {current_activity_id} ({current_activity_name}) termina às "
            f"{current_end_time.strftime('%d/%m %H:%M:%S')}, mas atividade sucessora "
            f"{successor_activity_id} ({successor_activity_name}) só pode iniciar às "
            f"{successor_start_time.strftime('%d/%m %H:%M:%S')}. "
            f"Atraso de {actual_delay} excede máximo permitido de {maximum_wait_time} "
            f"em {actual_delay - maximum_wait_time}."
        )
        
        super().__init__(
            message=message,
            error_type="TEMPO_MAXIMO_ESPERA_INTER_ATIVIDADE",
            details=details,
            suggestions=suggestions
        )


# Manter compatibilidade com código existente
MaximumWaitTimeExceededError = InterActivityTimingError


class SequencingConflictError(TimingError):
    """
    Exceção para conflitos de sequenciamento temporal entre atividades.
    """
    
    def __init__(self, activity_sequence: list, conflict_details: dict):
        
        details = {
            "activity_sequence": activity_sequence,
            "conflict_details": conflict_details,
            "total_activities_affected": len(activity_sequence)
        }
        
        suggestions = [
            "Revisar ordem de execução das atividades",
            "Verificar disponibilidade de equipamentos alternativos",
            "Considerar execução em paralelo quando possível",
            "Ajustar janela temporal do pedido"
        ]
        
        message = (
            f"Conflito de sequenciamento detectado envolvendo {len(activity_sequence)} atividades. "
            f"Não é possível executar a sequência dentro das restrições temporais definidas."
        )
        
        super().__init__(
            message=message,
            error_type="CONFLITO_SEQUENCIAMENTO",
            details=details,
            suggestions=suggestions
        )


class TemporalWindowViolationError(TimingError):
    """
    Exceção para violação da janela temporal permitida para execução.
    """
    
    def __init__(self, activity_id: int, activity_name: str, 
                 required_start: datetime, required_end: datetime,
                 available_start: datetime, available_end: datetime):
        
        details = {
            "activity": {
                "id": activity_id,
                "name": activity_name
            },
            "required_window": {
                "start": required_start.isoformat(),
                "end": required_end.isoformat(),
                "start_formatted": required_start.strftime('%d/%m %H:%M'),
                "end_formatted": required_end.strftime('%d/%m %H:%M'),
                "duration_hours": (required_end - required_start).total_seconds() / 3600
            },
            "available_window": {
                "start": available_start.isoformat(),
                "end": available_end.isoformat(),
                "start_formatted": available_start.strftime('%d/%m %H:%M'),
                "end_formatted": available_end.strftime('%d/%m %H:%M'),
                "duration_hours": (available_end - available_start).total_seconds() / 3600
            }
        }
        
        suggestions = [
            "Expandir janela temporal disponível para execução",
            "Verificar se há recursos adicionais disponíveis",
            "Considerar replanejamento da atividade",
            "Revisar dependências que restringem a janela temporal"
        ]
        
        message = (
            f"Janela temporal violada para atividade {activity_id} ({activity_name}). "
            f"Requer execução entre {required_start.strftime('%d/%m %H:%M')} e "
            f"{required_end.strftime('%d/%m %H:%M')}, mas só está disponível entre "
            f"{available_start.strftime('%d/%m %H:%M')} e {available_end.strftime('%d/%m %H:%M')}."
        )
        
        super().__init__(
            message=message,
            error_type="VIOLACAO_JANELA_TEMPORAL",
            details=details,
            suggestions=suggestions
        )