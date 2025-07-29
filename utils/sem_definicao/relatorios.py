from datetime import datetime
from typing import List
from models.funcionarios.funcionario import Funcionario

def mostrar_ocupacoes_do_equipamento(equipamento, data_desejada, atividades_por_id=None):
    """
    Mostra todas as ocupações de um equipamento em um dia específico.
    Se atividades_por_id for fornecido, mostra o tipo da atividade.
    
    Args:
        equipamento: objeto Equipamento
        data_desejada: datetime.date
        atividades_por_id: dict opcional {id_atividade: Atividade}
    """
    print(f"\n📋 Ocupações do equipamento '{equipamento.nome}' em {data_desejada.strftime('%d/%m/%Y')}:")
    encontrou = False
    for inicio, fim, id_atividade in sorted(equipamento.ocupacao, key=lambda x: x[0]):
        if inicio.date() == data_desejada:
            if atividades_por_id and id_atividade in atividades_por_id:
                tipo = atividades_por_id[id_atividade].tipo_atividade.name
                print(f" - Atividade ID {id_atividade} | {tipo}: {inicio.time()} → {fim.time()}")
            else:
                print(f" - Atividade ID {id_atividade}: {inicio.time()} → {fim.time()}")
            encontrou = True
    if not encontrou:
        print("   Nenhuma ocupação registrada nesse dia.")

def mostrar_ocupacoes_de_equipamentos(lista_equipamentos, data_desejada, atividades_por_id=None):
    """
    Mostra as ocupações de uma lista de equipamentos em um dia específico.
    """
    print(f"\n📋 RELATÓRIO DE OCUPAÇÃO - Data: {data_desejada.strftime('%d/%m/%Y')}")
    for equipamento in lista_equipamentos:
        mostrar_ocupacoes_do_equipamento(equipamento, data_desejada, atividades_por_id)



def exibir_historico_global(funcionarios: list):
    """
    Mostra um histórico único e ordenado de todas as atividades de todos os funcionários,
    incluindo o nome do funcionário responsável e da atividade.
    """
    entradas = []
    for f in funcionarios:
        for id_ordem, id_atividade, nome_atividade, ini, fim in f.historico_alocacoes:
            entradas.append((f.nome, id_ordem, id_atividade, nome_atividade, ini, fim))

    entradas_ordenadas = sorted(entradas, key=lambda x: x[4])  # ordena por início

    print("🗃️ Histórico Global de Alocações:")
    for nome, id_ordem, id_atividade, nome_atividade, ini, fim in entradas_ordenadas:
        print(
            f"👷 {nome} → Ordem {id_ordem} | Atividade {id_atividade} ({nome_atividade}) | "
            f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
        )



def exibir_ocupacoes_funcionarios_ordenadas_por_ordem(funcionarios: List[Funcionario]):
    """
    🧑‍🏭 Exibe ocupações dos funcionários agrupadas por ordem e ordenadas por horário.
    """
    for funcionario in funcionarios:
        if not funcionario.ocupacoes:
            print(f"\n✅ {funcionario.nome} não possui ocupações registradas.")
            continue

        print(f"\n📋 Ocupações de {funcionario.nome} agrupadas por ordem:")

        ocupacoes_por_ordem = {}
        for id_ordem, id_atividade, id_json, inicio, fim in funcionario.ocupacoes:
            if id_ordem not in ocupacoes_por_ordem:
                ocupacoes_por_ordem[id_ordem] = []
            ocupacoes_por_ordem[id_ordem].append((id_atividade, id_json, inicio, fim))

        for id_ordem in sorted(ocupacoes_por_ordem.keys()):
            print(f"📦 Ordem {id_ordem}:")
            for id_atividade, id_json, inicio, fim in sorted(ocupacoes_por_ordem[id_ordem], key=lambda o: o[2]):
                data_str = inicio.strftime('%d/%m/%Y')
                hora_inicio = inicio.strftime('%H:%M')
                hora_fim = fim.strftime('%H:%M')
                duracao_min = int((fim - inicio).total_seconds() // 60)
                print(
                    f"   • Atividade {id_atividade}/{id_json} — {data_str} "
                    f"das {hora_inicio} às {hora_fim} ({duracao_min} min)"
                )
