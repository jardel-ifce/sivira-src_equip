import os
from datetime import datetime
from models.funcionarios.funcionario import Funcionario
from models.equipamentos.equipamento import Equipamento


def registrar_log_funcionarios(ordem_id: int, pedido_id: int, id_atividade: int, nome_item: str,
                               nome_atividade: str, funcionarios: list[Funcionario],
                               inicio: datetime, fim: datetime):
    os.makedirs("logs", exist_ok=True)
    caminho = f"logs/funcionarios | Ordem: {ordem_id} Pedido: {pedido_id}.log"
    with open(caminho, "a", encoding="utf-8") as arq:
        for funcionario in funcionarios:
            linha = (
                f"{ordem_id} | {pedido_id} | {id_atividade} | {nome_item} | {nome_atividade} | "
                f"{funcionario.nome} | {inicio.strftime('%H:%M')} | {fim.strftime('%H:%M')} \n"
            )
            arq.write(linha)


def registrar_log_equipamentos(ordem_id: int, pedido_id: int, id_atividade: int, nome_item: str,
                                nome_atividade: str, equipamentos: list[tuple],
                                inicio: datetime, fim: datetime):
    os.makedirs("logs", exist_ok=True)
    caminho = f"logs/equipamentos |Ordem: {ordem_id} | Pedido: {pedido_id}.log"
    with open(caminho, "a", encoding="utf-8") as arq:
        for _, equipamento, i, f in equipamentos:
            linha = (
                f"{ordem_id} | {pedido_id} | {id_atividade} | {nome_item} | {nome_atividade} | "
                f"{equipamento.nome} | {i.strftime('%H:%M')} | {f.strftime('%H:%M')} \n"
            )
            arq.write(linha)
