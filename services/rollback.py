import os
from typing import List, Any, Optional, Union, Tuple
from models.funcionarios.funcionario import Funcionario
from utils.logger_factory import setup_logger
from utils.gerenciador_logs import remover_logs_pedido

logger = setup_logger("Rollback")


def rollback_pedido(ordem_id: int, pedido_id: int, atividades_modulares: List[Any], funcionarios: List[Funcionario]):
    """
    🔄 Executa rollback completo do pedido: libera equipamentos, funcionários e remove logs.
    """
    for atividade in atividades_modulares:
        if not atividade.alocada:
            continue

        rollback_equipamentos(equipamentos_alocados=atividade.equipamentos_selecionados, ordem_id=ordem_id, pedido_id=pedido_id, atividade_id=atividade.id)

    rollback_funcionarios(funcionarios_alocados=funcionarios, ordem_id=ordem_id, pedido_id=pedido_id, atividade_id=atividade.id)
    remover_logs_pedido(pedido_id)


def rollback_equipamentos(
    equipamentos_alocados: List[Union[Tuple[str, object], object]],
    ordem_id: int,
    pedido_id: Optional[int] = None,
    atividade_id: Optional[int] = None,
):
    """
    🔄 Libera todos os equipamentos alocados para uma ordem, pedido ou atividade.

    - Se apenas ordem_id for fornecido, libera por ordem.
    - Se ordem_id e pedido_id forem fornecidos, libera por pedido.
    - Se ordem_id, pedido_id e atividade_id forem fornecidos, libera por atividade.
    """
    for equipamento in _extrair_objetos_equipamento(equipamentos_alocados):
        try:
            if atividade_id is not None and pedido_id is not None:
                if hasattr(equipamento, "liberar_por_atividade"):
                    equipamento.liberar_por_atividade(ordem_id=ordem_id, pedido_id=pedido_id, atividade_id=atividade_id)
            elif pedido_id is not None:
                if hasattr(equipamento, "liberar_por_pedido"):
                    equipamento.liberar_por_pedido(ordem_id=ordem_id, pedido_id=pedido_id)
            else:
                if hasattr(equipamento, "liberar_por_ordem"):
                    equipamento.liberar_por_ordem(ordem_id=ordem_id)
        except Exception as e:
            logger.warning(
                f"⚠️ Erro ao liberar {equipamento.nome} "
                f"{'da atividade ' + str(atividade_id) if atividade_id is not None else ''} "
                f"{'do pedido ' + str(pedido_id) if pedido_id is not None else ''} "
                f"da ordem {ordem_id}: {e}"
            )


def _extrair_objetos_equipamento(lista):
    """
    🧰 Aceita lista com equipamentos ou tuplas (nome, equipamento), retornando só os objetos.
    """
    return [equip[1] if isinstance(equip, tuple) else equip for equip in lista]



def rollback_funcionarios(
    funcionarios_alocados: List[Funcionario],
    ordem_id: int,
    pedido_id: Optional[int] = None,
    atividade_id: Optional[int] = None,
):
    """
     🔄 Libera todos os funcionários envolvidos na ordem, pedido ou atividade.

    - Se apenas ordem_id for fornecido, libera por ordem.
    - Se ordem_id e pedido_id forem fornecidos, libera por pedido.
    - Se ordem_id, pedido_id e atividade_id forem fornecidos, libera por atividade.
    """
    for funcionario in funcionarios_alocados:
        try:
            if atividade_id is not None and pedido_id is not None:
                funcionario.liberar_por_atividade(ordem_id=ordem_id, pedido_id=pedido_id, atividade_id=atividade_id)
            elif pedido_id is not None:
                funcionario.liberar_por_pedido(ordem_id=ordem_id, pedido_id=pedido_id)
            else:
                funcionario.liberar_por_ordem(ordem_id=ordem_id)
        except Exception as e:
            logger.warning(
                f"⚠️ Falha ao liberar {funcionario.nome} "
                f"{'da atividade ' + str(atividade_id) if atividade_id is not None else ''} "
                f"{'do pedido ' + str(pedido_id) if pedido_id is not None else ''} "
                f"da ordem {ordem_id}: {e}"
            )
def _extrair_objetos_equipamento(equipamentos_alocados):
    """
    Garante que a função funcione tanto para listas de tuplas (ex: [(id, equipamento)])
    quanto para listas diretas de equipamentos.
    """
    if equipamentos_alocados and isinstance(equipamentos_alocados[0], tuple):
        return [e[1] for e in equipamentos_alocados]
    return equipamentos_alocados
