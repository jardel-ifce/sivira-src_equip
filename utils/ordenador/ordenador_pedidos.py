from typing import List


def chave_ordenacao_por_restricoes(pedido):
    """
    Chave de ordenação corrigida que trata atributos ausentes
    """
    criterios = []
    
    # Critério 1: Duração total estimada (mais longo = maior prioridade)
    duracao_total = sum(atividade.duracao.total_seconds() for atividade in pedido.atividades_modulares)
    criterios.append(-duracao_total)  # Negativo para ordem decrescente
    
    # Critério 2: Quantidade (maior = maior prioridade)
    criterios.append(-pedido.quantidade)  # Negativo para ordem decrescente
    
    # Critério 3: Tempo de antecipação (se existir)
    for atividade in pedido.atividades_modulares:
        # Tentar diferentes formas de obter tempo de antecipação
        tempo_antecipacao = 0
        
        if hasattr(atividade, 'tempo_de_antecipacao'):
            tempo_antecipacao = atividade.tempo_de_antecipacao.total_seconds()
        elif hasattr(atividade, 'antecipacao_de_producao'):
            # Converter string para timedelta se necessário
            antecipacao = atividade.antecipacao_de_producao
            if isinstance(antecipacao, str):
                # Assumir formato "HH:MM:SS"
                try:
                    h, m, s = map(int, antecipacao.split(':'))
                    tempo_antecipacao = h * 3600 + m * 60 + s
                except:
                    tempo_antecipacao = 0
            elif hasattr(antecipacao, 'total_seconds'):
                tempo_antecipacao = antecipacao.total_seconds()
        
        criterios.append(tempo_antecipacao)
        break  # Só usar da primeira atividade
    
    # Critério 4: ID do pedido (menor = maior prioridade)
    criterios.append(pedido.id_pedido)
    
    return tuple(criterios)

def ordenar_pedidos_por_restricoes(pedidos):
    """
    Versão corrigida da ordenação de pedidos
    """
    try:
        return sorted(pedidos, key=chave_ordenacao_por_restricoes)
    except Exception as e:
        print(f"⚠️ Erro na ordenação, usando ordem original: {e}")
        return pedidos

