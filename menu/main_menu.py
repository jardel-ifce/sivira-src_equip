#!/usr/bin/env python3
"""
Sistema de Menu Principal - Produção - DESACOPLADO
==================================================

Menu interativo para registro e execução de pedidos de produção
usando o novo GestorProducao independente dos scripts de teste.

✅ NOVIDADES:
- Desacoplado dos scripts producao_paes*
- Usa services/gestor_producao
- Limpeza automática integrada
- Interface simplificada
- 🆕 Limpeza automática de logs na inicialização
- 🆕 Sistema de Ordens/Sessões para agrupamento de pedidos
- 🆕 MODIFICAÇÃO: Limpeza automática de pedidos salvos (data/pedidos/pedidos_salvos.json)
- 🆕 AGENDA: Visualização de agenda de equipamentos integrada
- 🆕 CANCELAR PEDIDO: Liberação de equipamentos alocados
- 🆕 MÓDULO LIBERADOR: Sistema modular de liberação de equipamentos
"""

import os
import sys
from typing import Optional

# Adiciona paths necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu.gerenciador_pedidos import GerenciadorPedidos
from menu.utils_menu import MenuUtils
from services.gestor_producao import GestorProducao
from utils.logs.gerenciador_logs import limpar_logs_inicializacao


class MenuPrincipal:
    """Menu principal do sistema de produção com controle de ordens"""
    
    def __init__(self):
        print("🚀 Inicializando Sistema de Produção...")
        
        # 🆕 LIMPEZA AUTOMÁTICA DE LOGS E COMANDAS
        try:
            # 🆕 MODIFICAÇÃO: Agora limpar_logs_inicializacao() já inclui limpeza de comandas
            from utils.comandas.limpador_comandas import apagar_todas_as_comandas
            relatorio_limpeza = limpar_logs_inicializacao()
            apagar_todas_as_comandas()

            # Como agora retorna string formatada, vamos exibir
            if isinstance(relatorio_limpeza, str):
                print(relatorio_limpeza)
            else:
                # Compatibilidade com versão antiga
                if relatorio_limpeza['sucesso']:
                    if relatorio_limpeza['total_arquivos_removidos'] > 0:
                        print("✅ Ambiente de logs e comandas limpo e pronto!")  # ✅ MODIFICADO
                    else:
                        print("🔭 Ambiente de logs e comandas já estava limpo!")  # ✅ MODIFICADO
                else:
                    print("⚠️ Limpeza de logs/comandas concluída com alguns erros (sistema continuará)")  # ✅ MODIFICADO
                
        except Exception as e:
            print(f"⚠️ Erro durante limpeza de logs/comandas: {e}")  # ✅ MODIFICADO
            print("🔄 Sistema continuará normalmente...")
        
        print("🔧 Carregando nova arquitetura desacoplada...")
        
        # Inicializa componentes
        self.gerenciador = GerenciadorPedidos()
        self.gestor_producao = GestorProducao()  # ✅ NOVO: Usa GestorProducao independente
        self.utils = MenuUtils()
        self.rodando = True
        
        print("✅ Sistema inicializado com arquitetura independente!")
        print(f"📦 Sistema de Ordens ativo - Ordem atual: {self.gerenciador.obter_ordem_atual()}")

    
    def executar(self):
        """Executa o menu principal"""
        self.utils.limpar_tela()
        self.mostrar_banner()
        
        while self.rodando:
            try:
                self.mostrar_menu_principal()
                opcao = self.obter_opcao_usuario()
                self.processar_opcao(opcao)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Interrompido pelo usuário...")
                self.rodando = False
            except Exception as e:
                print(f"\n⚡ Erro inesperado: {e}")
                input("\nPressione Enter para continuar...")
    
    def mostrar_banner(self):
        """Mostra banner do sistema"""
        print("=" * 80)
        print("🏭 SISTEMA DE PRODUÇÃO - MENU INTERATIVO")
        print("=" * 80)
        print("📋 Registre pedidos e execute com arquitetura independente")
        print("🔧 Suporte a execução sequencial e otimizada (PL)")
        print("✅ Desacoplado dos scripts de teste (producao_paes*)")
        print("🎯 Nova arquitetura: services/gestor_producao")
        print("🧹 Limpeza automática integrada (logs + comandas)")  # ✅ MODIFICADO
        print("📦 Sistema de Ordens/Sessões para agrupamento")
        print("📅 Visualização de agenda de equipamentos")
        print("🔧 Módulo liberador: Sistema modular de equipamentos")
        print()
    
    def mostrar_menu_principal(self):
        """Mostra opções do menu principal"""
        print("\n" + "─" * 60)
        print("📋 MENU PRINCIPAL")
        print("─" * 60)
        
        # 🆕 Status com informações de ordem
        ordem_atual = self.gerenciador.obter_ordem_atual()
        pedidos_ordem_atual = len(self.gerenciador.obter_pedidos_ordem_atual())
        total_pedidos = len(self.gerenciador.pedidos)
        ordens_existentes = self.gerenciador.listar_ordens_existentes()
        
        print(f"📦 ORDEM ATUAL: {ordem_atual}")
        print(f"📊 Status: {pedidos_ordem_atual} pedido(s) na ordem atual | {total_pedidos} total")
        
        if len(ordens_existentes) > 1:
            print(f"📈 Ordens existentes: {ordens_existentes}")
        
        # Debug: verifica duplicatas
        if total_pedidos > 0:
            ids_completos = [(p.id_ordem, p.id_pedido) for p in self.gerenciador.pedidos]
            ids_unicos = len(set(ids_completos))
            if ids_unicos != total_pedidos:
                print(f"⚠️ ATENÇÃO: {total_pedidos - ids_unicos} duplicata(s) detectada(s)")
        
        # Status do sistema
        print("🗃️ Arquitetura: Independente (services/gestor_producao)")
        print("🧹 Limpeza: Automática (logs limpos na inicialização)")
        print("📦 Sistema: Ordens/Sessões ativo")
        print("📅 Agenda: Visualização de equipamentos disponível")
        print("🔧 Liberador: Sistema modular para equipamentos")
        
        if pedidos_ordem_atual == 0:
            print(f"📄 Ordem {ordem_atual}: Pronta para novos pedidos")
        else:
            print(f"⏳ Ordem {ordem_atual}: {pedidos_ordem_atual} pedido(s) aguardando execução")
        
        print()
        
        # Opções do menu
        print("📋 GESTÃO DE PEDIDOS:")
        print("1️⃣  Registrar Novo Pedido")
        print("2️⃣  Listar Pedidos Registrados")
        print("3️⃣  Remover Pedido")
        print("4️⃣  Cancelar Ordem | Pedido (Liberar Equipamentos)")
        print("5️⃣  Limpar Pedidos da Ordem Atual")
        print("6️⃣  Limpar Todos os Pedidos")
        print()
        print("🚀 EXECUÇÃO:")
        print("7️⃣  Executar Ordem Atual (SEQUENCIAL)")
        print("8️⃣  Executar Ordem Atual (OTIMIZADO PL)")
        print()
        print("📅 AGENDA DE EQUIPAMENTOS:")  # 🆕 NOVA SEÇÃO
        print("D️⃣  Ver Agenda de Equipamentos")
        print()
        print("⚙️ SISTEMA:")
        print("9️⃣  Testar Sistema")
        print("0️⃣  Configurações")
        print("A️⃣  Limpar Logs Manualmente")
        print("B️⃣  Histórico de Ordens")
        print("C️⃣  Debug Sistema Ordens")
        print("Z️⃣  Ajuda")
        print("[S]  Sair")
        print("─" * 60)
    
    def obter_opcao_usuario(self) -> str:
        """Obtém opção do usuário"""
        return input("🎯 Escolha uma opção: ").strip()
    
    def processar_opcao(self, opcao: str):
        """Processa opção escolhida pelo usuário"""
        
        if opcao == "1":
            self.registrar_pedido()
        
        elif opcao == "2":
            self.listar_pedidos()
        
        elif opcao == "3":
            self.remover_pedido()
        
        elif opcao == "4":
            self.cancelar_ordem_pedido()
        
        elif opcao == "5":
            self.limpar_ordem_atual()
        
        elif opcao == "6":
            self.limpar_todos_pedidos()
        
        elif opcao == "7":
            self.executar_sequencial()
        
        elif opcao == "8":
            self.executar_otimizado()
        
        elif opcao.lower() == "d":  # 🆕 NOVA OPÇÃO - AGENDA
            self.mostrar_submenu_agenda()
        
        elif opcao == "9":
            self.testar_sistema()
        
        elif opcao == "0":
            self.mostrar_configuracoes()
        
        elif opcao.lower() == "a":
            self.limpar_logs_manualmente()
        
        elif opcao.lower() == "b":
            self.mostrar_historico_ordens()
        
        elif opcao.lower() == "c":
            self.debug_sistema_ordens()
        
        elif opcao.lower() == "z":
            self.mostrar_ajuda()
        
        elif opcao.lower() in ["sair", "s", "quit", "exit"]:
            self.sair()
        
        else:
            print(f"\n⚡ Opção '{opcao}' inválida!")
            input("Pressione Enter para continuar...")
    
    # =========================================================================
    #                       🆕 SUBMENU AGENDA DE EQUIPAMENTOS
    # =========================================================================
    
    def mostrar_submenu_agenda(self):
        """Submenu para visualização de agenda de equipamentos"""
        try:
            from menu.visualizador_agenda import VisualizadorAgenda
            from menu.integrador_equipamentos import IntegradorEquipamentos
            
            visualizador = VisualizadorAgenda()
            integrador = IntegradorEquipamentos()
            rodando_agenda = True
            
            while rodando_agenda:
                try:
                    self.utils.limpar_tela()
                    print("📅 SISTEMA DE PRODUÇÃO - AGENDA DE EQUIPAMENTOS")
                    print("=" * 60)
                    
                    # Status da integração
                    if integrador.sistema_disponivel():
                        print("✅ Sistema de equipamentos: ATIVO")
                        info_sistema = integrador.obter_info_sistema()
                        print(f"🔧 Total de equipamentos: {info_sistema.get('total_equipamentos', 'N/A')}")
                        print(f"🏭 Tipos disponíveis: {info_sistema.get('total_tipos', 'N/A')}")
                    else:
                        print("⚠️ Sistema de equipamentos: LIMITADO (apenas logs)")
                    
                    print()
                    
                    # Menu expandido
                    print("OPÇÕES DISPONÍVEIS:")
                    print()
                    print("📋 VISUALIZAÇÃO BASEADA EM LOGS:")
                    print("1️⃣  Agenda Geral (todos os equipamentos)")
                    print("2️⃣  Agenda por Tipo de Equipamento")
                    print("3️⃣  Agenda de Equipamento Específico")
                    print("4️⃣  Buscar Atividades por Item")
                    print("5️⃣  Timeline por Ordem/Pedido")
                    print("6️⃣  Verificar Conflitos de Horário")
                    print()
                    print("🔧 SISTEMA REAL DE EQUIPAMENTOS:")
                    if integrador.sistema_disponivel():
                        print("7️⃣  Agenda de Equipamento Real (mostrar_agenda)")
                        print("8️⃣  Agenda de Gestor por Tipo")
                        print("9️⃣  Listar Todos os Equipamentos Disponíveis")
                        print("A️⃣  Verificar Status de Equipamento")
                    else:
                        print("7️⃣  [INDISPONÍVEL] Sistema de equipamentos não carregado")
                        print("8️⃣  [INDISPONÍVEL] Gestores não acessíveis")
                    print()
                    print("[V]  Voltar ao Menu Principal")
                    print("─" * 60)
                    
                    opcao_agenda = input("🎯 Escolha uma opção: ").strip().lower()
                    
                    # Processa opções tradicionais (baseadas em logs) 
                    if opcao_agenda in ['1', '2', '3', '4', '5', '6']:
                        visualizador.processar_opcao_agenda(opcao_agenda)
                        input("\nPressione Enter para continuar...")
                    
                    # Processa opções do sistema real
                    elif opcao_agenda == '7':
                        self._agenda_equipamento_real(integrador)
                        input("\nPressione Enter para continuar...")
                    elif opcao_agenda == '8':
                        self._agenda_gestor_tipo(integrador)
                        input("\nPressione Enter para continuar...")
                    elif opcao_agenda == '9':
                        self._listar_equipamentos_reais(integrador)
                        input("\nPressione Enter para continuar...")
                    elif opcao_agenda == 'a':
                        self._verificar_status_equipamento(integrador)
                        input("\nPressione Enter para continuar...")
                    elif opcao_agenda == 'v':
                        rodando_agenda = False
                    else:
                        print(f"\n⌚ Opção '{opcao_agenda}' inválida!")
                        input("Pressione Enter para continuar...")
                            
                except KeyboardInterrupt:
                    print("\n\n📙 Voltando ao menu principal...")
                    rodando_agenda = False
                except Exception as e:
                    print(f"\n⌚ Erro no submenu de agenda: {e}")
                    input("Pressione Enter para continuar...")
            
        except ImportError as e:
            print(f"\n⌚ Erro ao carregar módulos de agenda: {e}")
            print("📋 Verifique se os arquivos estão no diretório menu/:")
            print("   - menu/visualizador_agenda.py")
            print("   - menu/integrador_equipamentos.py")
            input("\nPressione Enter para continuar...")
        except Exception as e:
            print(f"\n⌚ Erro inesperado no submenu de agenda: {e}")
            input("Pressione Enter para continuar...")
    
    def _agenda_equipamento_real(self, integrador):
        """Mostra agenda de um equipamento real usando mostrar_agenda() - VERSÃO CORRIGIDA"""
        print("\n🔧 AGENDA DE EQUIPAMENTO REAL")
        print("=" * 30)
        
        if not integrador.sistema_disponivel():
            print("⌚ Sistema de equipamentos não disponível")
            return
        
        # Lista equipamentos disponíveis
        equipamentos_por_tipo = integrador.listar_equipamentos_disponiveis()
        
        if not equipamentos_por_tipo:
            print("🔭 Nenhum equipamento encontrado")
            return
        
        print("Equipamentos disponíveis por tipo:")
        todos_equipamentos = []
        for tipo, equipamentos in equipamentos_por_tipo.items():
            print(f"\n🏭 {tipo}:")
            for equipamento in equipamentos:
                todos_equipamentos.append(equipamento)
                print(f"  • {equipamento}")
        
        print(f"\nTotal: {len(todos_equipamentos)} equipamentos")
        
        nome_equipamento = input("\nDigite o nome exato do equipamento: ").strip()
        
        if nome_equipamento:
            print(f"\n📋 Obtendo agenda de '{nome_equipamento}'...")
            agenda = integrador.obter_agenda_equipamento_especifico(nome_equipamento)
            
            # CORREÇÃO: Verifica se houve erro explícito ou se executou com sucesso
            if agenda is not None and not (agenda.startswith("Erro") or agenda.startswith("Equipamento") or "não encontrado" in agenda or "não possui método" in agenda):
                if agenda.strip():
                    # Se capturou algum conteúdo, mostra
                    print("─" * 50)
                    print(agenda)
                    print("─" * 50)
                else:
                    # Agenda executada mas saída foi para o logger (comportamento normal)
                    print("✅ Agenda do equipamento executada com sucesso!")
                    print("📋 A agenda foi exibida através do sistema de logs acima.")
                    print("💡 NOTA: Os equipamentos usam logger.info() em vez de print() para a saída.")
            else:
                print(f"⌚ Não foi possível obter agenda de '{nome_equipamento}'")
                if agenda and (agenda.startswith("Erro") or "não encontrado" in agenda or "não possui método" in agenda):
                    print(f"   Detalhes: {agenda}")

    def _agenda_gestor_tipo(self, integrador):
        """Mostra agenda de um gestor por tipo - VERSÃO CORRIGIDA"""
        print("\n🏭 AGENDA DE GESTOR POR TIPO")
        print("=" * 30)
        
        if not integrador.sistema_disponivel():
            print("⌚ Sistema de equipamentos não disponível")
            return
        
        tipos_disponiveis = integrador.listar_tipos_equipamento()
        
        if not tipos_disponiveis:
            print("🔭 Nenhum tipo de equipamento encontrado")
            return
        
        print("Tipos de equipamento disponíveis:")
        for i, tipo in enumerate(tipos_disponiveis, 1):
            print(f"  {i}. {tipo}")
        
        try:
            escolha = input(f"\nEscolha um tipo (1-{len(tipos_disponiveis)}): ").strip()
            indice = int(escolha) - 1
            
            if 0 <= indice < len(tipos_disponiveis):
                tipo_escolhido = tipos_disponiveis[indice]
                print(f"\n📋 Obtendo agenda do gestor '{tipo_escolhido}'...")
                
                # CORREÇÃO: Captura o resultado mas não depende dele para determinar sucesso
                agenda = integrador.obter_agenda_gestor_tipo(tipo_escolhido)
                
                # Verifica se houve erro explícito ou se executou com sucesso
                if agenda is not None and not (agenda.startswith("Erro") or agenda.startswith("Gestor não encontrado") or agenda.startswith("Tipo de equipamento") or agenda.startswith("Nenhum equipamento encontrado")):
                    if agenda.strip():
                        # Se capturou algum conteúdo, mostra
                        print("─" * 50)
                        print(agenda)
                        print("─" * 50)
                    else:
                        # Agenda executada mas saída foi para o logger (comportamento normal)
                        print("✅ Agenda do gestor executada com sucesso!")
                        print("📋 A agenda foi exibida através do sistema de logs acima.")
                        print("💡 NOTA: Os gestores usam logger.info() em vez de print() para a saída.")
                else:
                    print(f"⌚ Não foi possível obter agenda do gestor '{tipo_escolhido}'")
                    if agenda and (agenda.startswith("Erro") or "não encontrado" in agenda):
                        print(f"   Detalhes: {agenda}")
            else:
                print("⌚ Opção inválida!")
                
        except ValueError:
            print("⌚ Digite um número válido!")

    def _listar_equipamentos_reais(self, integrador):
        """Lista todos os equipamentos disponíveis no sistema real"""
        print("\n📋 EQUIPAMENTOS DISPONÍVEIS NO SISTEMA")
        print("=" * 40)
        
        if not integrador.sistema_disponivel():
            print("⌚ Sistema de equipamentos não disponível")
            return
        
        estatisticas = integrador.obter_estatisticas_equipamentos()
        
        if "erro" in estatisticas:
            print(f"⌚ {estatisticas['erro']}")
            return
        
        print(f"📊 Total de equipamentos: {estatisticas['total_equipamentos']}")
        print(f"🏭 Total de tipos: {estatisticas['total_tipos']}")
        print()
        
        # Lista por tipo
        for tipo, equipamentos in estatisticas['equipamentos_por_tipo'].items():
            stats_tipo = estatisticas['estatisticas_por_tipo'][tipo]
            print(f"🔧 {tipo} ({stats_tipo['quantidade']} equipamentos - {stats_tipo['porcentagem']:.1f}%)")
            for equipamento in equipamentos:
                print(f"   • {equipamento}")
            print()

    def _verificar_status_equipamento(self, integrador):
        """Verifica status detalhado de um equipamento"""
        print("\n🔍 VERIFICAR STATUS DE EQUIPAMENTO")
        print("=" * 35)
        
        if not integrador.sistema_disponivel():
            print("⌚ Sistema de equipamentos não disponível")
            return
        
        nome_equipamento = input("Digite o nome do equipamento: ").strip()
        
        if not nome_equipamento:
            print("⌚ Nome não pode estar vazio")
            return
        
        print(f"\n🔍 Verificando '{nome_equipamento}'...")
        
        info = integrador.verificar_disponibilidade_equipamento(nome_equipamento)
        
        if "erro" in info:
            print(f"⌚ {info['erro']}")
            return
        
        print("✅ Equipamento encontrado!")
        print(f"🏷️ Nome: {info['nome']}")
        print(f"🏷️ Tipo: {info['tipo']}")
        print(f"📅 Tem agenda: {'✅ Sim' if info['tem_agenda'] else '⌚ Não'}")
        print(f"🔧 Métodos disponíveis: {len(info['metodos_disponiveis'])}")
        
        if info['metodos_disponiveis']:
            print("\nMétodos públicos:")
            for metodo in sorted(info['metodos_disponiveis']):
                print(f"   • {metodo}")
    
    # =========================================================================
    #                           GESTÃO DE PEDIDOS
    # =========================================================================
    
    def registrar_pedido(self):
        """Interface para registrar novo pedido"""
        self.utils.limpar_tela()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        proximo_pedido = len(self.gerenciador.obter_pedidos_ordem_atual()) + 1
        
        print("📋 REGISTRAR NOVO PEDIDO")
        print("=" * 40)
        print(f"📦 Ordem: {ordem_atual}")
        print(f"🎯 Próximo Pedido: {proximo_pedido}")
        print(f"🏷️ Será registrado como: Ordem {ordem_atual} | Pedido {proximo_pedido}")
        print()
        
        try:
            # Solicita dados do pedido
            dados_pedido = self.utils.coletar_dados_pedido()
            
            if dados_pedido:
                # Registra o pedido
                sucesso, mensagem = self.gerenciador.registrar_pedido(**dados_pedido)
                
                if sucesso:
                    print(f"\n✅ {mensagem}")
                    # Auto-salva pedidos após registro
                    self.gerenciador.salvar_pedidos()
                else:
                    print(f"\n⚡ {mensagem}")
            else:
                print("\nℹ️ Registro cancelado.")
                
        except Exception as e:
            print(f"\n⚡ Erro ao registrar pedido: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def listar_pedidos(self):
        """Lista todos os pedidos registrados"""
        self.utils.limpar_tela()
        print("📋 PEDIDOS REGISTRADOS")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("🔭 Nenhum pedido registrado ainda.")
            print("\n💡 Use a opção '1' para registrar novos pedidos")
        else:
            self.gerenciador.listar_pedidos()
            
            # Mostra estatísticas
            stats = self.gerenciador.obter_estatisticas()
            if stats["total"] > 0:
                print("📊 RESUMO GERAL:")
                print(f"   Total: {stats['total']} pedidos em {stats['total_ordens']} ordem(ns)")
                print(f"   Produtos: {stats['produtos']} | Subprodutos: {stats['subprodutos']}")
                print(f"   Quantidade total: {stats['quantidade_total']} unidades")
                print(f"   Período: {stats['inicio_mais_cedo'].strftime('%d/%m %H:%M')} → {stats['fim_mais_tarde'].strftime('%d/%m %H:%M')}")
                print()
                print(f"📦 ORDEM ATUAL ({stats['ordem_atual']}):")
                print(f"   Pedidos: {stats['pedidos_ordem_atual']}")
                if stats['pedidos_ordem_atual'] > 0:
                    print("   Status: ⏳ Aguardando execução")
                else:
                    print("   Status: 📄 Pronta para novos pedidos")
        
        input("\nPressione Enter para continuar...")
    
    def remover_pedido(self):
        """Remove um pedido específico"""
        self.utils.limpar_tela()
        print("🗒️ REMOVER PEDIDO")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("🔭 Nenhum pedido para remover.")
            input("\nPressione Enter para continuar...")
            return
        
        # Lista pedidos primeiro
        self.gerenciador.listar_pedidos()
        
        try:
            print("💡 Formato: Digite 'Ordem Pedido' (ex: '1 2' para Ordem 1 | Pedido 2)")
            print("💡 Ou apenas o número do pedido (buscará na ordem atual)")
            entrada = input("\n🎯 Digite Ordem e Pedido para remover (ou Enter para cancelar): ").strip()
            
            if entrada:
                partes = entrada.split()
                
                if len(partes) == 2:
                    # Formato: "ordem pedido"
                    id_ordem = int(partes[0])
                    id_pedido = int(partes[1])
                    sucesso, mensagem = self.gerenciador.remover_pedido(id_ordem, id_pedido)
                elif len(partes) == 1:
                    # Formato legado: apenas pedido (busca na ordem atual)
                    id_pedido = int(partes[0])
                    sucesso, mensagem = self.gerenciador.remover_pedido_legado(id_pedido)
                else:
                    print("\n⚡ Formato inválido!")
                    input("Pressione Enter para continuar...")
                    return
                
                print(f"\n{'✅' if sucesso else '⚡'} {mensagem}")
                
                if sucesso:
                    # Auto-salva após remoção
                    self.gerenciador.salvar_pedidos()
            else:
                print("\nℹ️ Remoção cancelada.")
                
        except ValueError:
            print("\n⚡ Formato inválido! Use números.")
        except Exception as e:
            print(f"\n⚡ Erro ao remover pedido: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def cancelar_ordem_pedido(self):
        """🆕 Cancela uma ordem/pedido específico liberando todos os equipamentos alocados"""
        self.utils.limpar_tela()
        print("🚫 CANCELAR ORDEM | PEDIDO")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("🔭 Nenhum pedido registrado para cancelar.")
            input("\nPressione Enter para continuar...")
            return
        
        # Lista pedidos existentes
        self.gerenciador.listar_pedidos()
        
        try:
            print("💡 Formato: Digite 'Ordem Pedido' (ex: '1 2' para cancelar Ordem 1 | Pedido 2)")
            entrada = input("\n🎯 Digite Ordem e Pedido para cancelar (ou Enter para voltar): ").strip()
            
            if not entrada:
                print("\nℹ️ Cancelamento cancelado.")
                input("\nPressione Enter para continuar...")
                return
                
            partes = entrada.split()
            
            if len(partes) != 2:
                print("\n⚡ Formato inválido! Use: 'ordem pedido' (ex: '1 2')")
                input("\nPressione Enter para continuar...")
                return
                
            id_ordem = int(partes[0])
            id_pedido = int(partes[1])
            
            # Verifica se o pedido existe
            pedido = self.gerenciador.obter_pedido(id_ordem, id_pedido)
            if not pedido:
                print(f"\n⌚ Ordem {id_ordem} | Pedido {id_pedido} não encontrado!")
                input("\nPressione Enter para continuar...")
                return
            
            # Mostra informações do pedido
            print(f"\n📋 Pedido encontrado:")
            print(f"   🎯 Ordem {pedido.id_ordem} | Pedido {pedido.id_pedido}")
            print(f"   📦 Item: {pedido.nome_item} (ID: {pedido.id_item})")
            print(f"   📊 Quantidade: {pedido.quantidade}")
            print(f"   🏷️ Tipo: {pedido.tipo_item}")
            
            # Confirmação
            confirmacao = input(f"\n⚠️ Confirma cancelamento da Ordem {id_ordem} | Pedido {id_pedido}? (s/N): ").strip().lower()
            
            if confirmacao in ['s', 'sim', 'y', 'yes']:
                # Tenta liberar equipamentos através do novo módulo
                try:
                    equipamentos_liberados = self._liberar_equipamentos_pedido(id_ordem, id_pedido)
                    
                    # Apaga o log do pedido cancelado
                    import os
                    log_path = f"logs/equipamentos/ordem: {id_ordem} | pedido: {id_pedido}.log"
                    if os.path.exists(log_path):
                        os.remove(log_path)
                        print(f"\n📄 Log do pedido removido: {log_path}")
                    
                    print(f"\n✅ Ordem {id_ordem} | Pedido {id_pedido} cancelado com sucesso!")
                    
                    if equipamentos_liberados > 0:
                        print(f"🔧 {equipamentos_liberados} equipamento(s) liberado(s)")
                    else:
                        print("ℹ️ Nenhum equipamento estava alocado ou já havia sido liberado")
                    
                    print("💡 NOTA: O pedido permanece registrado. Use 'Remover Pedido' para removê-lo completamente.")
                    
                except Exception as e:
                    print(f"\n⚠️ Erro ao liberar equipamentos: {e}")
                    print("ℹ️ O pedido pode não ter equipamentos alocados ou já foi processado")
            else:
                print("\nℹ️ Cancelamento cancelado.")
                
        except ValueError:
            print("\n⚡ Formato inválido! Use números (ex: '1 2')")
        except Exception as e:
            print(f"\n⚡ Erro ao cancelar pedido: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def _liberar_equipamentos_pedido(self, id_ordem: int, id_pedido: int) -> int:
        """
        Libera equipamentos alocados para uma ordem/pedido específico usando o novo módulo.
        
        Returns:
            int: Número de equipamentos que tiveram ocupações liberadas
        """
        try:
            from services.gestores_equipamentos.liberador_equipamentos import LiberadorEquipamentos
            
            liberador = LiberadorEquipamentos(debug=True)
            equipamentos_liberados, detalhes = liberador.liberar_equipamentos_pedido(id_ordem, id_pedido)
            
            # Mostra detalhes da liberação
            for detalhe in detalhes:
                print(detalhe)
            
            return equipamentos_liberados
            
        except ImportError as e:
            print(f"   Erro ao carregar módulo liberador: {e}")
            print("   Verifique se menu/liberador_equipamentos.py existe")
            return 0
        except Exception as e:
            print(f"   Erro geral na liberação: {e}")
            return 0
        
    def limpar_ordem_atual(self):
        """🆕 Remove apenas pedidos da ordem atual"""
        self.utils.limpar_tela()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        pedidos_ordem = self.gerenciador.obter_pedidos_ordem_atual()
        
        print("🗒️ LIMPAR ORDEM ATUAL")
        print("=" * 40)
        
        if not pedidos_ordem:
            print(f"🔭 Ordem {ordem_atual} não possui pedidos para limpar.")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"📦 Ordem atual: {ordem_atual}")
        print(f"⚠️ Isso removerá {len(pedidos_ordem)} pedido(s) da ordem atual!")
        print("💡 Outras ordens não serão afetadas")
        
        confirmacao = input("\nDigite 'CONFIRMAR' para prosseguir: ").strip()
        
        if confirmacao == "CONFIRMAR":
            self.gerenciador.limpar_ordem_atual()
            self.gerenciador.salvar_pedidos()  # Salva estado
            print(f"\n✅ Ordem {ordem_atual} limpa com sucesso.")
        else:
            print("\nℹ️ Operação cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def limpar_todos_pedidos(self):
        """Remove todos os pedidos de todas as ordens"""
        self.utils.limpar_tela()
        print("🗒️ LIMPAR TODOS OS PEDIDOS")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("🔭 Nenhum pedido para limpar.")
            input("\nPressione Enter para continuar...")
            return
        
        total_pedidos = len(self.gerenciador.pedidos)
        ordens_existentes = self.gerenciador.listar_ordens_existentes()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        
        print(f"⚠️ Isso removerá TODOS os {total_pedidos} pedidos!")
        print(f"📦 Ordens afetadas: {ordens_existentes}")
        print(f"💡 Ordem atual ({ordem_atual}) será mantida para novos pedidos")
        
        confirmacao = input("\nDigite 'CONFIRMAR TUDO' para prosseguir: ").strip()
        
        if confirmacao == "CONFIRMAR TUDO":
            self.gerenciador.limpar_pedidos()
            self.gerenciador.salvar_pedidos()  # Salva estado vazio
            print("\n✅ Todos os pedidos foram removidos.")
            print(f"📦 Ordem atual mantida: {ordem_atual}")
        else:
            print("\nℹ️ Operação cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    # =========================================================================
    #                              EXECUÇÃO
    # =========================================================================
    
    def executar_sequencial(self):
        """Executa pedidos da ordem atual em modo sequencial"""
        self.utils.limpar_tela()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        pedidos_ordem = self.gerenciador.obter_pedidos_ordem_atual()
        
        print("📄 EXECUÇÃO SEQUENCIAL")
        print("=" * 40)
        print(f"📦 Executando Ordem: {ordem_atual}")
        
        if not pedidos_ordem:
            print(f"🔭 Ordem {ordem_atual} não possui pedidos para executar.")
            print("\n💡 Use a opção '1' para registrar pedidos primeiro")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"📊 {len(pedidos_ordem)} pedido(s) da Ordem {ordem_atual} será(ão) executado(s).")
        print("⏱️ Isso pode levar alguns minutos...")
        print("\n🔧 Método: GestorProducao.executar_sequencial()")
        print("📋 SEQUENCIAL: Execução otimizada sem dependências externas")
        print("🧹 Ambiente limpo automaticamente")
        print("📦 SISTEMA DE ORDENS: Execução por ordem/sessão")
        
        # Mostra resumo dos pedidos da ordem atual
        print(f"\n📋 Pedidos da Ordem {ordem_atual}:")
        for pedido in pedidos_ordem:
            print(f"   • Ordem {pedido.id_ordem} | Pedido {pedido.id_pedido}: {pedido.nome_item} ({pedido.quantidade} uni)")
            print(f"     Prazo: {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
        
        confirmacao = input(f"\n🎯 Confirma execução da Ordem {ordem_atual}? (s/N): ").strip().lower()
        
        if confirmacao in ['s', 'sim', 'y', 'yes']:
            # Pergunta sobre validação de capacidade
            ignorar_capacidade = self._perguntar_validacao_capacidade(pedidos_ordem)
            print(f"🔍 DEBUG main_menu: ignorar_capacidade retornado = {ignorar_capacidade}")
            
            try:
                # Executa apenas pedidos da ordem atual
                sucesso = self.gestor_producao.executar_sequencial(pedidos_ordem, ignorar_capacidade=ignorar_capacidade)
                
                # 🆕 SEMPRE incrementa ordem após tentativa de execução (sucesso ou falha)
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()  # Salva nova ordem
                
                if sucesso:
                    print(f"\n🎉 Execução sequencial da Ordem {ordem_atual} concluída!")
                    print(f"📈 Sistema avançou para Ordem {nova_ordem}")
                    print("💡 Novos pedidos serão registrados na nova ordem")
                    
                    # 🆕 MODIFICAÇÃO: Limpeza automática após execução bem-sucedida
                    try:
                        from utils.logs.gerenciador_logs import limpar_arquivo_pedidos_salvos
                        print("🧹 Executando limpeza automática de pedidos salvos...")
                        if limpar_arquivo_pedidos_salvos():
                            print("✅ Arquivo de pedidos salvos limpo após execução bem-sucedida")
                    except Exception as e:
                        print(f"⚠️ Erro na limpeza pós-execução: {e}")
                    
                    # Mostra estatísticas
                    stats = self.gestor_producao.obter_estatisticas()
                    print(f"📊 Total processado: {stats.get('total_pedidos', 0)} pedidos")
                    print(f"⏱️ Tempo de execução: {stats.get('tempo_execucao', 0):.1f}s")
                else:
                    print(f"\n⚡ Falha na execução sequencial da Ordem {ordem_atual}!")
                    print(f"📈 Mesmo assim, sistema avançou para Ordem {nova_ordem}")
                    print("💡 Isso evita conflitos de IDs entre ordens com erro e novas ordens")
                    
            except Exception as e:
                # 🆕 MESMO EM CASO DE EXCEPTION, incrementa ordem
                print(f"\n⚡ Erro durante execução: {e}")
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()
                print(f"📈 Ordem incrementada para {nova_ordem} (devido ao erro)")
                print("💡 Isso evita conflitos de IDs em futuras execuções")
        else:
            print("\nℹ️ Execução cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def executar_otimizado(self):
        """Executa pedidos da ordem atual com otimização PL"""
        self.utils.limpar_tela()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        pedidos_ordem = self.gerenciador.obter_pedidos_ordem_atual()
        
        print("🚀 EXECUÇÃO OTIMIZADA (PL)")
        print("=" * 40)
        print(f"📦 Executando Ordem: {ordem_atual}")
        
        if not pedidos_ordem:
            print(f"🔭 Ordem {ordem_atual} não possui pedidos para executar.")
            print("\n💡 Use a opção '1' para registrar pedidos primeiro")
            input("\nPressione Enter para continuar...")
            return
        
        # Verifica OR-Tools primeiro
        ortools_ok, ortools_msg = self.utils.validar_or_tools()
        print(f"🔧 OR-Tools: {'✅' if ortools_ok else '⚡'} {ortools_msg}")
        
        if not ortools_ok:
            print("\n💡 Para instalar: pip install ortools")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"\n📊 {len(pedidos_ordem)} pedido(s) da Ordem {ordem_atual} será(ão) otimizado(s).")
        print("⏱️ Isso pode levar alguns minutos para encontrar a solução ótima...")
        print("\n🔧 Método: GestorProducao.executar_otimizado()")
        print("📋 OTIMIZADO: Usa Programação Linear independente")
        print("🧹 Ambiente limpo automaticamente")
        print("📦 SISTEMA DE ORDENS: Execução por ordem/sessão")
        
        # Mostra resumo dos pedidos da ordem atual
        print(f"\n📋 Pedidos da Ordem {ordem_atual} para otimização:")
        for pedido in pedidos_ordem:
            print(f"   • Ordem {pedido.id_ordem} | Pedido {pedido.id_pedido}: {pedido.nome_item} ({pedido.quantidade} uni)")
            print(f"     Prazo: {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
        
        confirmacao = input(f"\n🎯 Confirma execução otimizada da Ordem {ordem_atual}? (s/N): ").strip().lower()
        
        if confirmacao in ['s', 'sim', 'y', 'yes']:
            # Pergunta sobre validação de capacidade
            ignorar_capacidade = self._perguntar_validacao_capacidade(pedidos_ordem)
            
            try:
                # Executa apenas pedidos da ordem atual
                sucesso = self.gestor_producao.executar_otimizado(pedidos_ordem, ignorar_capacidade=ignorar_capacidade)
                
                # 🆕 SEMPRE incrementa ordem após tentativa de execução (sucesso ou falha)
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()  # Salva nova ordem
                
                if sucesso:
                    print(f"\n🎉 Execução otimizada da Ordem {ordem_atual} concluída!")
                    print(f"📈 Sistema avançou para Ordem {nova_ordem}")
                    print("💡 Novos pedidos serão registrados na nova ordem")
                    
                    # 🆕 MODIFICAÇÃO: Limpeza automática após execução bem-sucedida
                    try:
                        from utils.logs.gerenciador_logs import limpar_arquivo_pedidos_salvos
                        print("🧹 Executando limpeza automática de pedidos salvos...")
                        if limpar_arquivo_pedidos_salvos():
                            print("✅ Arquivo de pedidos salvos limpo após execução bem-sucedida")
                    except Exception as e:
                        print(f"⚠️ Erro na limpeza pós-execução: {e}")
                    
                    # Mostra estatísticas
                    stats = self.gestor_producao.obter_estatisticas()
                    print(f"📊 Total processado: {stats.get('total_pedidos', 0)} pedidos")
                    print(f"⏱️ Tempo de execução: {stats.get('tempo_execucao', 0):.1f}s")
                    if stats.get('modo') == 'otimizado':
                        print(f"🎯 Solução: {stats.get('status_solver', 'N/A')}")
                else:
                    print(f"\n⚡ Falha na execução otimizada da Ordem {ordem_atual}!")
                    print(f"📈 Mesmo assim, sistema avançou para Ordem {nova_ordem}")
                    print("💡 Isso evita conflitos de IDs entre ordens com erro e novas ordens")
                    
            except Exception as e:
                # 🆕 MESMO EM CASO DE EXCEPTION, incrementa ordem
                print(f"\n⚡ Erro durante execução otimizada: {e}")
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()
                print(f"📈 Ordem incrementada para {nova_ordem} (devido ao erro)")
                print("💡 Isso evita conflitos de IDs em futuras execuções")
        else:
            print("\nℹ️ Execução cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def _perguntar_validacao_capacidade(self, pedidos_ordem):
        """
        Pergunta ao usuário se deseja ignorar validação de capacidade.
        Retorna dicionário com configurações de bypass ou None para validação normal.
        """
        print("\n" + "─" * 50)
        print("🔧 CONFIGURAÇÃO DE VALIDAÇÃO DE CAPACIDADE")
        print("─" * 50)
        print("Deseja validar capacidade dos equipamentos durante execução?")
        print()
        print("📋 Opções:")
        print("1️⃣  SIM - Validar capacidade normalmente (padrão)")
        print("2️⃣  NÃO - Escolher pedidos específicos para ignorar validação")
        print("3️⃣  NUNCA - Ignorar validação para TODOS os pedidos")
        print()
        
        opcao = input("🎯 Escolha (1/2/3): ").strip()
        
        if opcao == "1" or opcao == "":
            print("✅ Validação de capacidade: ATIVADA para todos os pedidos")
            return None  # Validação normal
        
        elif opcao == "3":
            print("⚠️ Configurando bypass para TODOS os pedidos")
            # Configura bypass para todos os pedidos
            bypass_config = {}
            for pedido in pedidos_ordem:
                equipamentos_bypass = self._selecionar_equipamentos_bypass(pedido)
                if equipamentos_bypass:
                    if pedido.id_ordem not in bypass_config:
                        bypass_config[pedido.id_ordem] = {}
                    bypass_config[pedido.id_ordem][pedido.id_pedido] = equipamentos_bypass
            return bypass_config
        
        elif opcao == "2":
            return self._selecionar_pedidos_ignorar_capacidade(pedidos_ordem)
        
        else:
            print("⚡ Opção inválida. Usando validação padrão.")
            return None
    
    def _selecionar_pedidos_ignorar_capacidade(self, pedidos_ordem):
        """
        Permite ao usuário selecionar pedidos específicos e tipos de equipamentos para ignorar validação de capacidade.
        """
        print("\n📋 PEDIDOS DISPONÍVEIS:")
        print("─" * 30)
        for pedido in pedidos_ordem:
            print(f"   {pedido.id_ordem} {pedido.id_pedido}: {pedido.nome_item} ({pedido.quantidade} uni)")
        print()
        
        print("💡 INSTRUÇÕES:")
        print("   • Digite pares 'ordem pedido' separados por espaço")
        print("   • Exemplo: '1 1' para Ordem 1 Pedido 1")
        print("   • Exemplo: '1 1 1 2 2 1' para múltiplos pedidos")
        print("   • Digite '*' para configurar bypass para TODOS os pedidos")
        print("   • Digite apenas Enter para configurar TODOS os pedidos individualmente")
        print()
        
        entrada = input("🎯 Pedidos para configurar bypass: ").strip()
        
        if not entrada:
            print("⚠️ Nenhum pedido especificado - configurando bypass para TODOS os pedidos")
            # Se não especificar pedidos, configura bypass para todos
            bypass_config = {}
            for pedido in pedidos_ordem:
                equipamentos_bypass = self._selecionar_equipamentos_bypass(pedido)
                if equipamentos_bypass:
                    if pedido.id_ordem not in bypass_config:
                        bypass_config[pedido.id_ordem] = {}
                    bypass_config[pedido.id_ordem][pedido.id_pedido] = equipamentos_bypass
            return bypass_config
        
        if entrada == "*":
            print("⚠️ Configurando bypass para TODOS os pedidos")
            # Configura bypass para todos
            bypass_config = {}
            for pedido in pedidos_ordem:
                equipamentos_bypass = self._selecionar_equipamentos_bypass(pedido)
                if equipamentos_bypass:
                    if pedido.id_ordem not in bypass_config:
                        bypass_config[pedido.id_ordem] = {}
                    bypass_config[pedido.id_ordem][pedido.id_pedido] = equipamentos_bypass
            return bypass_config
        
        try:
            # Processa entrada manual
            partes = entrada.split()
            if len(partes) % 2 != 0:
                print("⚡ Formato inválido! Use pares 'ordem pedido'")
                return None
            
            bypass_config = {}
            pedidos_selecionados = []
            
            for i in range(0, len(partes), 2):
                ordem = int(partes[i])
                pedido_id = int(partes[i + 1])
                pedidos_selecionados.append((ordem, pedido_id))
            
            # Valida se pedidos existem
            pedidos_validos = [(p.id_ordem, p.id_pedido) for p in pedidos_ordem]
            pedidos_invalidos = [p for p in pedidos_selecionados if p not in pedidos_validos]
            
            if pedidos_invalidos:
                print(f"⚡ Pedidos inválidos encontrados: {pedidos_invalidos}")
                print("⚠️ Usando validação padrão para todos")
                return None
            
            # Para cada pedido selecionado, permite escolher equipamentos
            for ordem, pedido_id in pedidos_selecionados:
                pedido = next(p for p in pedidos_ordem if p.id_ordem == ordem and p.id_pedido == pedido_id)
                equipamentos_bypass = self._selecionar_equipamentos_bypass(pedido)
                
                if equipamentos_bypass:
                    if ordem not in bypass_config:
                        bypass_config[ordem] = {}
                    bypass_config[ordem][pedido_id] = equipamentos_bypass
            
            print(f"🔍 DEBUG _selecionar_pedidos_ignorar_capacidade: bypass_config final = {bypass_config}")
            return bypass_config
            
        except ValueError:
            print("⚡ Formato inválido! Use apenas números.")
            return None
        except Exception as e:
            print(f"⚡ Erro ao processar seleção: {e}")
            return None
    
    def _selecionar_equipamentos_bypass(self, pedido):
        """
        Permite ao usuário selecionar tipos específicos de equipamentos para ignorar validação.
        """
        print(f"\n🔧 CONFIGURAÇÃO DE BYPASS - Ordem {pedido.id_ordem} | Pedido {pedido.id_pedido}")
        print(f"📦 Item: {pedido.nome_item} ({pedido.quantidade} uni)")
        print("─" * 50)
        
        # Descobrir tipos de equipamentos usados nas atividades deste pedido
        tipos_equipamentos = self._descobrir_tipos_equipamentos_pedido(pedido)
        
        if not tipos_equipamentos:
            print("⚠️ Nenhum tipo de equipamento identificado para este pedido")
            return None
        
        print("📋 TIPOS DE EQUIPAMENTOS USADOS NESTE PEDIDO:")
        mapeamento_tipos = {}
        
        for idx, tipo_equip in enumerate(tipos_equipamentos, 1):
            nome_amigavel = self._obter_nome_amigavel_equipamento(tipo_equip)
            print(f"   {idx} - {nome_amigavel}")
            mapeamento_tipos[idx] = tipo_equip
        
        print()
        print("💡 INSTRUÇÕES:")
        print("   • Digite os números dos tipos de equipamentos para ignorar validação")
        print("   • Exemplo: '1 3' para ignorar validação nos tipos 1 e 3")
        print("   • Digite '*' para ignorar validação em TODOS os tipos")
        print("   • Digite apenas Enter para não ignorar nenhum tipo")
        print()
        
        entrada = input("🎯 Tipos de equipamentos para ignorar: ").strip()
        
        if not entrada:
            print("✅ Validação mantida para todos os tipos de equipamentos")
            return None
        
        if entrada == "*":
            print("⚠️ Bypass configurado para TODOS os tipos de equipamentos")
            return set(tipos_equipamentos)
        
        try:
            indices = [int(x) for x in entrada.split()]
            tipos_selecionados = set()
            
            for indice in indices:
                if indice in mapeamento_tipos:
                    tipos_selecionados.add(mapeamento_tipos[indice])
                else:
                    print(f"⚠️ Índice inválido: {indice}")
            
            if tipos_selecionados:
                print("✅ Bypass configurado para os seguintes tipos:")
                for tipo in tipos_selecionados:
                    nome_amigavel = self._obter_nome_amigavel_equipamento(tipo)
                    print(f"   • {nome_amigavel}")
                return tipos_selecionados
            else:
                print("⚠️ Nenhum tipo válido selecionado")
                return None
                
        except ValueError:
            print("⚡ Formato inválido! Use apenas números.")
            return None
        except Exception as e:
            print(f"⚡ Erro ao processar seleção: {e}")
            return None
    
    def _descobrir_tipos_equipamentos_pedido(self, pedido):
        """
        Descobre quais tipos de equipamentos são usados nas atividades de um pedido,
        incluindo subprodutos que precisam ser produzidos (lógica igual ao PedidoDeProducao).
        """
        try:
            from parser.carregador_json_atividades import buscar_atividades_por_id_item
            from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
            from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
            from enums.equipamentos.tipo_equipamento import TipoEquipamento
            from enums.producao.tipo_item import TipoItem
            
            # Converter string para enum se necessário
            tipo_item_enum = TipoItem.PRODUTO if pedido.tipo_item == "PRODUTO" else TipoItem.SUBPRODUTO
            
            tipos_equipamentos = set()
            
            # Buscar ficha técnica do item principal
            try:
                _, dados_ficha = buscar_ficha_tecnica_por_id(pedido.id_item, tipo_item=tipo_item_enum)
                ficha_tecnica_modular = FichaTecnicaModular(
                    dados_ficha_tecnica=dados_ficha,
                    quantidade_requerida=pedido.quantidade
                )
            except Exception as e:
                print(f"⚠️ Erro ao carregar ficha técnica do item {pedido.id_item}: {e}")
                return []
            
            # Descobrir equipamentos recursivamente
            self._descobrir_equipamentos_recursivo(ficha_tecnica_modular, tipos_equipamentos)
            
            tipos_list = sorted(list(tipos_equipamentos), key=lambda x: x.name)
            return tipos_list
            
        except Exception as e:
            print(f"⚠️ Erro ao descobrir equipamentos: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _descobrir_equipamentos_recursivo(self, ficha_modular, tipos_equipamentos):
        """
        Descobre tipos de equipamentos recursivamente seguindo a mesma lógica do PedidoDeProducao.
        """
        try:
            from parser.carregador_json_atividades import buscar_atividades_por_id_item
            from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
            from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
            from enums.producao.tipo_item import TipoItem
            
            # Lógica igual ao PedidoDeProducao: 
            # PRODUTOS sempre são produzidos, SUBPRODUTOS só se não tiverem estoque
            if ficha_modular.tipo_item == TipoItem.PRODUTO:
                deve_produzir = True
            elif ficha_modular.tipo_item == TipoItem.SUBPRODUTO:
                # Verificar estoque do subproduto
                deve_produzir = not self._verificar_estoque_suficiente_para_bypass(
                    ficha_modular.id_item, 
                    ficha_modular.quantidade_requerida
                )
            else:
                deve_produzir = True
            
            # Se deve produzir, buscar atividades e extrair equipamentos
            if deve_produzir:
                atividades = buscar_atividades_por_id_item(ficha_modular.id_item, ficha_modular.tipo_item)
                
                if atividades:
                    for atividade in atividades:
                        # atividade é uma tupla (dados_item, dados_atividade)
                        if isinstance(atividade, tuple) and len(atividade) > 1:
                            _, dados_atividade = atividade
                            equipamentos_elegiveis = dados_atividade.get("equipamentos_elegiveis", [])
                        elif isinstance(atividade, dict):
                            equipamentos_elegiveis = atividade.get("equipamentos_elegiveis", [])
                        else:
                            equipamentos_elegiveis = []
                        
                        for nome_equip in equipamentos_elegiveis:
                            tipo = self._mapear_nome_para_tipo_equipamento(nome_equip)
                            if tipo:
                                tipos_equipamentos.add(tipo)
            
            # Processar subprodutos recursivamente (igual ao PedidoDeProducao)
            try:
                estimativas = ficha_modular.calcular_quantidade_itens()
                
                for item_dict, quantidade in estimativas:
                    tipo = item_dict.get("tipo_item")
                    id_ficha = item_dict.get("id_ficha_tecnica")

                    if tipo == "SUBPRODUTO" and id_ficha:
                        try:
                            _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha, TipoItem.SUBPRODUTO)
                            ficha_sub = FichaTecnicaModular(dados_ficha_sub, quantidade)
                            # Chamada recursiva
                            self._descobrir_equipamentos_recursivo(ficha_sub, tipos_equipamentos)
                        except Exception as e:
                            print(f"⚠️ Erro ao processar subproduto {id_ficha}: {e}")
                            continue
                            
            except Exception as e:
                print(f"⚠️ Erro ao processar subprodutos do item {ficha_modular.id_item}: {e}")
                
        except Exception as e:
            print(f"⚠️ Erro na descoberta recursiva do item {ficha_modular.id_item}: {e}")
    
    def _verificar_estoque_suficiente_para_bypass(self, id_item, quantidade):
        """
        Verifica se há estoque suficiente para um item.
        Usa o gestor_almoxarifado se disponível, senão assume que precisa produzir.
        """
        try:
            # Tentar acessar o gestor de almoxarifado através do configurador
            if hasattr(self, 'configurador_ambiente') and self.configurador_ambiente:
                gestor_almoxarifado = self.configurador_ambiente.gestor_almoxarifado
            else:
                # Inicializar o ambiente se necessário
                self._inicializar_ambiente_bypass()
                gestor_almoxarifado = getattr(self.configurador_ambiente, 'gestor_almoxarifado', None)
            
            if gestor_almoxarifado:
                from datetime import datetime
                # Usar o método correto do gestor
                resultado = gestor_almoxarifado.verificar_disponibilidade_multiplos_itens(
                    [(id_item, quantidade)], datetime.now().date()
                )
                return resultado.get(id_item, False)
            else:
                # Se não tem gestor, assume que precisa produzir
                return False
                
        except Exception as e:
            print(f"⚠️ Erro ao verificar estoque para item {id_item}: {e}")
            # Em caso de erro, assume que precisa produzir
            return False
    
    def _inicializar_ambiente_bypass(self):
        """Inicializa o ambiente apenas se necessário para verificação de estoque"""
        try:
            if not hasattr(self, 'configurador_ambiente') or not self.configurador_ambiente:
                from services.gestor_producao.configurador_ambiente import ConfiguradorAmbiente
                self.configurador_ambiente = ConfiguradorAmbiente()
                self.configurador_ambiente.inicializar_ambiente()
        except Exception as e:
            print(f"⚠️ Erro ao inicializar ambiente para bypass: {e}")
    
    def _mapear_nome_para_tipo_equipamento(self, nome_equipamento):
        """
        Mapeia nome do equipamento para TipoEquipamento enum.
        """
        try:
            from enums.equipamentos.tipo_equipamento import TipoEquipamento
            
            mapeamento = {
                'masseira': TipoEquipamento.MISTURADORAS,
                'forno': TipoEquipamento.FORNOS,
                'bancada': TipoEquipamento.BANCADAS,
                'balanca_digital': TipoEquipamento.BALANCAS,
                'divisora_de_massas': TipoEquipamento.DIVISORAS_BOLEADORAS,
                'armario_fermentador': TipoEquipamento.ARMARIOS_PARA_FERMENTACAO,
                'embaladora': TipoEquipamento.EMBALADORAS,
                'batedeira_planetaria': TipoEquipamento.BATEDEIRAS,
                'batedeira_industrial': TipoEquipamento.BATEDEIRAS,
                'fogao': TipoEquipamento.FOGOES,
                'fritadeira': TipoEquipamento.FRITADEIRAS,
                'modeladora_de_paes': TipoEquipamento.MODELADORAS,
                'modeladora_de_salgados': TipoEquipamento.MODELADORAS,
                'camara_refrigerada': TipoEquipamento.REFRIGERACAO_CONGELAMENTO,
                'freezer': TipoEquipamento.REFRIGERACAO_CONGELAMENTO,
                'hot_mix': TipoEquipamento.MISTURADORAS_COM_COCCAO,
            }
            
            # Remove sufixo numérico para extrair tipo base (ex: "balanca_digital_1" -> "balanca_digital")
            nome_base = nome_equipamento.lower()
            if '_' in nome_base and nome_base.split('_')[-1].isdigit():
                nome_base = '_'.join(nome_base.split('_')[:-1])
            
            return mapeamento.get(nome_base)
            
        except Exception as e:
            print(f"⚠️ Erro no mapeamento de {nome_equipamento}: {e}")
            return None
    
    def _obter_nome_amigavel_equipamento(self, tipo_equipamento):
        """
        Converte TipoEquipamento enum para nome amigável.
        """
        try:
            nomes_amigaveis = {
                'MISTURADORAS': 'Misturadoras/Masseiras',
                'FORNOS': 'Fornos',
                'BANCADAS': 'Bancadas',
                'BALANCAS': 'Balanças Digitais',
                'DIVISORAS_BOLEADORAS': 'Divisoras/Boleadoras',
                'ARMARIOS_PARA_FERMENTACAO': 'Armários de Fermentação',
                'EMBALADORAS': 'Embaladoras',
                'BATEDEIRAS': 'Batedeiras',
                'FOGOES': 'Fogões',
                'FRITADEIRAS': 'Fritadeiras',
                'MODELADORAS': 'Modeladoras',
                'REFRIGERACAO_CONGELAMENTO': 'Refrigeração/Congelamento',
                'MISTURADORAS_COM_COCCAO': 'Misturadoras com Cocção',
            }
            
            return nomes_amigaveis.get(tipo_equipamento.name, tipo_equipamento.name)
            
        except Exception as e:
            return str(tipo_equipamento)
    
    # =========================================================================
    #                              SISTEMA
    # =========================================================================
    
    def testar_sistema(self):
        """Testa componentes do sistema"""
        self.utils.limpar_tela()
        print("🧪 TESTE DO SISTEMA")
        print("=" * 40)
        
        print("Executando diagnóstico completo do sistema...\n")
        
        try:
            resultados = self.gestor_producao.testar_sistema()
            
            # Resumo final
            print(f"\n🎯 DIAGNÓSTICO CONCLUÍDO")
            
            testes_ok = sum(1 for r in resultados.values() if isinstance(r, dict) and r.get('ok', False))
            total_testes = sum(1 for r in resultados.values() if isinstance(r, dict) and 'ok' in r)
            
            if testes_ok == total_testes:
                print("✅ Sistema pronto para execução!")
            else:
                print(f"⚠️ {total_testes - testes_ok} problema(s) encontrado(s)")
            
            print(f"🗃️ Arquitetura: Independente (services/gestor_producao)")
            print(f"📦 Sistema de Ordens: Ativo (Ordem atual: {self.gerenciador.obter_ordem_atual()})")
            
        except Exception as e:
            print(f"⚡ Erro durante teste: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def mostrar_configuracoes(self):
        """Mostra configurações do sistema"""
        self.utils.limpar_tela()
        print("⚙️ CONFIGURAÇÕES DO SISTEMA")
        print("=" * 40)
        
        # Informações do sistema
        info_sistema = self.utils.obter_info_sistema()
        print(f"🐍 Python: {info_sistema['python_version']}")
        print(f"💻 Sistema: {info_sistema['platform']} {info_sistema['platform_version']}")
        print()
        
        # Configurações dos diretórios
        print(f"📂 Diretórios:")
        print(f"   Produtos: {self.gerenciador.dir_produtos}")
        print(f"   Subprodutos: {self.gerenciador.dir_subprodutos}")
        print(f"   Pedidos salvos: {self.gerenciador.arquivo_pedidos}")
        print()
        
        # Arquitetura
        print(f"🗃️ Nova Arquitetura:")
        print(f"   Gestor: services/gestor_producao/")
        print(f"   Independente: ✅ Desacoplado dos scripts de teste")
        print(f"   Limpeza: ✅ Automática integrada")
        print(f"   Ordens: ✅ Sistema de sessões ativo")
        print(f"   Liberador: ✅ Sistema modular para equipamentos")
        print()
        
        # Status do sistema
        stats = self.gerenciador.obter_estatisticas()
        print(f"📋 Status:")
        print(f"   OR-Tools: {'✅ Disponível' if info_sistema['ortools_disponivel'] else '⚡ Não encontrado'}")
        print(f"   Ordem atual: {stats['ordem_atual']}")
        print(f"   Total de pedidos: {stats['total']} em {stats['total_ordens']} ordem(ns)")
        print(f"   Pedidos na ordem atual: {stats['pedidos_ordem_atual']}")
        
        # Opções de configuração
        print(f"\n🔧 CONFIGURAR PARÂMETROS:")
        print("1 - Configurar parâmetros de otimização")
        print("2 - Resetar ordem atual")  # 🆕 Nova opção
        print("0 - Voltar")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            print("\n⚙️ Configuração de parâmetros:")
            print("Digite novos valores ou pressione Enter para manter atual")
            
            try:
                # Resolução temporal
                atual_res = input("Resolução temporal em minutos (atual: 30): ").strip()
                if atual_res and int(atual_res) > 0:
                    self.gestor_producao.configurar(resolucao_minutos=int(atual_res))
                
                # Timeout
                atual_timeout = input("Timeout em segundos (atual: 300): ").strip()
                if atual_timeout and int(atual_timeout) > 0:
                    self.gestor_producao.configurar(timeout_pl=int(atual_timeout))
                    
                print("✅ Configurações atualizadas!")
                
            except ValueError:
                print("⚡ Valores inválidos!")
        
        elif opcao == "2":  # 🆕 Nova opção
            print(f"\n📦 Resetar ordem atual:")
            print(f"Ordem atual: {self.gerenciador.obter_ordem_atual()}")
            print("⚠️ Isso redefinirá a ordem para 1 e limpará todos os pedidos!")
            
            confirmacao = input("Digite 'RESET' para confirmar: ").strip()
            if confirmacao == "RESET":
                self.gerenciador.ordem_atual = 1
                self.gerenciador.contador_pedido = 1
                self.gerenciador.limpar_pedidos()
                self.gerenciador.salvar_pedidos()
                print("✅ Sistema resetado para Ordem 1!")
            else:
                print("ℹ️ Reset cancelado.")
        
        input("\nPressione Enter para continuar...")
    
    def limpar_logs_manualmente(self):
        """Limpeza manual de logs"""
        self.utils.limpar_tela()
        print("🧹 LIMPEZA MANUAL DE LOGS")
        print("=" * 40)
        
        print("Esta opção permite limpar logs manualmente durante a sessão.")
        print("⚠️ ATENÇÃO: Logs são limpos automaticamente na inicialização")
        print()
        
        print("Opções de limpeza:")
        print("1 - Limpar todos os logs de inicialização + pedidos salvos")
        print("2 - Limpar apenas logs de funcionários")
        print("3 - Limpar apenas logs de equipamentos")
        print("4 - Limpar apenas logs de erros")
        print("5 - Limpar apenas logs de execuções")
        print("6 - Limpar apenas arquivo de pedidos salvos")  # 🆕 MODIFICAÇÃO: Nova opção
        print("0 - Voltar")
        
        opcao = input("\n🎯 Escolha uma opção: ").strip()
        
        if opcao == "1":
            print("\n🧹 Limpando todos os logs de inicialização...")
            try:
                relatorio = limpar_logs_inicializacao()
                # Como pode retornar string ou dict
                if isinstance(relatorio, str):
                    print(relatorio)
                else:
                    if relatorio['sucesso']:
                        print("✅ Limpeza manual concluída!")
                    else:
                        print("⚠️ Limpeza concluída com alguns erros")
            except Exception as e:
                print(f"⚡ Erro durante limpeza: {e}")
        
        elif opcao in ["2", "3", "4", "5"]:
            pastas_opcoes = {
                "2": "logs/funcionarios",
                "3": "logs/equipamentos", 
                "4": "logs/erros",
                "5": "logs/execucoes"
            }
            
            pasta = pastas_opcoes[opcao]
            print(f"\n🧹 Limpando pasta: {pasta}")
            
            try:
                if os.path.exists(pasta):
                    arquivos_removidos = 0
                    for arquivo in os.listdir(pasta):
                        caminho = os.path.join(pasta, arquivo)
                        if os.path.isfile(caminho):
                            os.remove(caminho)
                            arquivos_removidos += 1
                    
                    print(f"✅ {arquivos_removidos} arquivo(s) removido(s) de {pasta}")
                else:
                    print(f"📁 Pasta {pasta} não existe")
                    
            except Exception as e:
                print(f"⚡ Erro ao limpar {pasta}: {e}")
        
        elif opcao == "6":  # 🆕 MODIFICAÇÃO: Nova opção
            print(f"\n🧹 Limpando arquivo de pedidos salvos...")
            try:
                from utils.logs.gerenciador_logs import limpar_arquivo_pedidos_salvos
                if limpar_arquivo_pedidos_salvos():
                    print("✅ Arquivo de pedidos salvos removido")
                else:
                    print("📄 Arquivo de pedidos salvos não existia")
            except Exception as e:
                print(f"⚡ Erro ao limpar arquivo de pedidos: {e}")
        
        elif opcao == "0":
            return
        else:
            print("⚡ Opção inválida!")
        
        input("\nPressione Enter para continuar...")
    
    def mostrar_historico_ordens(self):
        """🆕 Mostra histórico de ordens executadas"""
        self.utils.limpar_tela()
        print("📈 HISTÓRICO DE ORDENS")
        print("=" * 40)
        
        ordens_existentes = self.gerenciador.listar_ordens_existentes()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        
        if not ordens_existentes:
            print("🔭 Nenhuma ordem registrada ainda.")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"📦 Ordem atual: {ordem_atual}")
        print(f"📊 Total de ordens com pedidos: {len(ordens_existentes)}")
        print()
        
        for ordem in ordens_existentes:
            pedidos_ordem = self.gerenciador.obter_pedidos_por_ordem(ordem)
            
            # 🆕 Status mais descritivo
            if ordem == ordem_atual:
                status = "🎯 ATUAL"
            elif ordem < ordem_atual:
                status = "📋 PROCESSADA"  # Pode ter sido bem-sucedida ou ter falhado
            else:
                status = "❓ FUTURA"  # Não deveria acontecer
            
            print(f"📦 ORDEM {ordem} - {status}")
            print(f"   Pedidos: {len(pedidos_ordem)}")
            
            if pedidos_ordem:
                # Calcula estatísticas da ordem
                quantidade_total = sum(p.quantidade for p in pedidos_ordem)
                primeiro_registro = min(p.registrado_em for p in pedidos_ordem)
                ultimo_registro = max(p.registrado_em for p in pedidos_ordem)
                
                print(f"   Quantidade total: {quantidade_total} unidades")
                print(f"   Período de registro: {primeiro_registro.strftime('%d/%m %H:%M')} → {ultimo_registro.strftime('%d/%m %H:%M')}")
                
                # Lista itens resumidamente
                itens_resumo = {}
                for p in pedidos_ordem:
                    if p.nome_item in itens_resumo:
                        itens_resumo[p.nome_item] += p.quantidade
                    else:
                        itens_resumo[p.nome_item] = p.quantidade
                
                print("   Itens:")
                for item, qty in itens_resumo.items():
                    print(f"      • {item}: {qty} uni")
            
            print()
        
        print("💡 LEGENDA:")
        print("   🎯 ATUAL: Ordem ativa para novos pedidos")
        print("   📋 PROCESSADA: Ordem executada (sucesso ou erro)")
        print("   • Ordens sempre incrementam após execução")
        print("   • Isso garante IDs únicos mesmo quando há erros")
        
        input("\nPressione Enter para continuar...")
    
    def debug_sistema_ordens(self):
        """Debug do sistema de ordens"""
        self.utils.limpar_tela()
        print("DEBUG - SISTEMA DE ORDENS")
        print("=" * 40)
        
        self.gerenciador.debug_sistema_ordens()
        
        print("\nDEBUG - ESTATISTICAS DETALHADAS")
        print("-" * 40)
        
        # Debug adicional do gerenciador
        stats = self.gerenciador.obter_estatisticas()
        print(f"Ordem atual: {stats['ordem_atual']}")
        print(f"Contador pedido: {self.gerenciador.contador_pedido}")
        print(f"Total de pedidos na memoria: {len(self.gerenciador.pedidos)}")
        print(f"Pedidos unicos (sem duplicatas): {len(set((p.id_ordem, p.id_pedido) for p in self.gerenciador.pedidos))}")
        
        # Verifica consistencia dos IDs
        ids_completos = [(p.id_ordem, p.id_pedido) for p in self.gerenciador.pedidos]
        ids_duplicados = [id_ped for id_ped in ids_completos if ids_completos.count(id_ped) > 1]
        
        if ids_duplicados:
            print(f"ATENCAO: IDs duplicados encontrados: {set(ids_duplicados)}")
        else:
            print("Consistencia de IDs: OK")
        
        # Status do arquivo de salvamento
        if os.path.exists(self.gerenciador.arquivo_pedidos):
            stat_arquivo = os.stat(self.gerenciador.arquivo_pedidos)
            from datetime import datetime
            modificado = datetime.fromtimestamp(stat_arquivo.st_mtime)
            print(f"Arquivo de pedidos: {self.gerenciador.arquivo_pedidos}")
            print(f"Ultima modificacao: {modificado.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"Tamanho: {stat_arquivo.st_size} bytes")
        else:
            print("Arquivo de pedidos: NAO EXISTE")
        
        input("\nPressione Enter para continuar...")
    
    def mostrar_ajuda(self):
        """Mostra ajuda do sistema"""
        self.utils.limpar_tela()
        print("AJUDA - SISTEMA DE PRODUCAO")
        print("=" * 40)
        
        print("CONCEITOS PRINCIPAIS:")
        print("-" * 20)
        print("ORDEM: Grupo de pedidos executados juntos")
        print("PEDIDO: Item individual com quantidade e prazo")
        print("SEQUENCIAL: Execucao tradicional otimizada")
        print("OTIMIZADO (PL): Programacao Linear para melhor resultado")
        print()
        
        print("FLUXO RECOMENDADO:")
        print("-" * 18)
        print("1. Registre pedidos (opcao 1)")
        print("2. Revise pedidos registrados (opcao 2)")
        print("3. Execute ordem atual (opcao 7 ou 8)")
        print("4. Sistema avanca automaticamente para proxima ordem")
        print("5. Repita o processo")
        print()
        
        print("SISTEMA DE ORDENS:")
        print("-" * 18)
        print("• Cada execucao processa APENAS a ordem atual")
        print("• Apos execucao, ordem incrementa automaticamente")
        print("• Novos pedidos vao sempre para ordem atual")
        print("• Isso evita conflitos e organiza historico")
        print()
        
        print("LIMPEZA AUTOMATICA:")
        print("-" * 19)
        print("• Logs limpos na inicializacao")
        print("• Comandas removidas automaticamente")
        print("• Pedidos salvos limpos apos execucao bem-sucedida")
        print("• Ambiente sempre pronto para nova sessao")
        print()
        
        print("AGENDA DE EQUIPAMENTOS:")
        print("-" * 23)
        print("• Visualizacao baseada em logs (sempre disponivel)")
        print("• Integracao com sistema real (quando ativo)")
        print("• Timeline por ordem/pedido")
        print("• Deteccao de conflitos de horario")
        print()
        
        print("LIBERACAO DE EQUIPAMENTOS:")
        print("-" * 26)
        print("• Sistema modular para diferentes tipos")
        print("• Deteccao automatica de estruturas")
        print("• Bancadas, camaras, armarios, equipamentos padrao")
        print("• Relatorio detalhado de liberacoes")
        print()
        
        print("DICAS:")
        print("-" * 6)
        print("• Use 'Testar Sistema' antes da primeira execucao")
        print("• SEQUENCIAL e mais rapido, OTIMIZADO e mais eficiente")
        print("• Agenda mostra historico de todas as execucoes")
        print("• Sistema salva automaticamente apos cada operacao")
        print("• Use Debug para investigar problemas")
        print("• Cancelar pedido libera equipamentos automaticamente")
        
        input("\nPressione Enter para continuar...")
    
    def sair(self):
        """Encerra o sistema"""
        print("\nEncerrando Sistema de Producao...")
        print("Sistema salvo automaticamente.")
        print("Ate a proxima!")
        self.rodando = False


# =====================================================================
#                           PONTO DE ENTRADA
# =====================================================================

def main():
    """Funcao principal"""
    try:
        menu = MenuPrincipal()
        menu.executar()
    except KeyboardInterrupt:
        print("\n\nSistema interrompido pelo usuario.")
    except Exception as e:
        print(f"\nErro critico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Sistema encerrado.")


if __name__ == "__main__":
    main()