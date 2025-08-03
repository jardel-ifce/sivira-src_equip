#!/usr/bin/env python3
"""
TESTE DEFINITIVO - BUG MASSA CROCANTE
=====================================
Este script testa duas situações para identificar exatamente onde está o bug:
1. COM gestor_almoxarifado (como no menu - bug presente)
2. SEM gestor_almoxarifado (como no script - funciona?)
"""

import sys
import os
from datetime import datetime, timedelta
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_todos_os_logs
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from enums.producao.tipo_item import TipoItem

def configurar_almoxarifado():
    """Configura almoxarifado com massa_crocante = 0"""
    print("🔧 Configurando almoxarifado...")
    
    # Carregar itens
    itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
    
    # Limpar dados anteriores
    apagar_todas_as_comandas()
    limpar_todos_os_logs()
    
    # Inicializar almoxarifado
    almoxarifado = Almoxarifado()
    for item in itens:
        almoxarifado.adicionar_item(item)
    
    # Criar gestor
    gestor = GestorAlmoxarifado(almoxarifado)
    
    # Configurar massa_crocante = 0 (reproduzir cenário do menu)
    massa_crocante = gestor.obter_item_por_id(2001)
    if massa_crocante:
        massa_crocante.estoque_atual = 0
        print(f"   ✅ Massa crocante configurada: estoque = {massa_crocante.estoque_atual}")
    else:
        print("   ❌ Massa crocante não encontrada!")
    
    return almoxarifado, gestor

def executar_teste_com_gestor(almoxarifado, gestor):
    """TESTE 1: COM gestor_almoxarifado (cenário do menu)"""
    print("\n" + "="*60)
    print("🧪 TESTE 1: COM GESTOR_ALMOXARIFADO (cenário do menu)")
    print("="*60)
    
    try:
        inicio_jornada = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        fim_jornada = inicio_jornada + timedelta(hours=10)
        
        pedido = PedidoDeProducao(
            id_ordem=1,
            id_pedido=1,
            id_produto=1001,  # pão francês
            tipo_item=TipoItem.PRODUTO,
            quantidade=100,
            inicio_jornada=inicio_jornada,
            fim_jornada=fim_jornada,
            todos_funcionarios=funcionarios_disponiveis,
            gestor_almoxarifado=gestor  # ✅ COM GESTOR (como no menu)
        )
        
        print("🔄 Montando estrutura...")
        pedido.montar_estrutura()
        
        print("🔄 Criando atividades modulares...")
        pedido.criar_atividades_modulares_necessarias()
        
        # Verificar se foi criada atividade para massa_crocante
        atividades_massa_crocante = []
        for atividade in pedido.atividades_modulares:
            if hasattr(atividade, 'id_item') and atividade.id_item == 2001:
                atividades_massa_crocante.append(atividade)
            # Também verificar por tipo e nome
            if (hasattr(atividade, 'tipo_item') and atividade.tipo_item == TipoItem.SUBPRODUTO and
                hasattr(atividade, 'nome_item') and 'massa_crocante' in atividade.nome_item.lower()):
                atividades_massa_crocante.append(atividade)
        
        print(f"\n📊 RESULTADO TESTE 1:")
        print(f"   Total de atividades: {len(pedido.atividades_modulares)}")
        print(f"   Atividades de massa_crocante: {len(atividades_massa_crocante)}")
        
        if atividades_massa_crocante:
            print("   ✅ MASSA_CROCANTE FOI INCLUÍDA!")
            for atividade in atividades_massa_crocante:
                print(f"       - Atividade {getattr(atividade, 'id_atividade', 'N/A')}: {getattr(atividade, 'nome_atividade', 'N/A')}")
        else:
            print("   ❌ MASSA_CROCANTE NÃO FOI INCLUÍDA! (BUG CONFIRMADO)")
        
        # Debug adicional: mostrar todas as atividades
        print(f"\n🔍 Debug - Todas as atividades criadas:")
        for i, atividade in enumerate(pedido.atividades_modulares):
            print(f"   [{i+1}] ID: {getattr(atividade, 'id_atividade', 'N/A')}, "
                  f"Tipo: {getattr(atividade, 'tipo_item', 'N/A')}, "
                  f"Nome: {getattr(atividade, 'nome_item', 'N/A')}")
        
        return len(atividades_massa_crocante) > 0
        
    except Exception as e:
        print(f"❌ Erro no teste 1: {e}")
        import traceback
        traceback.print_exc()
        return False

def executar_teste_sem_gestor():
    """TESTE 2: SEM gestor_almoxarifado (cenário do script)"""
    print("\n" + "="*60)
    print("🧪 TESTE 2: SEM GESTOR_ALMOXARIFADO (cenário do script)")
    print("="*60)
    
    try:
        inicio_jornada = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        fim_jornada = inicio_jornada + timedelta(hours=10)
        
        pedido = PedidoDeProducao(
            id_ordem=2,
            id_pedido=2,
            id_produto=1001,  # pão francês
            tipo_item=TipoItem.PRODUTO,
            quantidade=100,
            inicio_jornada=inicio_jornada,
            fim_jornada=fim_jornada,
            todos_funcionarios=funcionarios_disponiveis
            # ❌ SEM gestor_almoxarifado (como no script)
        )
        
        print("🔄 Montando estrutura...")
        pedido.montar_estrutura()
        
        print("🔄 Criando atividades modulares...")
        pedido.criar_atividades_modulares_necessarias()
        
        # Verificar se foi criada atividade para massa_crocante
        atividades_massa_crocante = []
        for atividade in pedido.atividades_modulares:
            if hasattr(atividade, 'id_item') and atividade.id_item == 2001:
                atividades_massa_crocante.append(atividade)
            # Também verificar por tipo e nome
            if (hasattr(atividade, 'tipo_item') and atividade.tipo_item == TipoItem.SUBPRODUTO and
                hasattr(atividade, 'nome_item') and 'massa_crocante' in atividade.nome_item.lower()):
                atividades_massa_crocante.append(atividade)
        
        print(f"\n📊 RESULTADO TESTE 2:")
        print(f"   Total de atividades: {len(pedido.atividades_modulares)}")
        print(f"   Atividades de massa_crocante: {len(atividades_massa_crocante)}")
        
        if atividades_massa_crocante:
            print("   ✅ MASSA_CROCANTE FOI INCLUÍDA!")
            for atividade in atividades_massa_crocante:
                print(f"       - Atividade {getattr(atividade, 'id_atividade', 'N/A')}: {getattr(atividade, 'nome_atividade', 'N/A')}")
        else:
            print("   ❌ MASSA_CROCANTE NÃO FOI INCLUÍDA!")
        
        # Debug adicional: mostrar todas as atividades
        print(f"\n🔍 Debug - Todas as atividades criadas:")
        for i, atividade in enumerate(pedido.atividades_modulares):
            print(f"   [{i+1}] ID: {getattr(atividade, 'id_atividade', 'N/A')}, "
                  f"Tipo: {getattr(atividade, 'tipo_item', 'N/A')}, "
                  f"Nome: {getattr(atividade, 'nome_item', 'N/A')}")
        
        return len(atividades_massa_crocante) > 0
        
    except Exception as e:
        print(f"❌ Erro no teste 2: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal - executa ambos os testes"""
    print("🚀 TESTE DEFINITIVO - BUG MASSA CROCANTE")
    print("=" * 50)
    print("Este teste vai comparar dois cenários:")
    print("1. COM gestor_almoxarifado (menu - com bug)")
    print("2. SEM gestor_almoxarifado (script - sem bug?)")
    print()
    
    try:
        # Configurar ambiente
        almoxarifado, gestor = configurar_almoxarifado()
        
        # Executar testes
        resultado_com_gestor = executar_teste_com_gestor(almoxarifado, gestor)
        resultado_sem_gestor = executar_teste_sem_gestor()
        
        # Conclusão
        print("\n" + "="*60)
        print("🎯 CONCLUSÃO FINAL:")
        print("="*60)
        print(f"✅ Teste COM gestor: {'Passou' if resultado_com_gestor else 'FALHOU (bug confirmado)'}")
        print(f"✅ Teste SEM gestor: {'Passou' if resultado_sem_gestor else 'FALHOU'}")
        print()
        
        if not resultado_com_gestor and resultado_sem_gestor:
            print("🎯 BUG CONFIRMADO!")
            print("   - COM gestor: massa_crocante NÃO é produzida (BUG)")
            print("   - SEM gestor: massa_crocante É produzida (correto)")
            print("   - Problema está na lógica de verificação de estoque!")
        elif resultado_com_gestor and resultado_sem_gestor:
            print("🤔 Ambos funcionam - bug pode estar em outro lugar")
        elif not resultado_com_gestor and not resultado_sem_gestor:
            print("😞 Ambos falharam - problema mais profundo")
        else:
            print("🤨 Resultado inesperado")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()