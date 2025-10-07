"""
Módulo para cálculo de reagendamento de pedidos com atividades compartilhadas.

Este módulo implementa a lógica de reagendamento backward scheduling,
permitindo ajustar cronogramas de pedidos que compartilham atividades comuns.
"""

from datetime import datetime, timedelta
import re
from analisador.analisador_pedidos import AnalisadorPedidos


class CalculadorReagendamento:
    """
    Calculador de reagendamento para pedidos com atividades compartilhadas.

    Implementa backward scheduling a partir de uma atividade comum,
    recalculando os horários de todas as atividades de um pedido.

    Attributes:
        analisador (AnalisadorPedidos): Instância do analisador de pedidos
    """
    def __init__(self, analisador_pedidos):
        """
        Inicializa o calculador de reagendamento.

        Args:
            analisador_pedidos (AnalisadorPedidos): Analisador com logs carregados
        """
        self.analisador = analisador_pedidos

    def parse_horario(self, horario_str):
        """
        Converte string de horário para objeto datetime.

        Args:
            horario_str (str): Horário no formato "HH:MM [DD/MM]"

        Returns:
            datetime: Objeto datetime ou None se formato inválido
        """
        match = re.match(r'(\d{2}):(\d{2}) \[(\d{2})/(\d{2})\]', horario_str)
        if match:
            hora, minuto, dia, mes = match.groups()
            return datetime(2024, int(mes), int(dia), int(hora), int(minuto))
        return None

    def formatar_horario(self, dt):
        """
        Converte datetime para string no formato do log.

        Args:
            dt (datetime): Objeto datetime

        Returns:
            str: Horário no formato "HH:MM [DD/MM]"
        """
        return f"{dt.strftime('%H:%M')} [{dt.strftime('%d/%m')}]"

    def calcular_duracao(self, atividade):
        """
        Calcula a duração de uma atividade.

        Args:
            atividade (dict): Dicionário com dados da atividade

        Returns:
            timedelta: Duração da atividade
        """
        inicio = self.parse_horario(atividade['inicio'])
        fim = self.parse_horario(atividade['fim'])
        if inicio and fim:
            return fim - inicio
        return timedelta(0)
    
    def encontrar_atividade_comum(self, ordem_base, pedido_base, duplicatas):
        """
        Encontra dados da atividade comum no pedido base.

        Args:
            ordem_base (int): Número da ordem base
            pedido_base (int): Número do pedido base
            duplicatas (dict): Dicionário de atividades duplicadas

        Returns:
            tuple: (id_atividade, dados) ou (None, None) se não encontrado
        """
        for id_atividade, ocorrencias in duplicatas.items():
            for ordem, pedido, dados in ocorrencias:
                if ordem == ordem_base and pedido == pedido_base:
                    return id_atividade, dados
        return None, None

    def reagendar_pedido(self, ordem_target, pedido_target, horario_atividade_comum, id_atividade_comum):
        """
        Reagenda um pedido usando backward scheduling.

        Aplica uma diferença temporal a todas as atividades do pedido,
        mantendo a atividade comum sincronizada com o pedido base.

        Args:
            ordem_target (int): Ordem do pedido a reagendar
            pedido_target (int): Pedido a reagendar
            horario_atividade_comum (dict): Dados da atividade comum (horários de referência)
            id_atividade_comum (int): ID da atividade compartilhada

        Returns:
            tuple: (novas_atividades, horario_final_jornada) ou None se erro
        """
        atividades = self.analisador.pedidos.get((ordem_target, pedido_target), [])
        if not atividades:
            return None

        print(f"\n🔍 DEBUG - Ordem das atividades carregadas para Ordem {ordem_target}, Pedido {pedido_target}:")
        for i, ativ in enumerate(atividades):
            print(f"  {i+1}: ID {ativ['id_atividade']} - {ativ['atividade'][:50]}... - {ativ['inicio']}")

        atividades_originais = atividades.copy()

        atividade_comum_original = None
        for ativ in atividades_originais:
            if ativ['id_atividade'] == id_atividade_comum:
                atividade_comum_original = ativ
                break

        if atividade_comum_original is None:
            return None

        horario_original_fim = self.parse_horario(atividade_comum_original['fim'])
        horario_novo_fim = self.parse_horario(horario_atividade_comum['fim'])
        diferenca_tempo = horario_novo_fim - horario_original_fim

        print(f"🔍 DEBUG - Diferença temporal calculada: {diferenca_tempo}")
        print(f"🔍 DEBUG - Horário original da atividade comum: {atividade_comum_original['inicio']} → {atividade_comum_original['fim']}")
        print(f"🔍 DEBUG - Novo horário da atividade comum: {horario_atividade_comum['inicio']} → {horario_atividade_comum['fim']}")

        novas_atividades = []
        for i, ativ in enumerate(atividades_originais):
            nova_ativ = ativ.copy()

            if ativ['id_atividade'] == id_atividade_comum:
                nova_ativ['inicio'] = horario_atividade_comum['inicio']
                nova_ativ['fim'] = horario_atividade_comum['fim']
                print(f"  ✅ Atividade comum (pos {i+1}): ID {ativ['id_atividade']} - horário fixo")
            else:
                inicio_original = self.parse_horario(ativ['inicio'])
                fim_original = self.parse_horario(ativ['fim'])

                novo_inicio = inicio_original + diferenca_tempo
                novo_fim = fim_original + diferenca_tempo

                nova_ativ['inicio'] = self.formatar_horario(novo_inicio)
                nova_ativ['fim'] = self.formatar_horario(novo_fim)
                print(f"  🔄 Atividade {i+1}: ID {ativ['id_atividade']} - {ativ['inicio']} → {nova_ativ['inicio']}")

            novas_atividades.append(nova_ativ)

        horario_final_jornada = max(self.parse_horario(ativ['fim']) for ativ in novas_atividades)

        print(f"🔍 DEBUG - Novo horário final da jornada: {self.formatar_horario(horario_final_jornada)}")

        return novas_atividades, horario_final_jornada
    
    def escolher_pedido_base(self, duplicatas):
        """
        Interface interativa para escolha do pedido base.

        Args:
            duplicatas (dict): Dicionário de atividades duplicadas

        Returns:
            tuple: (ordem, pedido) escolhidos pelo usuário
        """
        print("\n=== ESCOLHA DO PEDIDO BASE ===")

        pedidos_envolvidos = set()
        for id_atividade, ocorrencias in duplicatas.items():
            for ordem, pedido, dados in ocorrencias:
                pedidos_envolvidos.add((ordem, pedido))

        pedidos_lista = sorted(list(pedidos_envolvidos))

        print("Pedidos que compartilham atividades:")
        for ordem, pedido in pedidos_lista:
            print(f"  - Ordem {ordem}, Pedido {pedido}")

        while True:
            try:
                entrada = input("\nDigite a ordem e pedido base (formato: ordem pedido, ex: 2 1): ").strip()
                partes = entrada.split()

                if len(partes) != 2:
                    print("Formato inválido! Use: ordem pedido (ex: 2 1)")
                    continue

                ordem_escolhida = int(partes[0])
                pedido_escolhido = int(partes[1])

                if (ordem_escolhida, pedido_escolhido) in pedidos_lista:
                    return ordem_escolhida, pedido_escolhido
                else:
                    print("Pedido não encontrado! Escolha entre os pedidos listados acima.")

            except ValueError:
                print("Por favor, digite dois números válidos (ex: 2 1)!")
    
    def calcular_reagendamentos(self, duplicatas):
        """
        Calcula reagendamentos para todos os pedidos não-base.

        Args:
            duplicatas (dict): Dicionário de atividades duplicadas

        Returns:
            tuple: (ordem_base, pedido_base, resultados) onde resultados é um dict
                   com os dados reagendados de cada pedido
        """
        ordem_base, pedido_base = self.escolher_pedido_base(duplicatas)

        print(f"\n✅ Pedido base escolhido: Ordem {ordem_base}, Pedido {pedido_base}")

        id_atividade_comum, atividade_comum_base = self.encontrar_atividade_comum(
            ordem_base, pedido_base, duplicatas
        )

        if not atividade_comum_base:
            print("❌ Erro: não foi possível encontrar atividade comum no pedido base")
            return

        print(f"🔄 Atividade comum (ID {id_atividade_comum}): {atividade_comum_base['atividade']}")
        print(f"   Horário base: {atividade_comum_base['inicio']} → {atividade_comum_base['fim']}")

        resultados = {}

        for id_ativ, ocorrencias in duplicatas.items():
            if id_ativ == id_atividade_comum:
                for ordem, pedido, dados in ocorrencias:
                    if ordem != ordem_base or pedido != pedido_base:
                        print(f"\n📋 Reagendando Ordem {ordem}, Pedido {pedido}...")

                        resultado = self.reagendar_pedido(
                            ordem, pedido, atividade_comum_base, id_atividade_comum
                        )

                        if resultado:
                            novas_atividades, horario_final = resultado
                            resultados[(ordem, pedido)] = {
                                'atividades': novas_atividades,
                                'horario_final_jornada': horario_final
                            }

                            print(f"   ✅ Novo horário final da jornada: {self.formatar_horario(horario_final)}")

        return ordem_base, pedido_base, resultados

    def exibir_cronograma_reagendado(self, ordem, pedido, atividades):
        """
        Exibe o cronograma reagendado de um pedido.

        Args:
            ordem (int): Número da ordem
            pedido (int): Número do pedido
            atividades (list): Lista de atividades reagendadas
        """
        print(f"\n📅 CRONOGRAMA REAGENDADO - Ordem {ordem}, Pedido {pedido}")
        print("-" * 80)

        for ativ in atividades:
            print(f"{ativ['ordem']} | {ativ['pedido']} | {ativ['id_atividade']} | "
                  f"{ativ['produto']} | {ativ['atividade']} | {ativ['equipamento']} | "
                  f"{ativ['inicio']} | {ativ['fim']}")


