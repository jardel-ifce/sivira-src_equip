#!/usr/bin/env python3
"""
Teste final com DEBUG COMPLETO para identificar por que as atividades do creme ainda são criadas:
1. Coleta logs detalhados de verificação de estoque
2. Rastreia decisões de criação de atividades
3. Salva debug completo em arquivo JSON
4. Verifica especificamente o creme de queijo (ID 2010)
"""

import sys
import os
import json
from datetime import datetime, timedelta
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from enums.producao.tipo_item import TipoItem

def configurar_creme_estocado_com_estoque():
    """
    🔧 Configura o creme de queijo como ESTOCADO com 50.000g de estoque.
    """
    print("🔧 Configurando creme de queijo...")
    
    itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
    
    # Encontrar e modificar o creme de queijo
    creme_encontrado = False
    for item in itens:
        if item.id_item == 2010:  # creme_de_queijo
            print(f"   📦 Creme encontrado: {item.descricao}")
            print(f"   🏷️ Política original: {item.politica_producao.value}")
            print(f"   📊 Estoque original: {item.estoque_atual}")
            
            # Verificar se já está ESTOCADO
            from enums.producao.politica_producao import PoliticaProducao
            if item.politica_producao != PoliticaProducao.ESTOCADO:
                item.politica_producao = PoliticaProducao.ESTOCADO
                print(f"   🔄 Política alterada para: {item.politica_producao.value}")
            
            # Definir estoque alto
            item.estoque_atual = 50000
            print(f"   📈 Estoque definido para: {item.estoque_atual}")
            creme_encontrado = True
            break
    
    if not creme_encontrado:
        print("   ❌ ERRO: Creme de queijo não encontrado!")
        return None, None
    
    # Criar almoxarifado
    almoxarifado = Almoxarifado()
    for item in itens:
        almoxarifado.adicionar_item(item)
    
    gestor = GestorAlmoxarifado(almoxarifado)
    
    # Verificar se a configuração funcionou
    creme_item = gestor.obter_item_por_id(2010)
    print(f"   ✅ Verificação final:")
    print(f"      Política: {creme_item.politica_producao.value}")
    print(f"      Estoque: {creme_item.estoque_atual}")
    
    return gestor, creme_item

def analisar_debug_creme(arquivo_debug):
    """
    🔍 Analisa os eventos de debug específicos do creme de queijo.
    """
    try:
        with open(arquivo_debug, 'r', encoding='utf-8') as f:
            debug_data = json.load(f)
        
        eventos_creme = [
            evento for evento in debug_data.get('eventos', [])
            if evento['item_id'] == 2010 or 'creme' in evento['item_nome'].lower()
        ]
        
        print(f"\n🔍 ANÁLISE DO DEBUG - CREME DE QUEIJO:")
        print("=" * 60)
        print(f"📊 Total de eventos relacionados ao creme: {len(eventos_creme)}")
        
        # Agrupar por categoria
        por_categoria = {}
        for evento in eventos_creme:
            categoria = evento['categoria']
            if categoria not in por_categoria:
                por_categoria[categoria] = []
            por_categoria[categoria].append(evento)
        
        # Exibir por categoria
        for categoria, eventos in por_categoria.items():
            print(f"\n📂 {categoria}: {len(eventos)} evento(s)")
            for i, evento in enumerate(eventos):
                print(f"   {i+1}. {evento['timestamp']}")
                print(f"      📝 Dados: {evento['dados']}")
        
        # Verificar pontos críticos
        print(f"\n🎯 PONTOS CRÍTICOS:")
        
        # 1. Verificação de estoque
        verificacoes_estoque = por_categoria.get('DECISAO_ESTOQUE', [])
        if verificacoes_estoque:
            for verif in verificacoes_estoque:
                dados = verif['dados']
                print(f"   📦 Verificação de estoque:")
                print(f"      Política: {dados.get('politica')}")
                print(f"      Estoque atual: {dados.get('estoque_atual')}")
                print(f"      Necessário: {dados.get('quantidade_necessaria')}")
                print(f"      Suficiente: {dados.get('tem_estoque_suficiente')}")
                print(f"      Decisão: {dados.get('decisao')}")
        
        # 2. Decisão de produção
        decisoes_producao = por_categoria.get('DECISAO_PRODUCAO', [])
        if decisoes_producao:
            for decisao in decisoes_producao:
                dados = decisao['dados']
                print(f"   🏭 Decisão de produção:")
                print(f"      Deve produzir: {dados.get('deve_produzir')}")
                print(f"      Motivo: {dados.get('motivo')}")
        
        # 3. Atividades criadas
        atividades_criadas = por_categoria.get('ATIVIDADE_CRIADA', [])
        print(f"   🔧 Atividades criadas: {len(atividades_criadas)}")
        
        # 4. Produção cancelada
        producao_cancelada = por_categoria.get('PRODUCAO_CANCELADA', [])
        if producao_cancelada:
            print(f"   ⏹️ Produção cancelada: {len(producao_cancelada)}")
            for cancelamento in producao_cancelada:
                print(f"      Motivo: {cancelamento['dados'].get('motivo')}")
        else:
            print(f"   ❌ PROBLEMA: Produção NÃO foi cancelada!")
        
        return por_categoria
        
    except Exception as e:
        print(f"❌ Erro ao analisar debug: {e}")
        return None

def testar_com_debug_completo():
    """
    🧪 Teste completo com debug detalhado.
    """
    print("🔍 TESTE COMPLETO COM DEBUG - CREME DE QUEIJO")
    print("=" * 70)
    
    # 1. Configurar ambiente
    gestor, creme_item = configurar_creme_estocado_com_estoque()
    if not gestor or not creme_item:
        print("❌ Falha na configuração!")
        return False
    
    # 2. Criar pedido
    print(f"\n📋 Criando pedido 777...")
    data_fim = datetime(2025, 6, 26, 7, 0)
    pedido = PedidoDeProducao(
        id_ordem=1,
        id_pedido=777,
        id_produto=1005,
        tipo_item=TipoItem.PRODUTO,
        quantidade=20,
        inicio_jornada=data_fim - timedelta(hours=12),
        fim_jornada=data_fim,
        todos_funcionarios=funcionarios_disponiveis,
        gestor_almoxarifado=gestor
    )
    
    try:
        # 3. Executar com debug
        print(f"🔄 Executando pedido...")
        pedido.montar_estrutura()
        pedido.criar_atividades_modulares_necessarias()
        
        # 4. Salvar logs ANTES da execução das atividades
        arquivo_debug = pedido.salvar_debug_logs()
        print(f"💾 Debug inicial salvo em: {arquivo_debug}")
        
        # 5. Analisar debug
        debug_analysis = analisar_debug_creme(arquivo_debug)
        
        # 6. Verificar se atividades do creme foram criadas
        atividades_creme = [
            a for a in pedido.atividades_modulares
            if hasattr(a, 'nome_item') and 'creme' in a.nome_item.lower()
        ]
        
        print(f"\n📊 RESULTADO DA ANÁLISE:")
        print(f"   🔢 Atividades de creme criadas: {len(atividades_creme)}")
        
        if len(atividades_creme) == 0:
            print(f"   ✅ SUCESSO: Nenhuma atividade de creme criada (estoque suficiente)!")
            
            # Continuar execução para ver produto
            pedido.executar_atividades_em_ordem()
            
            # Salvar debug final
            arquivo_debug_final = pedido.salvar_debug_logs()
            print(f"💾 Debug final salvo em: {arquivo_debug_final}")
            
            return True
            
        else:
            print(f"   ❌ PROBLEMA: {len(atividades_creme)} atividades de creme criadas mesmo com estoque!")
            
            print(f"\n🔧 Atividades criadas:")
            for i, atividade in enumerate(atividades_creme):
                print(f"   {i+1}. ID {atividade.id_atividade} - {atividade.nome_atividade}")
            
            return False
    
    except Exception as e:
        print(f"❌ ERRO na execução: {e}")
        
        # Salvar logs mesmo com erro
        try:
            arquivo_debug_erro = pedido.salvar_debug_logs()
            print(f"💾 Debug de erro salvo em: {arquivo_debug_erro}")
            analisar_debug_creme(arquivo_debug_erro)
        except:
            pass
        
        return False

def main():
    """
    🚀 Função principal do teste.
    """
    print("🧪 TESTE DE DEBUG COMPLETO - IDENTIFICAR PROBLEMA DO CREME")
    print("=" * 70)
    
    try:
        sucesso = testar_com_debug_completo()
        
        if sucesso:
            print(f"\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
            print(f"✅ O creme de queijo não foi produzido (usando estoque)")
        else:
            print(f"\n⚠️ TESTE IDENTIFICOU PROBLEMA!")
            print(f"❌ O creme de queijo foi produzido mesmo com estoque suficiente")
            print(f"🔍 Analise os arquivos de debug gerados para identificar a causa")
        
        return sucesso
        
    except Exception as e:
        print(f"❌ ERRO GERAL no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = main()
    if not sucesso:
        print(f"\n💡 DICA: Verifique os arquivos debug_pedido_producao_*.json gerados")
        sys.exit(1)
    else:
        print(f"\n✅ Todos os testes passaram!")
        sys.exit(0)