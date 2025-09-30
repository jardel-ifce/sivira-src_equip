#!/usr/bin/env python3
"""
📅 Script de Demonstração: Visualização de Agenda de Equipamentos
================================================================

Script independente que demonstra como visualizar a agenda dos equipamentos 
após executar um processo de produção de coxinhas.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from datetime import datetime, timedelta
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestores.almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_logs_inicializacao
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from enums.producao.tipo_item import TipoItem
from enums.equipamentos.tipo_equipamento import TipoEquipamento

# Importações para visualização de agenda
from menu.integrador_equipamentos import IntegradorEquipamentos


def mostrar_agenda_todos_equipamentos():
    """
    Mostra a agenda de todos os equipamentos disponíveis no sistema.
    """
    print("\n📅 AGENDA COMPLETA DE TODOS OS EQUIPAMENTOS")
    print("=" * 60)
    
    try:
        # Inicializar integrador
        integrador = IntegradorEquipamentos()
        
        if not integrador.sistema_disponivel():
            print("⚠️ Sistema de equipamentos não disponível no momento")
            return
            
        # Obter lista de equipamentos por tipo
        equipamentos_por_tipo = integrador.listar_equipamentos_disponiveis()
        
        if not equipamentos_por_tipo:
            print("🔭 Nenhum equipamento encontrado no sistema")
            return
            
        total_equipamentos = sum(len(eqs) for eqs in equipamentos_por_tipo.values())
        print(f"🏭 Sistema encontrou {total_equipamentos} equipamentos em {len(equipamentos_por_tipo)} categorias")
        print()
        
        # Mostrar agenda por tipo de equipamento
        for tipo_equipamento, lista_equipamentos in equipamentos_por_tipo.items():
            print(f"📋 {tipo_equipamento.upper()}")
            print("-" * (len(tipo_equipamento) + 2))
            
            for nome_equipamento in lista_equipamentos:
                print(f"\n🔧 {nome_equipamento}:")
                try:
                    agenda = integrador.obter_agenda_equipamento_especifico(nome_equipamento)
                    
                    if agenda and not any(erro in agenda.lower() for erro in ['erro', 'não encontrado', 'não possui']):
                        if agenda.strip():
                            # Se retornou conteúdo na agenda
                            linhas = agenda.strip().split('\n')
                            for linha in linhas:
                                print(f"   {linha}")
                        else:
                            # Agenda foi executada via logger
                            print("   ✅ Agenda executada (verifique logs para detalhes)")
                    else:
                        print("   ⚠️ Sem agenda disponível ou equipamento inativo")
                        
                except Exception as e:
                    print(f"   ❌ Erro ao obter agenda: {e}")
            
            print()
            
    except Exception as e:
        print(f"❌ Erro ao acessar sistema de equipamentos: {e}")


def executar_pedido_simples():
    """
    Executa um pedido simples de coxinhas para gerar dados na agenda.
    """
    print("🍟 EXECUTANDO PEDIDO SIMPLES PARA GERAR AGENDA")
    print("=" * 50)
    
    # Limpeza inicial
    print("🧹 Limpando ambiente...")
    limpar_logs_inicializacao()
    apagar_todas_as_comandas()
    print("✅ Ambiente limpo\n")
    
    # Configurar almoxarifado
    print("📦 Inicializando almoxarifado...")
    itens_almoxarifado = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
    almoxarifado = Almoxarifado()
    
    # Adicionar itens ao almoxarifado
    for item in itens_almoxarifado:
        almoxarifado.adicionar_item(item)
        
    gestor_almoxarifado = GestorAlmoxarifado(almoxarifado)
    print(f"✅ Almoxarifado configurado com {len(itens_almoxarifado)} itens\n")
    
    # Definir jornada de trabalho
    inicio_jornada = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    fim_jornada = inicio_jornada.replace(hour=18, minute=0)
    
    print(f"⏰ Jornada de trabalho: {inicio_jornada.strftime('%H:%M')} às {fim_jornada.strftime('%H:%M')}")
    print()
    
    # Criar pedido simples
    print("📋 Criando pedido de coxinhas de frango...")
    pedido = PedidoDeProducao(
        id_ordem=1,
        id_pedido=1,
        id_produto=1055,  # ID das coxinhas de frango
        tipo_item=TipoItem.PRODUTO,
        quantidade=20,  # Quantidade pequena para ser processada rapidamente
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada,
        gestor_almoxarifado=gestor_almoxarifado
    )
    
    print("✅ Pedido criado\n")
    
    try:
        # Executar o pedido
        print("⚡ EXECUTANDO PEDIDO...")
        print("1️⃣ Montando estrutura técnica...")
        pedido.montar_estrutura()
        
        print("2️⃣ Criando atividades modulares...")
        pedido.criar_atividades_modulares_necessarias()
        
        atividades_produto = [a for a in pedido.atividades_modulares if a.tipo_item == TipoItem.PRODUTO]
        atividades_subproduto = [a for a in pedido.atividades_modulares if a.tipo_item == TipoItem.SUBPRODUTO]
        
        print(f"📊 Atividades: {len(atividades_produto)} PRODUTO, {len(atividades_subproduto)} SUBPRODUTO")
        print()
        
        print("3️⃣ Executando atividades com agrupamento de subprodutos...")
        pedido.executar_atividades_em_ordem()
        
        print(f"✅ PEDIDO EXECUTADO COM SUCESSO!")
        print(f"📊 Atividades executadas: {len(pedido.atividades_executadas)}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO na execução do pedido: {e}")
        return False


def main():
    """Função principal do script."""
    print("📅 DEMONSTRAÇÃO: VISUALIZAÇÃO DE AGENDA DE EQUIPAMENTOS")
    print("=" * 65)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    try:
        # Passo 1: Executar um pedido para gerar dados na agenda
        sucesso = executar_pedido_simples()
        
        if not sucesso:
            print("⚠️ Pedido não foi executado, mas vamos tentar mostrar a agenda mesmo assim")
        
        print("\n" + "="*65)
        print("📅 VISUALIZANDO AGENDA DOS EQUIPAMENTOS")
        print("="*65)
        
        # Passo 2: Mostrar agenda de todos os equipamentos
        mostrar_agenda_todos_equipamentos()
        
        print("\n" + "="*65)
        print("🎉 DEMONSTRAÇÃO CONCLUÍDA!")
        print("="*65)
        
        print("\n💡 EXPLICAÇÃO:")
        print("   • O sistema executou um pedido de coxinhas que usa agrupamento de subprodutos")
        print("   • As atividades foram alocadas automaticamente nos equipamentos disponíveis") 
        print("   • Cada equipamento mantém sua própria agenda com horários ocupados")
        print("   • O agrupamento permite que subprodutos relacionados sejam executados em sequência")
        print("   • A visualização mostra todos os equipamentos e suas respectivas agendas")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Execução interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Fim da demonstração")


if __name__ == "__main__":
    main()