# ========================================
# ARQUIVO: utils/logs/quantity_exceptions.py
# ========================================
"""
Exceções específicas para problemas de quantidade de equipamentos.
Implementação inicial focada apenas em capacidades.
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta


class QuantityError(Exception):
    """
    Classe base para erros relacionados a quantidades de equipamento.
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


class QuantityBelowMinimumError(QuantityError):
    """
    Exceção para quantidade abaixo da capacidade mínima do equipamento.
    """
    
    def __init__(self, equipment_type: str, requested_quantity: float, 
                 minimum_capacity: float, available_equipment: list):
        
        details = {
            "equipment_type": equipment_type,
            "requested_quantity": requested_quantity,
            "minimum_capacity": minimum_capacity,
            "available_equipment": available_equipment,
            "deficit": minimum_capacity - requested_quantity
        }
        
        suggestions = [
            f"Aumentar a quantidade para pelo menos {minimum_capacity}g",
            "Verificar se há equipamentos com capacidade menor disponíveis",
            "Considerar produção em lotes maiores"
        ]
        
        message = (
            f"Quantidade {requested_quantity}g está abaixo da capacidade mínima "
            f"({minimum_capacity}g) para equipamentos do tipo {equipment_type}"
        )
        
        super().__init__(
            message=message,
            error_type="QUANTIDADE_ABAIXO_MINIMO",
            details=details,
            suggestions=suggestions
        )


class QuantityExceedsMaximumError(QuantityError):
    """
    Exceção para quantidade acima da capacidade máxima total do sistema.
    """
    
    def __init__(self, equipment_type: str, requested_quantity: float, 
                 total_system_capacity: float, individual_capacities: list):
        
        details = {
            "equipment_type": equipment_type,
            "requested_quantity": requested_quantity,
            "total_system_capacity": total_system_capacity,
            "individual_capacities": individual_capacities,
            "excess": requested_quantity - total_system_capacity
        }
        
        suggestions = [
            f"Reduzir a quantidade para no máximo {total_system_capacity}g",
            "Dividir o pedido em lotes menores",
            "Produzir em etapas separadas"
        ]
        
        message = (
            f"Quantidade {requested_quantity}g excede a capacidade máxima total "
            f"({total_system_capacity}g) do sistema de {equipment_type}"
        )
        
        super().__init__(
            message=message,
            error_type="QUANTIDADE_EXCEDE_MAXIMO",
            details=details,
            suggestions=suggestions
        )