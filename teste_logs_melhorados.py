#!/usr/bin/env python3
"""
Script de teste para verificar os logs melhorados.
Testa a nova funcionalidade de gerar logs legíveis a partir dos JSONs.
"""

import os
import sys
from datetime import datetime
from utils.logs.gerenciador_logs import salvar_erro_detalhado, salvar_erro_em_log, _gerar_descricao_erro_legivel

def testar_log_quantidade():
    """Testa log de erro de quantidade"""
    print("🧪 Testando log de erro de QUANTIDADE...")
    
    descricao = {
        'mensagem': 'Quantidade 2500g está abaixo da capacidade mínima (3000g) para equipamentos do tipo MISTURADORAS',
        'detalhes': {
            'nome_atividade': 'mistura_de_massas_suaves',
            'quantidade_solicitada': 2500,
            'capacidade_minima': 3000,
            'diferenca': 500,
            'tipo_equipamento': 'MISTURADORAS',
            'equipamentos': [
                {'nome': 'Masseira 1', 'min': 3000, 'max': 50000},
                {'nome': 'Masseira 2', 'min': 3000, 'max': 30000}
            ]
        },
        'sugestoes': [
            'Aumentar a quantidade para pelo menos 3000g',
            'Verificar se há equipamentos com capacidade menor disponíveis',
            'Considerar produção em lotes maiores'
        ]
    }
    
    salvar_erro_detalhado(99, 1, "QUANTIDADE", descricao)
    print("✅ Log de quantidade salvo em: logs/erros/ordem: 99 | pedido: 1.log")

def testar_log_tempo():
    """Testa log de erro de tempo"""
    print("\n🧪 Testando log de erro de TEMPO...")
    
    descricao = {
        'mensagem': 'Tempo máximo de espera excedido entre atividades. Atraso de 11 minutos excede o máximo permitido.',
        'detalhes': {
            'atividade_atual': {
                'nome': 'corte_de_pestana_para_paes_baguete',
                'fim': '26/06 08:26:00'
            },
            'atividade_sucessora': {
                'nome': 'coccao_de_paes_baguete',
                'inicio': '26/06 08:37:00'
            },
            'conflito': {
                'tempo_maximo': '0:00:00',
                'atraso': '0:11:00',
                'excesso': '0:11:00'
            }
        },
        'sugestoes': [
            'Verificar disponibilidade de equipamentos',
            'Ajustar sequenciamento das atividades',
            'Considerar recursos alternativos'
        ]
    }
    
    salvar_erro_detalhado(99, 2, "TEMPO", descricao)
    print("✅ Log de tempo salvo em: logs/erros/ordem: 99 | pedido: 2.log")

def testar_leitura_json_existente():
    """Testa leitura de um JSON existente para gerar log"""
    print("\n🧪 Testando leitura de JSON existente...")
    
    # Simula uma exceção para teste
    class ErroTeste(Exception):
        pass
    
    # Tenta ler um JSON existente (pedido 5)
    erro = ErroTeste("Teste de leitura de JSON")
    descricao = _gerar_descricao_erro_legivel(1, 5, erro)
    
    if descricao:
        print("✅ Descrição gerada a partir do JSON:")
        print("-" * 40)
        print(descricao[:500] + "..." if len(descricao) > 500 else descricao)
        print("-" * 40)
    else:
        print("⚠️ Nenhuma descrição gerada (JSON pode não existir)")

def limpar_logs_teste():
    """Limpa os logs de teste"""
    print("\n🧹 Limpando logs de teste...")
    
    arquivos = [
        "logs/erros/ordem: 99 | pedido: 1.log",
        "logs/erros/ordem: 99 | pedido: 2.log"
    ]
    
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            os.remove(arquivo)
            print(f"   • Removido: {arquivo}")

def main():
    print("=" * 60)
    print("TESTE DO SISTEMA DE LOGS MELHORADOS")
    print("=" * 60)
    
    # Executar testes
    testar_log_quantidade()
    testar_log_tempo()
    testar_leitura_json_existente()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)
    
    # Verificar se os arquivos foram criados
    arquivos_esperados = [
        "logs/erros/ordem: 99 | pedido: 1.log",
        "logs/erros/ordem: 99 | pedido: 2.log"
    ]
    
    for arquivo in arquivos_esperados:
        if os.path.exists(arquivo):
            print(f"✅ {arquivo} criado com sucesso")
            # Mostrar primeiras linhas do arquivo
            with open(arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()[:15]
                print(f"\n   Prévia do conteúdo:")
                for linha in linhas:
                    print(f"   {linha.rstrip()}")
        else:
            print(f"❌ {arquivo} não foi criado")
    
    # Perguntar se deseja limpar
    resposta = input("\n🗑️ Deseja limpar os logs de teste? (s/n): ")
    if resposta.lower() == 's':
        limpar_logs_teste()
        print("✅ Logs de teste removidos")
    else:
        print("ℹ️ Logs de teste mantidos para análise")

if __name__ == "__main__":
    main()