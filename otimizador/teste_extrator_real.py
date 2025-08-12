"""
Teste do Extrator com Dados Reais da Padaria
===========================================

Este arquivo testa o ExtratorDadosPedidos com os pedidos reais da padaria.
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path para importar as classes do seu projeto
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from enums.producao.tipo_item import TipoItem

# Importa o extrator
from otimizador.extrator_dados_pedidos import ExtratorDadosPedidos


def criar_pedidos_teste():
    """
    Cria os mesmos 4 pedidos da padaria que você usa no sistema atual
    """
    print("🔄 Criando pedidos de teste...")
    
    # Inicializa almoxarifado
    itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
    almoxarifado = Almoxarifado()
    for item in itens:
        almoxarifado.adicionar_item(item)
    gestor_almoxarifado = GestorAlmoxarifado(almoxarifado)
    
    # Configurações dos pedidos (mesmo do producao_paes.py)
    data_base = datetime(2025, 6, 26)
    configuracoes_pedidos = [
        {"produto": "Pão Francês", "id_produto": 1001, "quantidade": 450, "hora_fim": 7},
        {"produto": "Pão Hambúrguer", "id_produto": 1002, "quantidade": 120, "hora_fim": 7},
        {"produto": "Pão de Forma", "id_produto": 1003, "quantidade": 70, "hora_fim": 7},
        {"produto": "Pão Baguete", "id_produto": 1004, "quantidade": 50, "hora_fim": 7},
    ]
    
    pedidos = []
    
    for i, config in enumerate(configuracoes_pedidos, 1):
        try:
            # Calcular datas
            fim_jornada = data_base.replace(hour=config['hora_fim'], minute=0, second=0, microsecond=0)
            inicio_jornada = fim_jornada - timedelta(days=3)
            
            # Criar pedido
            pedido = PedidoDeProducao(
                id_ordem=1,
                id_pedido=i,
                id_produto=config['id_produto'],
                tipo_item=TipoItem.PRODUTO,
                quantidade=config['quantidade'],
                inicio_jornada=inicio_jornada,
                fim_jornada=fim_jornada,
                todos_funcionarios=funcionarios_disponiveis,
                gestor_almoxarifado=gestor_almoxarifado
            )
            
            # Monta estrutura (isso carrega as atividades)
            pedido.montar_estrutura()
            pedido.criar_atividades_modulares_necessarias()
            
            pedidos.append(pedido)
            print(f"✅ Pedido {i} criado: {config['produto']} ({config['quantidade']} uni)")
            
        except Exception as e:
            print(f"❌ Erro ao criar pedido {i}: {e}")
    
    print(f"📊 Total de pedidos criados: {len(pedidos)}")
    return pedidos


def testar_extracao_real():
    """
    Função principal que testa a extração com dados reais
    """
    print("🚀 TESTANDO EXTRATOR COM DADOS REAIS DA PADARIA")
    print("="*60)
    
    try:
        # 1. Cria pedidos reais
        pedidos = criar_pedidos_teste()
        
        if not pedidos:
            print("❌ Nenhum pedido foi criado. Verifique a configuração.")
            return
        
        # 2. Testa extração
        print("\n🔄 Iniciando extração de dados...")
        extrator = ExtratorDadosPedidos()
        dados_extraidos = extrator.extrair_dados(pedidos)
        
        # 3. Mostra resultados
        extrator.imprimir_resumo()
        
        # 4. Análise detalhada
        print("\n🔍 ANÁLISE DETALHADA:")
        print("-"*40)
        
        for i, pedido_data in enumerate(dados_extraidos):
            print(f"\n📋 Pedido {pedido_data.id_pedido}: {pedido_data.nome_produto}")
            print(f"   Quantidade: {pedido_data.quantidade}")
            print(f"   Duração total: {pedido_data.duracao_total}")
            print(f"   Janela: {pedido_data.inicio_jornada.strftime('%d/%m %H:%M')} → {pedido_data.fim_jornada.strftime('%d/%m %H:%M')}")
            print(f"   Atividades ({len(pedido_data.atividades)}):")
            
            for j, atividade in enumerate(pedido_data.atividades):
                equipamentos_str = ", ".join(atividade.equipamentos_necessarios[:3])
                if len(atividade.equipamentos_necessarios) > 3:
                    equipamentos_str += f" (+{len(atividade.equipamentos_necessarios)-3} mais)"
                
                print(f"     {j+1}. {atividade.nome} ({atividade.duracao})")
                print(f"        Equipamentos: {equipamentos_str}")
                print(f"        Tempo máx espera: {atividade.tempo_maximo_espera}")
        
        # 5. Validações
        print(f"\n✅ EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"   • {len(dados_extraidos)} pedidos extraídos")
        print(f"   • {sum(len(p.atividades) for p in dados_extraidos)} atividades totais")
        print(f"   • {len(extrator.equipamentos_unicos)} equipamentos únicos identificados")
        
        return dados_extraidos
        
    except Exception as e:
        print(f"❌ ERRO DURANTE TESTE: {e}")
        import traceback
        traceback.print_exc()
        return None


def verificar_consistencia_dados(dados_extraidos):
    """
    Verifica se os dados extraídos estão consistentes
    """
    print("\n🔍 VERIFICANDO CONSISTÊNCIA DOS DADOS...")
    
    problemas = []
    
    for pedido_data in dados_extraidos:
        # Verifica se tem atividades
        if not pedido_data.atividades:
            problemas.append(f"Pedido {pedido_data.id_pedido}: sem atividades")
        
        # Verifica durações
        if pedido_data.duracao_total <= timedelta(0):
            problemas.append(f"Pedido {pedido_data.id_pedido}: duração total inválida")
        
        # Verifica janela temporal
        janela = pedido_data.fim_jornada - pedido_data.inicio_jornada
        if pedido_data.duracao_total > janela:
            problemas.append(f"Pedido {pedido_data.id_pedido}: duração maior que janela temporal")
        
        # Verifica atividades
        for atividade in pedido_data.atividades:
            if not atividade.equipamentos_necessarios:
                problemas.append(f"Atividade {atividade.id_atividade}: sem equipamentos")
            
            if atividade.duracao <= timedelta(0):
                problemas.append(f"Atividade {atividade.id_atividade}: duração inválida")
    
    if problemas:
        print("⚠️ PROBLEMAS ENCONTRADOS:")
        for problema in problemas:
            print(f"   • {problema}")
    else:
        print("✅ Todos os dados estão consistentes!")
    
    return len(problemas) == 0


if __name__ == "__main__":
    dados = testar_extracao_real()
    
    if dados:
        print("\n" + "="*60)
        verificar_consistencia_dados(dados)
        print("="*60)
    else:
        print("\n❌ Teste falhou - não foi possível extrair dados")