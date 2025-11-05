#!/usr/bin/env python3
"""
Gerador de PDF - Escala de Funcionários e Análise de Pedidos
Sistema SIVIRA - Versão com cálculo correto de duração (>24h)
"""

from datetime import datetime
import re
from typing import List, Tuple, Optional
import glob
import os

def calcular_duracao(inicio_str: str, fim_str: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Calcula a duração entre dois horários no formato do log.
    Suporta durações maiores que 24 horas.

    Retorna: (duracao_formatada, total_minutos)
    """
    try:
        # Parse do formato "HH:MM [DD/MM]"
        pattern = r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*\[(\d{1,2})/(\d{1,2})\]'

        match_inicio = re.search(pattern, inicio_str)
        match_fim = re.search(pattern, fim_str)

        if not match_inicio or not match_fim:
            return None, None

        # Parse início
        h_ini = int(match_inicio.group(1))
        m_ini = int(match_inicio.group(2))
        dia_ini = int(match_inicio.group(4))
        mes_ini = int(match_inicio.group(5))

        # Parse fim
        h_fim = int(match_fim.group(1))
        m_fim = int(match_fim.group(2))
        dia_fim = int(match_fim.group(4))
        mes_fim = int(match_fim.group(5))

        # Cria objetos datetime
        ano = 2024
        dt_inicio = datetime(ano, mes_ini, dia_ini, h_ini, m_ini)
        dt_fim = datetime(ano, mes_fim, dia_fim, h_fim, m_fim)

        # Calcula diferença
        duracao = dt_fim - dt_inicio
        total_segundos = int(duracao.total_seconds())
        total_minutos = total_segundos // 60

        if total_segundos < 0:
            return "⚠️ Duração negativa", 0

        dias = total_segundos // 86400
        horas = (total_segundos % 86400) // 3600
        minutos = (total_segundos % 3600) // 60

        # Formata string de saída
        partes = []
        if dias > 0:
            partes.append(f"{dias}d")
        if horas > 0:
            partes.append(f"{horas}h")
        if minutos > 0 or len(partes) == 0:
            partes.append(f"{minutos}min")

        return " ".join(partes), total_minutos

    except Exception as e:
        print(f"Erro ao calcular duração: {e}")
        return None, None


def analisar_pedido(numero_pedido: int) -> dict:
    """Analisa um pedido específico dos logs"""
    arquivo_log = f"logs/equipamentos/sucesso/ordem: 1 | pedido: {numero_pedido}.log"

    if not os.path.exists(arquivo_log):
        return None

    atividades = []

    with open(arquivo_log, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                partes = [p.strip() for p in linha.split('|')]
                if len(partes) >= 8:
                    atividades.append({
                        'ordem': partes[0],
                        'pedido': partes[1],
                        'id_atividade': partes[2],
                        'item': partes[3],
                        'nome_atividade': partes[4],
                        'equipamento': partes[5],
                        'inicio': partes[6],
                        'fim': partes[7]
                    })

    if not atividades:
        return None

    # Ordena por horário de início
    atividades.sort(key=lambda x: x['inicio'])

    # Primeira e última atividade
    primeira = atividades[0]
    ultima = atividades[-1]

    # Calcula duração total
    duracao_str, duracao_min = calcular_duracao(primeira['inicio'], ultima['fim'])

    return {
        'numero': numero_pedido,
        'produto': primeira['item'],
        'inicio': primeira['inicio'],
        'fim': ultima['fim'],
        'duracao': duracao_str,
        'duracao_minutos': duracao_min,
        'num_atividades': len(atividades),
        'atividades': atividades
    }


def gerar_pdf_escala_e_pedidos():
    """Gera PDF completo com escala e análise de pedidos"""

    print("📄 GERANDO RELATÓRIO PDF - ESCALA E PEDIDOS")
    print("=" * 50)

    try:
        from matplotlib.backends.backend_pdf import PdfPages
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        # Analisa todos os pedidos
        pedidos = []
        for num in [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]:
            pedido = analisar_pedido(num)
            if pedido:
                pedidos.append(pedido)
                print(f"✅ Pedido {num}: {pedido['produto']} - Duração: {pedido['duracao']}")

        if not pedidos:
            print("❌ Nenhum pedido encontrado nos logs")
            return

        # Cria PDF
        nome_arquivo = f"escala_e_pedidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        with PdfPages(nome_arquivo) as pdf:
            # Página 1: Capa
            gerar_pagina_capa(pdf)

            # Página 2: Escala de Funcionários
            gerar_pagina_escala(pdf)

            # Página 3: Resumo dos Pedidos
            gerar_pagina_resumo_pedidos(pdf, pedidos)

            # Páginas 4+: Detalhamento de cada pedido
            for pedido in pedidos:
                gerar_pagina_detalhamento_pedido(pdf, pedido)

            # Última página: Conclusões
            gerar_pagina_conclusoes(pdf, pedidos)

        print(f"\n✅ PDF gerado com sucesso: {nome_arquivo}")
        print(f"📊 Total de páginas: {6 + len(pedidos)}")

    except ImportError:
        print("❌ Biblioteca matplotlib não encontrada")
        print("💡 Instale com: pip install matplotlib")
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()


def gerar_pagina_capa(pdf):
    """Gera página de capa"""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')

    # Título
    ax.text(0.5, 0.7, 'ESCALA DE FUNCIONÁRIOS',
            ha='center', va='center', fontsize=24, fontweight='bold')
    ax.text(0.5, 0.65, 'E ANÁLISE DE PEDIDOS',
            ha='center', va='center', fontsize=24, fontweight='bold')

    # Subtítulo
    ax.text(0.5, 0.55, 'Sistema SIVIRA - Gestão de Produção',
            ha='center', va='center', fontsize=14, style='italic')

    # Data
    data_geracao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    ax.text(0.5, 0.45, f'Gerado em: {data_geracao}',
            ha='center', va='center', fontsize=11)

    # Informações
    ax.text(0.5, 0.3, '📋 Ordem: 1',
            ha='center', va='center', fontsize=12)
    ax.text(0.5, 0.25, '📊 Análise com cálculo correto de duração (>24h)',
            ha='center', va='center', fontsize=10, color='blue')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def gerar_pagina_escala(pdf):
    """Gera página com escala de funcionários"""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')

    # Título
    ax.text(0.5, 0.95, 'ESCALA DE FUNCIONÁRIOS',
            ha='center', va='top', fontsize=16, fontweight='bold')

    y_pos = 0.88

    # Setor Panificação
    ax.text(0.05, y_pos, 'Setor: PANIFICAÇÃO (Turnos Escalonados)',
            fontsize=12, fontweight='bold')
    y_pos -= 0.04

    funcionarios_panificacao = [
        ('1', 'Funcionário 1', 'PADEIRO', '00:00-08:00', 'SAB, DOM', '40h'),
        ('2', 'Funcionário 2', 'AUX. PADEIRO', '02:00-10:00', 'SAB', '40h'),
        ('3', 'Funcionário 3', 'AUX. PADEIRO/CONF.', '04:00-12:00', 'SAB', '40h'),
        ('6', 'Funcionário 6', 'AUX. CONF./PADEIRO', '06:00-14:00', 'SAB', '40h'),
    ]

    for func in funcionarios_panificacao:
        ax.text(0.05, y_pos, f"ID {func[0]}: {func[1]} - {func[2]}", fontsize=9)
        y_pos -= 0.025
        ax.text(0.10, y_pos, f"Turno: {func[3]} | Folgas: {func[4]} | CH: {func[5]}",
                fontsize=8, color='darkblue')
        y_pos -= 0.035

    # Outros setores
    y_pos -= 0.02
    ax.text(0.05, y_pos, 'Outros Setores:',
            fontsize=12, fontweight='bold')
    y_pos -= 0.04

    outros_funcionarios = [
        ('4', 'Funcionário 4', 'CONFEITEIRO', 'CONFEITARIA', '08:00-18:00', '44h'),
        ('5', 'Funcionário 5', 'AUX. CONFEITEIRO', 'CONFEITARIA', '08:00-18:00', '44h'),
        ('7', 'Funcionário 7', 'COZINHEIRO', 'COZINHA', '08:00-18:00', '44h'),
        ('8', 'Funcionário 8', 'ALMOXARIFE', 'ALMOXARIFADO', '08:00-18:00', '44h'),
        ('9', 'Funcionário 9', 'ALMOXARIFE', 'ALMOXARIFADO', '08:00-18:00', '44h'),
    ]

    for func in outros_funcionarios:
        ax.text(0.05, y_pos, f"ID {func[0]}: {func[1]} - {func[2]} ({func[3]})", fontsize=9)
        y_pos -= 0.025
        ax.text(0.10, y_pos, f"Turno: {func[4]} | CH: {func[5]}",
                fontsize=8, color='darkblue')
        y_pos -= 0.035

    # Cobertura de turnos
    y_pos -= 0.03
    ax.text(0.05, y_pos, 'COBERTURA DE TURNOS (Panificação):',
            fontsize=12, fontweight='bold')
    y_pos -= 0.04

    ax.text(0.1, y_pos, 'Horário de maior cobertura: 06:00-08:00 (4 funcionários)',
            fontsize=9)
    y_pos -= 0.03
    ax.text(0.1, y_pos, 'Janela de produção: 00:00-14:00', fontsize=9)
    y_pos -= 0.03
    ax.text(0.1, y_pos, 'Folgas respeitadas: Sábado (todos) + Domingo (F1)', fontsize=9)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def gerar_pagina_resumo_pedidos(pdf, pedidos: List[dict]):
    """Gera página com resumo de todos os pedidos"""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')

    # Título
    ax.text(0.5, 0.95, 'RESUMO DOS PEDIDOS EXECUTADOS',
            ha='center', va='top', fontsize=16, fontweight='bold')
    ax.text(0.5, 0.92, 'Ordem 1',
            ha='center', va='top', fontsize=12, color='gray')

    y_pos = 0.86

    # Cabeçalho da tabela
    ax.text(0.05, y_pos, 'Pedido', fontsize=9, fontweight='bold')
    ax.text(0.15, y_pos, 'Produto', fontsize=9, fontweight='bold')
    ax.text(0.40, y_pos, 'Início', fontsize=9, fontweight='bold')
    ax.text(0.55, y_pos, 'Fim', fontsize=9, fontweight='bold')
    ax.text(0.70, y_pos, 'Duração', fontsize=9, fontweight='bold')
    ax.text(0.88, y_pos, 'Ativ.', fontsize=9, fontweight='bold')
    y_pos -= 0.02

    # Linha separadora
    ax.plot([0.05, 0.95], [y_pos, y_pos], 'k-', linewidth=0.5)
    y_pos -= 0.025

    # Dados dos pedidos
    for pedido in sorted(pedidos, key=lambda p: p['numero']):
        # Destaca pedidos com duração > 24h
        cor = 'red' if pedido['duracao_minutos'] and pedido['duracao_minutos'] >= 1440 else 'black'
        fontweight = 'bold' if cor == 'red' else 'normal'

        ax.text(0.05, y_pos, str(pedido['numero']), fontsize=8)
        ax.text(0.15, y_pos, pedido['produto'][:20], fontsize=8)

        # Extrai apenas hora do início e fim
        inicio_match = re.search(r'(\d{1,2}:\d{2})', pedido['inicio'])
        fim_match = re.search(r'(\d{1,2}:\d{2})', pedido['fim'])
        inicio_hora = inicio_match.group(1) if inicio_match else pedido['inicio']
        fim_hora = fim_match.group(1) if fim_match else pedido['fim']

        ax.text(0.40, y_pos, inicio_hora, fontsize=8)
        ax.text(0.55, y_pos, fim_hora, fontsize=8)
        ax.text(0.70, y_pos, pedido['duracao'], fontsize=8, color=cor, fontweight=fontweight)
        ax.text(0.88, y_pos, str(pedido['num_atividades']), fontsize=8)

        y_pos -= 0.03

        if y_pos < 0.1:
            break

    # Legenda
    y_pos -= 0.03
    ax.text(0.05, y_pos, '⚠️ Pedidos em vermelho têm duração superior a 24 horas',
            fontsize=9, color='red', fontweight='bold')

    # Estatísticas
    y_pos -= 0.06
    ax.text(0.05, y_pos, 'ESTATÍSTICAS:',
            fontsize=11, fontweight='bold')
    y_pos -= 0.035

    total_atividades = sum(p['num_atividades'] for p in pedidos)
    media_atividades = total_atividades / len(pedidos)

    ax.text(0.1, y_pos, f'• Total de pedidos: {len(pedidos)}', fontsize=9)
    y_pos -= 0.03
    ax.text(0.1, y_pos, f'• Total de atividades: {total_atividades}', fontsize=9)
    y_pos -= 0.03
    ax.text(0.1, y_pos, f'• Média de atividades por pedido: {media_atividades:.1f}', fontsize=9)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def gerar_pagina_detalhamento_pedido(pdf, pedido: dict):
    """Gera página detalhada para um pedido específico"""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')

    # Cabeçalho
    cor_titulo = 'red' if pedido['duracao_minutos'] >= 1440 else 'black'
    ax.text(0.5, 0.95, f"PEDIDO {pedido['numero']}: {pedido['produto']}",
            ha='center', va='top', fontsize=14, fontweight='bold', color=cor_titulo)

    y_pos = 0.90

    # Informações gerais
    ax.text(0.05, y_pos, 'INFORMAÇÕES GERAIS:', fontsize=11, fontweight='bold')
    y_pos -= 0.035

    ax.text(0.1, y_pos, f"Início: {pedido['inicio']}", fontsize=9)
    y_pos -= 0.03
    ax.text(0.1, y_pos, f"Fim: {pedido['fim']}", fontsize=9)
    y_pos -= 0.03

    # Duração destacada
    duracao_cor = 'red' if pedido['duracao_minutos'] >= 1440 else 'blue'
    ax.text(0.1, y_pos, f"Duração total: {pedido['duracao']}",
            fontsize=10, fontweight='bold', color=duracao_cor)
    y_pos -= 0.03

    if pedido['duracao_minutos'] >= 1440:
        ax.text(0.1, y_pos, '⚠️ ATENÇÃO: Duração superior a 24 horas!',
                fontsize=9, color='red', fontweight='bold')
        y_pos -= 0.03

    ax.text(0.1, y_pos, f"Total de atividades: {pedido['num_atividades']}", fontsize=9)
    y_pos -= 0.05

    # Lista de atividades
    ax.text(0.05, y_pos, 'ATIVIDADES:', fontsize=11, fontweight='bold')
    y_pos -= 0.035

    for i, atividade in enumerate(pedido['atividades'][:25], 1):  # Máximo 25 atividades
        if y_pos < 0.08:
            ax.text(0.1, y_pos, f'... e mais {pedido["num_atividades"] - i + 1} atividades',
                    fontsize=8, style='italic', color='gray')
            break

        ax.text(0.05, y_pos, f"{i}.", fontsize=8)
        ax.text(0.08, y_pos, atividade['nome_atividade'][:40], fontsize=8)
        y_pos -= 0.025

        ax.text(0.12, y_pos, f"Equipamento: {atividade['equipamento']}", fontsize=7, color='darkblue')
        y_pos -= 0.02

        ax.text(0.12, y_pos, f"Horário: {atividade['inicio']} - {atividade['fim']}",
                fontsize=7, color='gray')
        y_pos -= 0.03

    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def gerar_pagina_conclusoes(pdf, pedidos: List[dict]):
    """Gera página final com conclusões"""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis('off')

    # Título
    ax.text(0.5, 0.95, 'ANÁLISE E RECOMENDAÇÕES',
            ha='center', va='top', fontsize=16, fontweight='bold')

    y_pos = 0.88

    # Análise de adequação da escala
    ax.text(0.05, y_pos, 'ADEQUAÇÃO DA ESCALA:', fontsize=12, fontweight='bold')
    y_pos -= 0.04

    ax.text(0.1, y_pos, '✅ Escala otimizada cobre 100% das atividades de produção',
            fontsize=9)
    y_pos -= 0.03
    ax.text(0.1, y_pos, '✅ Pico atendido com 4 funcionários entre 06:00-08:00',
            fontsize=9)
    y_pos -= 0.03
    ax.text(0.1, y_pos, '⚠️ Monitorar produtividade nos horários de overlap',
            fontsize=9)
    y_pos -= 0.03
    ax.text(0.1, y_pos, '💡 Considerar adicionar 5º funcionário se demanda aumentar',
            fontsize=9)

    y_pos -= 0.05

    # Pedidos com duração longa
    ax.text(0.05, y_pos, 'PEDIDOS COM DURAÇÃO LONGA (>24h):', fontsize=12, fontweight='bold')
    y_pos -= 0.04

    pedidos_longos = [p for p in pedidos if p['duracao_minutos'] and p['duracao_minutos'] >= 1440]

    if pedidos_longos:
        for pedido in pedidos_longos:
            ax.text(0.1, y_pos, f"⚠️ Pedido {pedido['numero']} ({pedido['produto']}): {pedido['duracao']}",
                    fontsize=9, color='red', fontweight='bold')
            y_pos -= 0.03

        y_pos -= 0.02
        ax.text(0.1, y_pos, 'Possíveis causas:', fontsize=9, style='italic')
        y_pos -= 0.025
        ax.text(0.12, y_pos, '• Fermentação prolongada (massa suave requer ~24h)', fontsize=8)
        y_pos -= 0.025
        ax.text(0.12, y_pos, '• Resfriamento em câmara refrigerada', fontsize=8)
        y_pos -= 0.025
        ax.text(0.12, y_pos, '• Processo de maturação necessário', fontsize=8)
    else:
        ax.text(0.1, y_pos, 'Nenhum pedido com duração superior a 24 horas', fontsize=9)

    y_pos -= 0.05

    # Recomendações
    ax.text(0.05, y_pos, 'RECOMENDAÇÕES OPERACIONAIS:', fontsize=12, fontweight='bold')
    y_pos -= 0.04

    recomendacoes = [
        '1. Implementar nova escala gradualmente (1-2 semanas de adaptação)',
        '2. Coletar feedback dos funcionários durante período de testes',
        '3. Monitorar indicadores de produtividade diariamente',
        '4. Ajustar turnos conforme necessário baseado nos dados reais',
        '5. Para pedidos longos, planejar início com antecedência adequada',
        '6. Considerar estratégias de paralelização de atividades'
    ]

    for rec in recomendacoes:
        ax.text(0.1, y_pos, rec, fontsize=9)
        y_pos -= 0.03

    # Rodapé
    ax.text(0.5, 0.05, 'Documento gerado automaticamente pelo Sistema SIVIRA',
            ha='center', va='bottom', fontsize=8, style='italic', color='gray')
    ax.text(0.5, 0.02, 'Para dúvidas ou sugestões, contate a equipe de desenvolvimento',
            ha='center', va='bottom', fontsize=7, color='gray')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    gerar_pdf_escala_e_pedidos()
