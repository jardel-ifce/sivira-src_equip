from datetime import datetime, timedelta
import re
from analisador_pedidos import AnalisadorPedidos

class CalculadorReagendamento:
    def __init__(self, analisador_pedidos):
        self.analisador = analisador_pedidos
    
    def parse_horario(self, horario_str):
        """Converte string de horário para datetime"""
        # Formato: "HH:MM [DD/MM]"
        match = re.match(r'(\d{2}):(\d{2}) \[(\d{2})/(\d{2})\]', horario_str)
        if match:
            hora, minuto, dia, mes = match.groups()
            # Assumindo ano atual (pode ajustar conforme necessário)
            return datetime(2024, int(mes), int(dia), int(hora), int(minuto))
        return None
    
    def formatar_horario(self, dt):
        """Converte datetime para string no formato do log"""
        return f"{dt.strftime('%H:%M')} [{dt.strftime('%d/%m')}]"
    
    def calcular_duracao(self, atividade):
        """Calcula duração de uma atividade"""
        inicio = self.parse_horario(atividade['inicio'])
        fim = self.parse_horario(atividade['fim'])
        if inicio and fim:
            return fim - inicio
        return timedelta(0)
    
    def encontrar_atividade_comum(self, ordem_base, pedido_base, duplicatas):
        """Encontra dados da atividade comum no pedido base"""
        for id_atividade, ocorrencias in duplicatas.items():
            for ordem, pedido, dados in ocorrencias:
                if ordem == ordem_base and pedido == pedido_base:
                    return id_atividade, dados
        return None, None
    
    def reagendar_pedido(self, ordem_target, pedido_target, horario_atividade_comum, id_atividade_comum):
        """Reagenda um pedido usando backward scheduling"""
        atividades = self.analisador.pedidos.get((ordem_target, pedido_target), [])
        if not atividades:
            return None
        
        # DEBUG: Mostrar ordem das atividades como foram carregadas
        print(f"\n🔍 DEBUG - Ordem das atividades carregadas para Ordem {ordem_target}, Pedido {pedido_target}:")
        for i, ativ in enumerate(atividades):
            print(f"  {i+1}: ID {ativ['id_atividade']} - {ativ['atividade'][:50]}... - {ativ['inicio']}")
        
        # Manter ordem original
        atividades_originais = atividades.copy()
        
        # Encontrar a atividade comum
        atividade_comum_original = None
        for ativ in atividades_originais:
            if ativ['id_atividade'] == id_atividade_comum:
                atividade_comum_original = ativ
                break
        
        if atividade_comum_original is None:
            return None
        
        # Calcular diferença de tempo
        horario_original_fim = self.parse_horario(atividade_comum_original['fim'])
        horario_novo_fim = self.parse_horario(horario_atividade_comum['fim'])
        diferenca_tempo = horario_novo_fim - horario_original_fim
        
        print(f"🔍 DEBUG - Diferença temporal calculada: {diferenca_tempo}")
        print(f"🔍 DEBUG - Horário original da atividade comum: {atividade_comum_original['inicio']} → {atividade_comum_original['fim']}")
        print(f"🔍 DEBUG - Novo horário da atividade comum: {horario_atividade_comum['inicio']} → {horario_atividade_comum['fim']}")
        
        # Aplicar a diferença temporal para todas as atividades
        novas_atividades = []
        for i, ativ in enumerate(atividades_originais):
            nova_ativ = ativ.copy()
            
            if ativ['id_atividade'] == id_atividade_comum:
                # Usar horário da atividade comum base
                nova_ativ['inicio'] = horario_atividade_comum['inicio']
                nova_ativ['fim'] = horario_atividade_comum['fim']
                print(f"  ✅ Atividade comum (pos {i+1}): ID {ativ['id_atividade']} - horário fixo")
            else:
                # Aplicar mesma diferença temporal
                inicio_original = self.parse_horario(ativ['inicio'])
                fim_original = self.parse_horario(ativ['fim'])
                
                novo_inicio = inicio_original + diferenca_tempo
                novo_fim = fim_original + diferenca_tempo
                
                nova_ativ['inicio'] = self.formatar_horario(novo_inicio)
                nova_ativ['fim'] = self.formatar_horario(novo_fim)
                print(f"  🔄 Atividade {i+1}: ID {ativ['id_atividade']} - {ativ['inicio']} → {nova_ativ['inicio']}")
            
            novas_atividades.append(nova_ativ)
        
        # Calcular novo horário final da jornada
        horario_final_jornada = max(self.parse_horario(ativ['fim']) for ativ in novas_atividades)
        
        print(f"🔍 DEBUG - Novo horário final da jornada: {self.formatar_horario(horario_final_jornada)}")
        
        return novas_atividades, horario_final_jornada
    
    def escolher_pedido_base(self, duplicatas):
        """Interface para escolha do pedido base"""
        print("\n=== ESCOLHA DO PEDIDO BASE ===")
        
        # Coletar todos os pedidos envolvidos
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
                
                # Verificar se existe nos pedidos disponíveis
                if (ordem_escolhida, pedido_escolhido) in pedidos_lista:
                    return ordem_escolhida, pedido_escolhido
                else:
                    print("Pedido não encontrado! Escolha entre os pedidos listados acima.")
                    
            except ValueError:
                print("Por favor, digite dois números válidos (ex: 2 1)!")
    
    def calcular_reagendamentos(self, duplicatas):
        """Calcula reagendamentos para todos os pedidos não-base"""
        # Escolher pedido base
        ordem_base, pedido_base = self.escolher_pedido_base(duplicatas)
        
        print(f"\n✅ Pedido base escolhido: Ordem {ordem_base}, Pedido {pedido_base}")
        
        # Encontrar atividade comum no pedido base
        id_atividade_comum, atividade_comum_base = self.encontrar_atividade_comum(
            ordem_base, pedido_base, duplicatas
        )
        
        if not atividade_comum_base:
            print("❌ Erro: não foi possível encontrar atividade comum no pedido base")
            return
        
        print(f"🔄 Atividade comum (ID {id_atividade_comum}): {atividade_comum_base['atividade']}")
        print(f"   Horário base: {atividade_comum_base['inicio']} → {atividade_comum_base['fim']}")
        
        # Calcular reagendamentos para outros pedidos
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
        """Exibe o cronograma reagendado de um pedido"""
        print(f"\n📅 CRONOGRAMA REAGENDADO - Ordem {ordem}, Pedido {pedido}")
        print("-" * 80)
        
        # Manter ordem original - não reordenar
        for ativ in atividades:
            print(f"{ativ['ordem']} | {ativ['pedido']} | {ativ['id_atividade']} | "
                  f"{ativ['produto']} | {ativ['atividade']} | {ativ['equipamento']} | "
                  f"{ativ['inicio']} | {ativ['fim']}")

def main():
    # Usar o analisador já criado
    diretorio = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/equipamentos"
    
    analisador = AnalisadorPedidos(diretorio)
    analisador.carregar_logs()
    duplicatas = analisador.detectar_atividades_duplicadas()
    
    if not duplicatas:
        print("Nenhuma atividade duplicada encontrada.")
        return
    
    # Criar calculador e executar reagendamento
    calculador = CalculadorReagendamento(analisador)
    
    ordem_base, pedido_base, resultados = calculador.calcular_reagendamentos(duplicatas)
    
    # Exibir resultados detalhados
    print(f"\n{'='*60}")
    print("RESUMO DOS REAGENDAMENTOS")
    print(f"{'='*60}")
    print(f"Pedido base: Ordem {ordem_base}, Pedido {pedido_base}")
    
    for (ordem, pedido), dados in resultados.items():
        print(f"\n🔄 Ordem {ordem}, Pedido {pedido}:")
        print(f"   Novo horário final da jornada: {calculador.formatar_horario(dados['horario_final_jornada'])}")
        
        # Exibir cronograma reagendado
        calculador.exibir_cronograma_reagendado(ordem, pedido, dados['atividades'])

if __name__ == "__main__":
    main()