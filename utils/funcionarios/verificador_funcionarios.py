from collections import defaultdict
from datetime import datetime

def verificar_agenda_funcionarios(funcionarios, fips_por_tipo_profissional):
    """
    Verifica conflitos de horários, uso incorreto de FIP e reaproveitamento de profissionais.

    :param funcionarios: lista de objetos Funcionario (com .nome, .ocupacoes, .tipo)
    :param fips_por_tipo_profissional: dict, exemplo: {"PADEIRO": 2, "AUXILIAR_DE_PADEIRO": 1}
    """

    print("🔎 Verificando agenda de funcionários...\n")

    conflitos = []
    uso_incorreto_de_fip = []
    pedidos_por_funcionario = defaultdict(set)
    funcionarios_por_pedido = defaultdict(list)

    for funcionario in funcionarios:
        ocups = sorted(funcionario.ocupacoes, key=lambda x: x[3])  # ordenar por início
        nome = funcionario.nome
        tipo = funcionario.tipo.name if hasattr(funcionario.tipo, "name") else str(funcionario.tipo)

        for i in range(len(ocups)):
            id_ordem, id_atividade, quantidade, inicio, fim = ocups[i]
            pedidos_por_funcionario[nome].add(id_ordem)
            funcionarios_por_pedido[id_ordem].append((nome, tipo, fips_por_tipo_profissional.get(tipo, 999)))

            # Verifica sobreposição com a próxima
            if i < len(ocups) - 1:
                _, _, _, prox_inicio, prox_fim = ocups[i + 1]
                if fim > prox_inicio:
                    conflitos.append((nome, fim.strftime("%H:%M"), prox_inicio.strftime("%H:%M")))

    # 🔁 Verificar se o melhor FIP foi utilizado em cada pedido
    for ordem_id, lista in funcionarios_por_pedido.items():
        # tipo: {nome, tipo, fip}
        lista_ordenada = sorted(lista, key=lambda x: x[2])  # menor FIP primeiro
        melhor_fip = lista_ordenada[0][2]
        nomes_com_melhor_fip = {nome for nome, _, fip in lista_ordenada if fip == melhor_fip}

        for nome, _, fip in lista_ordenada:
            if fip > melhor_fip:
                uso_incorreto_de_fip.append((ordem_id, nome, fip, melhor_fip))

    # 🔍 Resultados
    if conflitos:
        print("🚨 Conflitos de horário encontrados:")
        for nome, fim, inicio_prox in conflitos:
            print(f"  - {nome}: fim às {fim} sobrepõe início às {inicio_prox}")
    else:
        print("✅ Nenhum conflito de horário encontrado.")

    if uso_incorreto_de_fip:
        print("\n🚨 Uso incorreto de FIP (profissionais com FIP maior foram alocados):")
        for ordem_id, nome, fip_usado, fip_esperado in uso_incorreto_de_fip:
            print(f"  - Ordem {ordem_id}: {nome} com FIP {fip_usado}, deveria ser {fip_esperado}")
    else:
        print("✅ Todos os profissionais alocados com menor FIP permitido.")

    print("\n📊 Resumo por funcionário:")
    for nome, pedidos in pedidos_por_funcionario.items():
        print(f"  - {nome} atuou nos pedidos: {sorted(pedidos)}")

    print("\n✅ Verificação finalizada.\n")
