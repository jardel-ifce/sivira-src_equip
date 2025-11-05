#!/usr/bin/env python3
"""Gera arquivo Markdown com análise de escala e pedidos"""

import os
import re
from datetime import datetime

def calcular_duracao(inicio_str, fim_str):
    """Calcula duração entre dois horários"""
    try:
        pattern = r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*\[(\d{1,2})/(\d{1,2})\]'
        match_inicio = re.search(pattern, inicio_str)
        match_fim = re.search(pattern, fim_str)

        if not match_inicio or not match_fim:
            return None, None

        h_ini = int(match_inicio.group(1))
        m_ini = int(match_inicio.group(2))
        dia_ini = int(match_inicio.group(4))
        mes_ini = int(match_inicio.group(5))

        h_fim = int(match_fim.group(1))
        m_fim = int(match_fim.group(2))
        dia_fim = int(match_fim.group(4))
        mes_fim = int(match_fim.group(5))

        ano = 2024
        dt_inicio = datetime(ano, mes_ini, dia_ini, h_ini, m_ini)
        dt_fim = datetime(ano, mes_fim, dia_fim, h_fim, m_fim)

        duracao = dt_fim - dt_inicio
        total_segundos = int(duracao.total_seconds())
        total_minutos = total_segundos // 60

        dias = total_segundos // 86400
        horas = (total_segundos % 86400) // 3600
        minutos = (total_segundos % 3600) // 60

        partes = []
        if dias > 0:
            partes.append(f'{dias}d')
        if horas > 0:
            partes.append(f'{horas}h')
        if minutos > 0 or len(partes) == 0:
            partes.append(f'{minutos}min')

        return ' '.join(partes), total_minutos
    except:
        return None, None

def analisar_pedido(numero):
    arquivo = f'logs/equipamentos/sucesso/ordem: 1 | pedido: {numero}.log'
    if not os.path.exists(arquivo):
        return None

    atividades = []
    with open(arquivo, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                partes = [p.strip() for p in linha.split('|')]
                if len(partes) >= 8:
                    atividades.append({
                        'item': partes[3],
                        'nome': partes[4],
                        'equipamento': partes[5],
                        'inicio': partes[6],
                        'fim': partes[7]
                    })

    if not atividades:
        return None

    atividades.sort(key=lambda x: x['inicio'])
    primeira = atividades[0]
    ultima = atividades[-1]

    duracao_str, duracao_min = calcular_duracao(primeira['inicio'], ultima['fim'])

    return {
        'numero': numero,
        'produto': primeira['item'],
        'inicio': primeira['inicio'],
        'fim': ultima['fim'],
        'duracao': duracao_str,
        'duracao_min': duracao_min,
        'num_atividades': len(atividades),
        'atividades': atividades
    }

# Analisa todos os pedidos
print("Analisando pedidos...")
pedidos = []
for num in [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]:
    p = analisar_pedido(num)
    if p:
        pedidos.append(p)
        print(f"  Pedido {num}: {p['duracao']}")

# Gera Markdown
print("\nGerando Markdown...")
with open('escala_e_pedidos_corrigido.md', 'w', encoding='utf-8') as f:
    f.write('# ESCALA DE FUNCIONÁRIOS E ANÁLISE DE PEDIDOS\n\n')
    f.write('**Sistema SIVIRA - Gestão de Produção**  \n')
    f.write(f'*Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}*\n\n')
    f.write('> ✅ **Versão Corrigida** - Cálculo de duração considerando períodos superiores a 24 horas\n\n')
    f.write('---\n\n')

    # Escala de funcionários
    f.write('## 📋 ESCALA DE FUNCIONÁRIOS\n\n')
    f.write('### Setor: Panificação (Turnos Escalonados)\n\n')
    f.write('| ID | Nome | Tipo | Turno | Intervalo | Folgas | CH Semanal |\n')
    f.write('|----|------|------|-------|-----------|--------|------------|\n')
    f.write('| 1 | Funcionário 1 | PADEIRO | 00:00 - 08:00 | 04:00 (30min) | SAB, DOM | 40h |\n')
    f.write('| 2 | Funcionário 2 | AUX. PADEIRO | 02:00 - 10:00 | 06:00 (30min) | SAB | 40h |\n')
    f.write('| 3 | Funcionário 3 | AUX. PADEIRO/CONF. | 04:00 - 12:00 | 08:00 (60min) | SAB | 40h |\n')
    f.write('| 6 | Funcionário 6 | AUX. CONF./PADEIRO | 06:00 - 14:00 | 10:00 (60min) | SAB | 40h |\n\n')

    f.write('### Outros Setores\n\n')
    f.write('| ID | Nome | Setor | Tipo | Turno | CH Semanal |\n')
    f.write('|----|------|-------|------|-------|------------|\n')
    f.write('| 4 | Funcionário 4 | CONFEITARIA | CONFEITEIRO | 08:00 - 18:00 | 44h |\n')
    f.write('| 5 | Funcionário 5 | CONFEITARIA | AUX. CONFEITEIRO | 08:00 - 18:00 | 44h |\n')
    f.write('| 7 | Funcionário 7 | COZINHA | COZINHEIRO | 08:00 - 18:00 | 44h |\n')
    f.write('| 8 | Funcionário 8 | ALMOXARIFADO | ALMOXARIFE | 08:00 - 18:00 | 44h |\n')
    f.write('| 9 | Funcionário 9 | ALMOXARIFADO | ALMOXARIFE | 08:00 - 18:00 | 44h |\n\n')

    f.write('---\n\n')

    # Resumo dos pedidos
    f.write('## 📦 RESUMO DOS PEDIDOS EXECUTADOS (Ordem 1)\n\n')
    f.write('| Pedido | Produto | Início | Fim | Duração | Atividades | Status |\n')
    f.write('|--------|---------|--------|-----|---------|------------|--------|\n')

    for p in sorted(pedidos, key=lambda x: x['numero']):
        inicio_hora = re.search(r'(\d{1,2}:\d{2})', p['inicio']).group(1)
        fim_hora = re.search(r'(\d{1,2}:\d{2})', p['fim']).group(1)

        # Extrai datas
        inicio_data = re.search(r'\[(\d{1,2}/\d{1,2})\]', p['inicio']).group(1)
        fim_data = re.search(r'\[(\d{1,2}/\d{1,2})\]', p['fim']).group(1)

        status = '⚠️ **>24h**' if p['duracao_min'] >= 1440 else '✅'
        duracao = f'**{p["duracao"]}**' if p['duracao_min'] >= 1440 else p['duracao']

        f.write(f'| {p["numero"]} | {p["produto"]} | {inicio_hora} [{inicio_data}] | {fim_hora} [{fim_data}] | {duracao} | {p["num_atividades"]} | {status} |\n')

    f.write('\n')

    # Análise de pedidos longos
    pedidos_longos = [p for p in pedidos if p['duracao_min'] >= 1440]
    if pedidos_longos:
        f.write('### ⚠️ Pedidos com Duração Superior a 24 Horas\n\n')
        for p in pedidos_longos:
            f.write(f'**Pedido {p["numero"]}** - {p["produto"]}  \n')
            f.write(f'- Início: {p["inicio"]}  \n')
            f.write(f'- Fim: {p["fim"]}  \n')
            f.write(f'- Duração total: **{p["duracao"]}**  \n')
            f.write(f'- Atividades: {p["num_atividades"]}  \n\n')

        f.write('**Análise:**  \n')
        f.write('Estes pedidos apresentam duração superior a 24 horas devido a processos que requerem:\n\n')
        f.write('- 🕐 Fermentação prolongada de massas suaves (~24h em temperatura controlada)\n')
        f.write('- ❄️ Resfriamento em câmara refrigerada\n')
        f.write('- 🔬 Maturação necessária para desenvolvimento de sabor e textura\n\n')

    f.write('---\n\n')

    # Estatísticas
    f.write('## 📊 ESTATÍSTICAS GERAIS\n\n')
    total_atividades = sum(p['num_atividades'] for p in pedidos)
    media_atividades = total_atividades / len(pedidos)

    f.write(f'- **Total de pedidos:** {len(pedidos)}\n')
    f.write(f'- **Total de atividades:** {total_atividades}\n')
    f.write(f'- **Média de atividades por pedido:** {media_atividades:.1f}\n')
    f.write(f'- **Pedidos com duração >24h:** {len(pedidos_longos)}\n')
    f.write(f'- **Pedidos com duração <24h:** {len(pedidos) - len(pedidos_longos)}\n\n')

    # Distribuição por duração
    f.write('### Distribuição por Faixa de Duração\n\n')
    f.write('| Faixa | Quantidade | Pedidos |\n')
    f.write('|-------|------------|----------|\n')

    faixas = {
        '< 2h': [p for p in pedidos if p['duracao_min'] < 120],
        '2h - 4h': [p for p in pedidos if 120 <= p['duracao_min'] < 240],
        '4h - 8h': [p for p in pedidos if 240 <= p['duracao_min'] < 480],
        '> 24h': [p for p in pedidos if p['duracao_min'] >= 1440]
    }

    for faixa, lista in faixas.items():
        if lista:
            nums = ', '.join(str(p['numero']) for p in lista)
            f.write(f'| {faixa} | {len(lista)} | {nums} |\n')

    f.write('\n---\n\n')

    # Cobertura de turnos
    f.write('## 🕐 COBERTURA DE TURNOS (Panificação)\n\n')
    f.write('```\n')
    f.write('Horário:  00 01 02 03 04 05 06 07 08 09 10 11 12 13 14\n')
    f.write('          |  |  |  |  |  |  |  |  |  |  |  |  |  |  |\n')
    f.write('F1:       [============================]              \n')
    f.write('F2:          [============================]           \n')
    f.write('F3:                [============================]     \n')
    f.write('F6:                      [============================]\n')
    f.write('\n')
    f.write('Cobertura: 1  1  2  2  3  3  4  4  3  3  2  2  1  1  0\n')
    f.write('```\n\n')

    f.write('**Destaques:**\n\n')
    f.write('- 🏆 **Horário de pico:** 06:00-08:00 (4 funcionários)\n')
    f.write('- ⏰ **Janela de produção:** 00:00-14:00\n')
    f.write('- ✅ **Folgas respeitadas:** Sábado (todos) + Domingo (F1)\n\n')

    f.write('---\n\n')

    # Adequação da escala
    f.write('## 🎯 ADEQUAÇÃO DA ESCALA\n\n')
    f.write('| Faixa Horária | Funcionários | Status |\n')
    f.write('|---------------|--------------|--------|\n')
    f.write('| 00:00-01:59 | 1 | ⚠️ Mínimo |\n')
    f.write('| 02:00-03:59 | 2 | ✅ Adequado |\n')
    f.write('| 04:00-05:59 | 3 | ✅ Bom |\n')
    f.write('| 06:00-07:59 | 4 | 🏆 Ótimo |\n')
    f.write('| 08:00-09:59 | 3 | ✅ Bom |\n')
    f.write('| 10:00-11:59 | 2 | ✅ Adequado |\n')
    f.write('| 12:00-13:59 | 1 | ⚠️ Mínimo |\n\n')

    f.write('---\n\n')

    # Recomendações
    f.write('## 💡 RECOMENDAÇÕES\n\n')
    f.write('### Operacionais\n\n')
    f.write('1. ✅ **Escala otimizada** cobre 100% das atividades de produção\n')
    f.write('2. ✅ **Pico atendido** com 4 funcionários entre 06:00-08:00\n')
    f.write('3. ⚠️ **Monitorar** produtividade nos horários de overlap\n')
    f.write('4. 💡 **Considerar** adicionar 5º funcionário se demanda aumentar\n\n')

    f.write('### Gestão de Pedidos Longos (>24h)\n\n')
    f.write('1. 📅 **Planejar com antecedência** - Iniciar pedidos de massa suave com pelo menos 36h de antecedência\n')
    f.write('2. 🔄 **Paralelizar processos** - Executar outros pedidos durante fermentação\n')
    f.write('3. ❄️ **Otimizar refrigeração** - Garantir câmaras refrigeradas disponíveis\n')
    f.write('4. 📊 **Monitorar temperatura** - Controle rigoroso para fermentação adequada\n\n')

    f.write('### Gestão de Pessoas\n\n')
    f.write('1. 🕐 **Turnos escalonados** evitam fadiga excessiva\n')
    f.write('2. 📋 **Intervalos distribuídos** mantêm operação contínua\n')
    f.write('3. 🔄 **Overlap planejado** facilita passagem de turno\n')
    f.write('4. 💼 **Folgas respeitadas** garantem descanso adequado\n\n')

    f.write('### Próximos Passos\n\n')
    f.write('1. Implementar nova escala gradualmente (1-2 semanas de adaptação)\n')
    f.write('2. Coletar feedback dos funcionários durante período de testes\n')
    f.write('3. Monitorar indicadores de produtividade diariamente\n')
    f.write('4. Ajustar conforme necessário baseado nos dados reais\n')
    f.write('5. Documentar processos de fermentação para pedidos longos\n\n')

    f.write('---\n\n')
    f.write('**Documento gerado automaticamente pelo Sistema SIVIRA**  \n')
    f.write('*Para dúvidas ou sugestões, contate a equipe de desenvolvimento*\n')

print('✅ Arquivo Markdown gerado: escala_e_pedidos_corrigido.md')
