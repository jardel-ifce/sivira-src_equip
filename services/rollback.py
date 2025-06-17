from typing import List, Optional
from models.atividade_base import Atividade
from models.funcionarios.funcionario import Funcionario
from models.equips.equipamento import Equipamento


def rollback_atividade(
    atividade: Atividade,
    funcionarios: Optional[List[Funcionario]] = None,
    equipamentos: Optional[List[Equipamento]] = None
):
    """
    ⛔ Rollback completo: desaloca funcionários e equipamentos da atividade informada.

    Args:
        atividade (Atividade): Atividade que falhou e precisa ter alocações revertidas
        funcionarios (List[Funcionario], optional): Lista de funcionários a desalocar
        equipamentos (List[Equipamento], optional): Lista de equipamentos a desalocar
    """
    if funcionarios:
        for f in funcionarios:
            f.desalocar(atividade.id, atividade.id_ordem)

    if equipamentos:
        for e in equipamentos:
            e.liberar_por_atividade(atividade.id, atividade.id_ordem)
