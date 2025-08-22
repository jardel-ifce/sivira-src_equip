#!/usr/bin/env python3
"""
Script para regenerar todos os logs de erro no formato limpo e legível.
Lê os arquivos JSON existentes e recria os logs .log correspondentes.
"""

import os
import json
import glob
from datetime import datetime
from utils.logs.gerenciador_logs import salvar_erro_detalhado

def extrair_ids_do_nome_arquivo(nome_arquivo):
    """Extrai id_ordem e id_pedido do nome do arquivo JSON"""
    # Formato: quantidade_*_1_5_*.json ou timing_*_1_7_*.json
    partes = nome_arquivo.split('_')
    
    # Procurar por padrão de IDs no nome
    for i in range(len(partes) - 1):
        if partes[i].isdigit() and partes[i+1].isdigit():
            return int(partes[i]), int(partes[i+1])
    
    return None, None

def converter_json_para_log_limpo(arquivo_json):
    """Converte um arquivo JSON de erro para o formato de log limpo"""
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Extrair IDs do arquivo
        id_ordem = dados.get('identificacao', {}).get('id_ordem')
        id_pedido = dados.get('identificacao', {}).get('id_pedido')
        
        if not id_ordem or not id_pedido:
            # Tentar extrair do nome do arquivo
            id_ordem, id_pedido = extrair_ids_do_nome_arquivo(os.path.basename(arquivo_json))
            
        if not id_ordem or not id_pedido:
            print(f"⚠️ Não foi possível extrair IDs de {arquivo_json}")
            return False
        
        # Determinar tipo de erro e criar descrição estruturada
        if 'erro_quantidade' in dados:
            tipo_erro = "QUANTIDADE"
            erro = dados['erro_quantidade']
            detalhes = erro.get('details', {})
            
            descricao = {
                'mensagem': erro.get('message', 'Erro de quantidade'),
                'detalhes': {
                    'nome_atividade': dados.get('identificacao', {}).get('nome_atividade', 'N/A'),
                    'quantidade_solicitada': detalhes.get('requested_quantity', 'N/A'),
                    'capacidade_minima': detalhes.get('minimum_capacity', 'N/A'),
                    'diferenca': detalhes.get('deficit', 'N/A'),
                    'tipo_equipamento': detalhes.get('equipment_type', 'N/A'),
                    'equipamentos': []
                },
                'sugestoes': erro.get('suggestions', [])
            }
            
            # Adicionar equipamentos disponíveis
            if 'available_equipment' in detalhes:
                for equip in detalhes['available_equipment']:
                    descricao['detalhes']['equipamentos'].append({
                        'nome': equip.get('nome', 'N/A'),
                        'min': equip.get('capacidade_min', 0),
                        'max': equip.get('capacidade_max', 0)
                    })
                    
        elif 'erro_tempo' in dados:
            tipo_erro = "TEMPO"
            erro = dados['erro_tempo']
            detalhes = erro.get('details', {})
            
            descricao = {
                'mensagem': erro.get('message', 'Conflito de tempo'),
                'detalhes': {},
                'sugestoes': erro.get('suggestions', [])
            }
            
            # Adicionar informações das atividades
            if 'current_activity' in detalhes:
                ativ = detalhes['current_activity']
                descricao['detalhes']['atividade_atual'] = {
                    'nome': ativ.get('name', 'N/A'),
                    'fim': ativ.get('end_time_formatted', 'N/A')
                }
            
            if 'successor_activity' in detalhes:
                ativ = detalhes['successor_activity']
                descricao['detalhes']['atividade_sucessora'] = {
                    'nome': ativ.get('name', 'N/A'),
                    'inicio': ativ.get('start_time_formatted', 'N/A')
                }
            
            if 'timing_violation' in detalhes:
                viol = detalhes['timing_violation']
                descricao['detalhes']['conflito'] = {
                    'tempo_maximo': viol.get('maximum_wait_time_formatted', 'N/A'),
                    'atraso': viol.get('actual_delay_formatted', 'N/A'),
                    'excesso': viol.get('excess_time_formatted', 'N/A')
                }
        else:
            print(f"⚠️ Tipo de erro desconhecido em {arquivo_json}")
            return False
        
        # Salvar log limpo
        salvar_erro_detalhado(id_ordem, id_pedido, tipo_erro, descricao)
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar {arquivo_json}: {e}")
        return False

def regenerar_todos_os_logs():
    """Regenera todos os logs baseados nos JSONs existentes"""
    print("=" * 60)
    print("REGENERAÇÃO DE LOGS EM FORMATO LIMPO")
    print("=" * 60)
    
    pasta_erros = "logs/erros"
    
    # Buscar todos os arquivos JSON de erro
    arquivos_json = glob.glob(f"{pasta_erros}/*.json")
    
    if not arquivos_json:
        print("⚠️ Nenhum arquivo JSON de erro encontrado")
        return
    
    print(f"\n📁 Encontrados {len(arquivos_json)} arquivos JSON para processar")
    
    # Agrupar JSONs por pedido
    pedidos_processados = {}
    
    for arquivo in arquivos_json:
        nome_base = os.path.basename(arquivo)
        
        # Extrair ordem e pedido
        if 'quantidade_' in nome_base:
            # Formato: quantidade_*_1_5_*.json
            partes = nome_base.split('_')
            for i in range(len(partes) - 1):
                if partes[i].isdigit() and partes[i+1].isdigit():
                    chave = f"{partes[i]}_{partes[i+1]}"
                    if chave not in pedidos_processados:
                        pedidos_processados[chave] = []
                    pedidos_processados[chave].append(arquivo)
                    break
                    
        elif 'timing_' in nome_base:
            # Formato: timing_*_1_7_*.json
            partes = nome_base.split('_')
            for i in range(len(partes) - 1):
                if partes[i].isdigit() and partes[i+1].isdigit():
                    chave = f"{partes[i]}_{partes[i+1]}"
                    if chave not in pedidos_processados:
                        pedidos_processados[chave] = []
                    pedidos_processados[chave].append(arquivo)
                    break
    
    print(f"📊 {len(pedidos_processados)} pedidos únicos identificados")
    
    sucesso = 0
    falhas = 0
    
    for chave, arquivos in pedidos_processados.items():
        # Ordenar por timestamp (pegar o mais recente)
        arquivos.sort()
        arquivo_mais_recente = arquivos[-1]
        
        print(f"\n🔄 Processando: {os.path.basename(arquivo_mais_recente)}")
        
        if converter_json_para_log_limpo(arquivo_mais_recente):
            ordem, pedido = chave.split('_')
            print(f"   ✅ Log regenerado: ordem: {ordem} | pedido: {pedido}.log")
            sucesso += 1
        else:
            print(f"   ❌ Falha ao processar")
            falhas += 1
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO DA REGENERAÇÃO")
    print("=" * 60)
    print(f"✅ Logs regenerados com sucesso: {sucesso}")
    print(f"❌ Falhas: {falhas}")
    print(f"📁 Total processado: {sucesso + falhas}")

def visualizar_log_regenerado(id_ordem, id_pedido):
    """Mostra o conteúdo de um log regenerado"""
    arquivo = f"logs/erros/ordem: {id_ordem} | pedido: {id_pedido}.log"
    
    if os.path.exists(arquivo):
        print(f"\n📄 Conteúdo de {arquivo}:")
        print("-" * 60)
        with open(arquivo, 'r', encoding='utf-8') as f:
            print(f.read())
        print("-" * 60)
    else:
        print(f"⚠️ Arquivo {arquivo} não encontrado")

if __name__ == "__main__":
    # Regenerar todos os logs
    regenerar_todos_os_logs()
    
    # Mostrar exemplo de log regenerado
    print("\n" + "=" * 60)
    print("EXEMPLO DE LOG REGENERADO")
    print("=" * 60)
    
    # Mostrar o log do pedido 7 (que tinha problema de tempo)
    visualizar_log_regenerado(1, 7)
    
    print("\n✅ Processo concluído!")
    print("ℹ️ Todos os logs foram regenerados no formato limpo e legível")