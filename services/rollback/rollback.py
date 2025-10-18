from typing import List, Any, Optional, Union, Tuple
from models.funcionarios.funcionario import Funcionario
from utils.logs.logger_factory import setup_logger
from utils.logs.gerenciador_logs import apagar_logs_por_pedido_e_ordem
from utils.logs.logger_ocupacao_detalhada import logger_ocupacao_detalhada

logger = setup_logger("Rollback")


def rollback_pedido(id_ordem: int, id_pedido: int, atividades_modulares: List[Any], funcionarios: List[Funcionario]):
    """
    🔄 Executa rollback completo do pedido: libera equipamentos, funcionários e remove logs.

    ✅ ATUALIZADO: Agora usa apagar_logs_por_pedido_e_ordem() para remover logs de:
       - logs/equipamentos/sucesso/
       - logs/funcionarios/sucesso/
       - logs/funcionarios/erro/
    """
    logger.info(f"🔄 Iniciando rollback do pedido {id_pedido} da ordem {id_ordem}.")
    for atividade in atividades_modulares:
        rollback_equipamentos(
            equipamentos_alocados=atividade.equipamentos_selecionados,
            id_ordem=id_ordem,
            id_pedido=id_pedido,
        )

    rollback_funcionarios(
        funcionarios_alocados=funcionarios,
        id_ordem=id_ordem,
        id_pedido=id_pedido,
    )

    # ✅ Remove logs (equipamentos/sucesso + funcionarios/sucesso + funcionarios/erro)
    apagar_logs_por_pedido_e_ordem(id_ordem, id_pedido)

    # 🆕 Remove logs detalhados de equipamentos
    logger_ocupacao_detalhada.rollback_ordem_pedido(id_ordem, id_pedido)


def rollback_equipamentos(
    equipamentos_alocados: List[Union[Tuple[str, object], object]],
    id_ordem: int,
    id_pedido: Optional[int] = None,
    id_atividade: Optional[int] = None,
):
    """
    🔄 Libera todos os equipamentos alocados para uma ordem, pedido ou atividade.

    - Se apenas id_ordem for fornecido, libera por ordem.
    - Se id_ordem e id_pedido forem fornecidos, libera por pedido.
    - Se id_ordem, id_pedido e id_atividade forem fornecidos, libera por atividade.
    """
    print("🔍 DEBUG - equipamentos_alocados RECEBIDO:")
    print(repr(equipamentos_alocados))

    equipamentos_extraidos = _extrair_objetos_equipamento(equipamentos_alocados)

    print("🔍 DEBUG - EQUIPAMENTOS EXTRAÍDOS:")
    for i, equipamento in enumerate(equipamentos_extraidos):
        print(f"  [{i}] Tipo: {type(equipamento)} | Valor: {repr(equipamento)}")

    for equipamento in equipamentos_extraidos:
        try:
            equipamento_nome = getattr(equipamento, 'nome', str(equipamento))
            print(f"🔄 Liberando {equipamento_nome} ")

            if id_atividade is not None and id_pedido is not None:
                if hasattr(equipamento, "liberar_por_atividade"):
                    equipamento.liberar_por_atividade(id_ordem=id_ordem, id_pedido=id_pedido, id_atividade=id_atividade)
            elif id_pedido is not None:
                if hasattr(equipamento, "liberar_por_pedido"):
                    equipamento.liberar_por_pedido(id_ordem=id_ordem, id_pedido=id_pedido)
            else:
                if hasattr(equipamento, "liberar_por_ordem"):
                    equipamento.liberar_por_ordem(id_ordem=id_ordem)
        except Exception as e:
            equipamento_nome = getattr(equipamento, 'nome', str(equipamento))
            logger.warning(
                f"⚠️ Erro ao liberar {equipamento_nome} "
                f"{'da atividade ' + str(id_atividade) if id_atividade is not None else ''} "
                f"{'do pedido ' + str(id_pedido) if id_pedido is not None else ''} "
                f"da ordem {id_ordem}: {e}"
            )



def _extrair_objetos_equipamento(equipamentos_alocados):
    """
    Garante extração de objetos de equipamento mesmo se forem:
    - tuplas: (nome, equipamento)
    - listas de listas: [[equipamento1, equipamento2]]
    - tuplas de alocação: (True, [equipamentos], inicio, fim)
    """
    resultado = []
    
    for item in equipamentos_alocados:
        if isinstance(item, tuple):
            # Caso especial: (True, [equipamentos], inicio, fim)
            if len(item) == 4 and isinstance(item[1], list):
                resultado.extend(item[1])
            elif len(item) == 2:
                resultado.append(item[1])
        elif isinstance(item, list):
            resultado.extend(_extrair_objetos_equipamento(item))  # recursivo
        else:
            resultado.append(item)

    return resultado


def _extrair_objetos_equipamento(equipamentos_alocados):
    """
    Garante que a função funcione tanto para listas de tuplas (ex: [(id, equipamento)])
    quanto para listas diretas de equipamentos.
    """
    if equipamentos_alocados and isinstance(equipamentos_alocados[0], tuple):
        return [e[1] for e in equipamentos_alocados]
    return equipamentos_alocados




def rollback_funcionarios(
    funcionarios_alocados: List[Funcionario],
    id_ordem: int,
    id_pedido: Optional[int] = None,
    id_atividade: Optional[int] = None,
):
    """
     🔄 Libera todos os funcionários envolvidos na ordem, pedido ou atividade.

    - Se apenas id_ordem for fornecido, libera por ordem.
    - Se id_ordem e id_pedido forem fornecidos, libera por pedido.
    - Se id_ordem, id_pedido e id_atividade forem fornecidos, libera por atividade.
    """
    for funcionario in funcionarios_alocados:
        try:
            if id_atividade is not None and id_pedido is not None:
                funcionario.liberar_por_atividade(id_ordem=id_ordem, id_pedido=id_pedido, id_atividade=id_atividade)
            elif id_pedido is not None:
                funcionario.liberar_por_pedido(id_ordem=id_ordem, id_pedido=id_pedido)
            else:
                funcionario.liberar_por_ordem(id_ordem=id_ordem)
            
        except Exception as e:
            logger.warning(
                f"⚠️ Falha ao liberar {funcionario.nome} "
                f"{'da atividade ' + str(id_atividade) if id_atividade is not None else ''} "
                f"{'do pedido ' + str(id_pedido) if id_pedido is not None else ''} "
                f"da ordem {id_ordem}: {e}"
            )


