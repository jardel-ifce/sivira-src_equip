from datetime import datetime

def mostrar_ocupacoes_do_equipamento(equipamento, data_desejada, atividades_por_id=None):
    """
    Mostra todas as ocupações de um equipamento em um dia específico.
    Se atividades_por_id for fornecido, mostra o tipo da atividade.
    
    Args:
        equipamento: objeto Equipamento
        data_desejada: datetime.date
        atividades_por_id: dict opcional {atividade_id: Atividade}
    """
    print(f"\n📋 Ocupações do equipamento '{equipamento.nome}' em {data_desejada.strftime('%d/%m/%Y')}:")
    encontrou = False
    for inicio, fim, atividade_id in sorted(equipamento.ocupacao, key=lambda x: x[0]):
        if inicio.date() == data_desejada:
            if atividades_por_id and atividade_id in atividades_por_id:
                tipo = atividades_por_id[atividade_id].tipo_atividade.name
                print(f" - Atividade ID {atividade_id} | {tipo}: {inicio.time()} → {fim.time()}")
            else:
                print(f" - Atividade ID {atividade_id}: {inicio.time()} → {fim.time()}")
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
