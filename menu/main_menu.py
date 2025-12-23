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
import re
import sys
import csv
from typing import Optional
from datetime import datetime

# Adiciona paths necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu.gerenciador_pedidos import GerenciadorPedidos
from menu.utils_menu import MenuUtils
from services.gestores.producao import GestorProducao
from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios
from services.validacao.validador_pedidos import ValidadorPedidos
from services.exportacao.exportador_banco import ExportadorBanco
from utils.logs.gerenciador_logs import limpar_logs_inicializacao, limpar_escalas_inicializacao
from analisador.analisador_pedidos import AnalisadorPedidos
from analisador.calculador_reagendamento import CalculadorReagendamento


class MenuPrincipal:
    """Menu principal do sistema de produção com controle de ordens"""
    
    def __init__(self):
        print("🚀 Inicializando Sistema de Produção...")
        
        # 🆕 LIMPEZA AUTOMÁTICA DE LOGS, COMANDAS E ESCALAS
        try:
            # 🆕 MODIFICAÇÃO: Agora limpar_logs_inicializacao() já inclui limpeza de comandas
            from utils.comandas.limpador_comandas import apagar_todas_as_comandas
            relatorio_limpeza = limpar_logs_inicializacao()
            apagar_todas_as_comandas()
            limpar_escalas_inicializacao()  # 🆕 Limpa escalas Excel anteriores

            # Como agora retorna string formatada, vamos exibir
            if isinstance(relatorio_limpeza, str):
                print(relatorio_limpeza)
            else:
                # Compatibilidade com versão antiga
                if relatorio_limpeza['sucesso']:
                    if relatorio_limpeza['total_arquivos_removidos'] > 0:
                        print("✅ Ambiente de logs, comandas e escalas limpo e pronto!")
                    else:
                        print("🔭 Ambiente de logs, comandas e escalas já estava limpo!")
                else:
                    print("⚠️ Limpeza concluída com alguns erros (sistema continuará)")

        except Exception as e:
            print(f"⚠️ Erro durante limpeza de logs/comandas/escalas: {e}")
            print("🔄 Sistema continuará normalmente...")
        
        print("🔧 Carregando nova arquitetura desacoplada...")
        
        # Inicializa componentes
        self.gerenciador = GerenciadorPedidos()
        self.gestor_producao = GestorProducao()  # ✅ NOVO: Usa GestorProducao independente
        self.gestor_funcionarios = GestorFuncionarios()  # ✅ SINGLETON: Uma única instância para toda sessão
        self.validador_pedidos = ValidadorPedidos()  # ✅ NOVO: Validador de pedidos
        self.exportador_banco = ExportadorBanco()  # ✅ NOVO: Exportador para banco
        self.utils = MenuUtils()
        self.rodando = True

        print("✅ Sistema inicializado com arquitetura independente!")
        print(f"📦 Sistema de Ordens ativo - Ordem atual: {self.gerenciador.obter_ordem_atual()}")
        print(f"👷 GestorFuncionarios: {len(self.gestor_funcionarios.funcionarios_disponiveis)} funcionários disponíveis")

    
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
        print("1️⃣  Registrar Pedidos")
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
        print("E️⃣  Visualizar Equipamentos em Memória")
        print()
        print("👥 FUNCIONÁRIOS:")
        print("F️⃣  Gestão de Funcionários")
        print()
        print("📦 ALMOXARIFADO:")
        print("G️⃣  Gestão de Almoxarifado")
        print()
        print("✅ VALIDAÇÃO E EXPORTAÇÃO:")  # 🆕 NOVA SEÇÃO
        print("I️⃣  Validação e Exportação para Banco")
        print()
        print("📊 ESCALAS:")
        print("J️⃣  Gerar Escala de Funcionários (Excel)")
        print()
        print("🔍 AVALIADOR DE PEDIDOS:")
        print("H️⃣  Analisar Pedidos (Atividades e Reagendamento)")
        print()
        print("⚙️ SISTEMA:")
        print("T️⃣  Testar Sistema")
        print("0️⃣  Configurações")
        print("R️⃣  Recuperar Estado (via Logs Detalhados)")
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
            self.mostrar_submenu_registro_pedidos()
        
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

        elif opcao.lower() == "e":  # 🆕 NOVA OPÇÃO - VISUALIZAR EQUIPAMENTOS
            self.visualizar_equipamentos()

        elif opcao.lower() == "f":  # 🆕 NOVA OPÇÃO - FUNCIONÁRIOS
            self.mostrar_submenu_funcionarios()

        elif opcao.lower() == "g":  # 🆕 NOVA OPÇÃO - ALMOXARIFADO
            self.mostrar_submenu_almoxarifado()

        elif opcao.lower() == "i":  # 🆕 NOVA OPÇÃO - VALIDAÇÃO E EXPORTAÇÃO
            self.mostrar_submenu_validacao_exportacao()

        elif opcao.lower() == "h":  # 🆕 NOVA OPÇÃO - AVALIADOR DE PEDIDOS
            self.mostrar_submenu_avaliador_pedidos()

        elif opcao.lower() == "j":  # 🆕 NOVA OPÇÃO - GERAR ESCALA
            self.gerar_escala_funcionarios()

        elif opcao.lower() == "t":  # OPÇÃO MOVIDA - TESTAR SISTEMA
            self.testar_sistema()

        elif opcao == "0":
            self.mostrar_configuracoes()
        

        elif opcao.lower() == "r":
            self.recuperar_estado_logs()
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
                    print("5️⃣  Estatísticas de Utilização")
                    print("6️⃣  Timeline por Ordem/Pedido")
                    print("7️⃣  Verificar Conflitos de Horário")
                    print("8️⃣  Exportar Agenda para Arquivo TXT")
                    print("9️⃣  Gerar Relatório PDF de Escala e Pedidos")
                    print("R️⃣  Recarregar Dados dos Logs")
                    print()
                    print("🔧 SISTEMA REAL DE EQUIPAMENTOS:")
                    if integrador.sistema_disponivel():
                        print("T️⃣  Agenda de Equipamento Real (mostrar_agenda)")
                        print("U️⃣  Agenda de Gestor por Tipo")
                        print("W️⃣  Listar Todos os Equipamentos Disponíveis")
                        print("X️⃣  Verificar Status de Equipamento")
                    else:
                        print("T️⃣  [INDISPONÍVEL] Sistema de equipamentos não carregado")
                        print("U️⃣  [INDISPONÍVEL] Gestores não acessíveis")
                    print()
                    print("[V]  Voltar ao Menu Principal")
                    print("─" * 60)

                    opcao_agenda = input("🎯 Escolha uma opção: ").strip().lower()

                    # Processa opções tradicionais (baseadas em logs)
                    if opcao_agenda in ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'r']:
                        visualizador.processar_opcao_agenda(opcao_agenda)
                        input("\nPressione Enter para continuar...")

                    # Processa opções do sistema real
                    elif opcao_agenda == 't':
                        self._agenda_equipamento_real(integrador)
                        input("\nPressione Enter para continuar...")
                    elif opcao_agenda == 'u':
                        self._agenda_gestor_tipo(integrador)
                        input("\nPressione Enter para continuar...")
                    elif opcao_agenda == 'w':
                        self._listar_equipamentos_reais(integrador)
                        input("\nPressione Enter para continuar...")
                    elif opcao_agenda == 'x':
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

    def mostrar_submenu_registro_pedidos(self):
        """Submenu para escolha entre registro manual ou por CSV"""
        rodando_submenu = True

        while rodando_submenu:
            try:
                self.utils.limpar_tela()
                print("📋 REGISTRO DE PEDIDOS")
                print("=" * 40)
                print()
                print("🔹 Como deseja registrar o pedido?")
                print()
                print("1️⃣ Registro Manual (Terminal)")
                print("2️⃣ Registro por CSV (Arquivo)")
                print()
                print("V - Voltar ao menu principal")
                print()

                opcao = input("🎯 Escolha uma opção: ").strip().upper()

                if opcao == "1":
                    self.registrar_pedido_manual()
                elif opcao == "2":
                    self.registrar_pedido_csv()
                elif opcao == "V":
                    rodando_submenu = False
                else:
                    print("\n❌ Opção inválida!")
                    input("Pressione Enter para continuar...")

            except KeyboardInterrupt:
                print("\n\n📋 Voltando ao menu principal...")
                rodando_submenu = False
            except Exception as e:
                print(f"\n⚠️ Erro no submenu de registro: {e}")
                input("Pressione Enter para continuar...")

    def registrar_pedido_manual(self):
        """Interface para registrar novo pedido manualmente"""
        self.utils.limpar_tela()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        proximo_pedido = len(self.gerenciador.obter_pedidos_ordem_atual()) + 1

        print("📋 REGISTRAR PEDIDO MANUAL")
        print("=" * 40)
        print(f"📦 Ordem: {ordem_atual}")
        print(f"🎯 Próximo Pedido: {proximo_pedido}")
        print(f"🏷️ Será registrado como: Ordem {ordem_atual} | Pedido {proximo_pedido}")
        print()

        try:
            dados_pedido = self.utils.coletar_dados_pedido()

            if dados_pedido:
                sucesso, mensagem = self.gerenciador.registrar_pedido(**dados_pedido)

                if sucesso:
                    print(f"\n✅ {mensagem}")
                    self.gerenciador.salvar_pedidos()
                else:
                    print(f"\n⚡ {mensagem}")
            else:
                print("\nℹ️ Registro cancelado.")

        except Exception as e:
            print(f"\n⚡ Erro ao registrar pedido: {e}")

        input("\nPressione Enter para continuar...")

    def registrar_pedido_csv(self):
        """Interface para registrar pedidos a partir de arquivo CSV"""
        self.utils.limpar_tela()
        print("📋 REGISTRAR PEDIDOS POR CSV")
        print("=" * 40)
        print()
        print("📁 Pasta CSV: data/csv/")
        print("📋 Formato esperado: id, tipo_produto, quantidade, fim_jornada")
        print("📅 Data formato: YYYY-MM-DD HH:MM:SS")
        print()

        # Lista arquivos CSV disponíveis
        csv_dir = "data/csv"
        if not os.path.exists(csv_dir):
            print("❌ Pasta 'data/csv' não encontrada!")
            input("Pressione Enter para continuar...")
            return

        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]

        if not csv_files:
            print("❌ Nenhum arquivo CSV encontrado na pasta 'data/csv'!")
            print("💡 Coloque seu arquivo CSV na pasta 'data/csv' e tente novamente.")
            input("Pressione Enter para continuar...")
            return

        print("📂 Arquivos CSV disponíveis:")
        for i, arquivo in enumerate(csv_files, 1):
            print(f"   {i}. {arquivo}")
        print()

        try:
            escolha = input("🎯 Digite o número do arquivo ou 'V' para voltar: ").strip()

            if escolha.upper() == 'V':
                return

            indice = int(escolha) - 1
            if 0 <= indice < len(csv_files):
                arquivo_escolhido = csv_files[indice]
                self.processar_arquivo_csv(os.path.join(csv_dir, arquivo_escolhido))
            else:
                print("❌ Número inválido!")
                input("Pressione Enter para continuar...")

        except ValueError:
            print("❌ Entrada inválida!")
            input("Pressione Enter para continuar...")
        except Exception as e:
            print(f"⚡ Erro: {e}")
            input("Pressione Enter para continuar...")

    def processar_arquivo_csv(self, caminho_arquivo):
        """Processa arquivo CSV e registra pedidos"""
        try:
            pedidos_registrados = 0
            erros = []

            print(f"\n📂 Processando: {os.path.basename(caminho_arquivo)}")
            print("=" * 50)

            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                reader = csv.DictReader(arquivo)

                # Valida cabeçalhos
                colunas_esperadas = {'id', 'tipo_produto', 'quantidade', 'fim_jornada'}
                if not colunas_esperadas.issubset(set(reader.fieldnames)):
                    print(f"❌ Colunas inválidas!")
                    print(f"📋 Esperado: {', '.join(colunas_esperadas)}")
                    print(f"📋 Encontrado: {', '.join(reader.fieldnames)}")
                    input("Pressione Enter para continuar...")
                    return

                for linha_num, linha in enumerate(reader, 2):  # +2 pois linha 1 é cabeçalho
                    try:
                        # Converte dados
                        id_item = int(linha['id'].strip())
                        tipo_item = linha['tipo_produto'].strip().upper()
                        quantidade = int(linha['quantidade'].strip())
                        fim_jornada_str = linha['fim_jornada'].strip()

                        # Converte data
                        fim_jornada = datetime.strptime(fim_jornada_str, '%Y-%m-%d %H:%M:%S')

                        # Valida tipo
                        if tipo_item not in ['PRODUTO', 'SUBPRODUTO']:
                            raise ValueError(f"Tipo inválido: {tipo_item}")

                        # Registra pedido
                        sucesso, mensagem = self.gerenciador.registrar_pedido(
                            id_item=id_item,
                            tipo_item=tipo_item,
                            quantidade=quantidade,
                            fim_jornada=fim_jornada
                        )

                        if sucesso:
                            pedidos_registrados += 1
                            print(f"✅ Linha {linha_num}: Pedido {id_item} registrado")
                        else:
                            erros.append(f"Linha {linha_num}: {mensagem}")
                            print(f"❌ Linha {linha_num}: {mensagem}")

                    except Exception as e:
                        erro_msg = f"Linha {linha_num}: {str(e)}"
                        erros.append(erro_msg)
                        print(f"❌ {erro_msg}")

            # Salva pedidos se houve registros bem-sucedidos
            if pedidos_registrados > 0:
                self.gerenciador.salvar_pedidos()

            # Relatório final
            print("\n" + "=" * 50)
            print("📊 RELATÓRIO DE IMPORTAÇÃO")
            print("=" * 50)
            print(f"✅ Pedidos registrados: {pedidos_registrados}")
            print(f"❌ Erros encontrados: {len(erros)}")

            if erros:
                print("\n📝 DETALHES DOS ERROS:")
                for erro in erros:
                    print(f"   • {erro}")

        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        except Exception as e:
            print(f"⚡ Erro ao processar CSV: {e}")

        input("\nPressione Enter para continuar...")

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

                    # Apaga os arquivos relacionados ao pedido cancelado
                    import os
                    import glob
                    arquivos_removidos = 0

                    # 1. Remove log de equipamentos
                    log_path = f"logs/equipamentos/ordem: {id_ordem} | pedido: {id_pedido}.log"
                    if os.path.exists(log_path):
                        os.remove(log_path)
                        arquivos_removidos += 1
                        print(f"\n📄 Log de equipamentos removido: {log_path}")

                    # 2. Remove comanda
                    comanda_path = f"data/comandas/comanda_ordem_{id_ordem}_pedido_{id_pedido}.json"
                    if os.path.exists(comanda_path):
                        os.remove(comanda_path)
                        arquivos_removidos += 1
                        print(f"📋 Comanda removida: {comanda_path}")

                    # 3. Remove logs de erro (ambos os formatos possíveis)
                    erro_log_path = f"logs/equipamentos/erros/ordem: {id_ordem} | pedido: {id_pedido}.log"
                    if os.path.exists(erro_log_path):
                        os.remove(erro_log_path)
                        arquivos_removidos += 1
                        print(f"⚠️ Log de erro removido: {erro_log_path}")

                    erro_json_path = f"logs/equipamentos/erros/ordem_{id_ordem}_pedido_{id_pedido}_temporal_errors.json"
                    if os.path.exists(erro_json_path):
                        os.remove(erro_json_path)
                        arquivos_removidos += 1
                        print(f"⚠️ Arquivo de erros temporais removido: {erro_json_path}")

                    # 4. Remove logs detalhados de equipamentos que contenham este pedido
                    # Padrão: ocupacoes_detalhadas_ordem_X_pedidos_..._Y_...*.log
                    pattern = f"logs/equipamentos_detalhados/ocupacoes_detalhadas_ordem_{id_ordem}_pedidos_*{id_pedido}*.log"
                    logs_detalhados = glob.glob(pattern)
                    for log_detalhado in logs_detalhados:
                        os.remove(log_detalhado)
                        arquivos_removidos += 1
                        print(f"📊 Log detalhado removido: {log_detalhado}")

                    # 5. Remove logs de tipos de funcionários requeridos
                    func_req_path = f"logs/tipos_funcionarios_requeridos/ordem: {id_ordem} | pedido: {id_pedido}.log"
                    if os.path.exists(func_req_path):
                        os.remove(func_req_path)
                        arquivos_removidos += 1
                        print(f"👥 Log de funcionários requeridos removido: {func_req_path}")

                    # 6. Remove o pedido da lista de pedidos registrados
                    sucesso, mensagem = self.gerenciador.remover_pedido(id_ordem, id_pedido)
                    if sucesso:
                        print(f"📋 Pedido removido da lista de pedidos registrados")

                    print(f"\n✅ Ordem {id_ordem} | Pedido {id_pedido} cancelado com sucesso!")
                    print(f"🗑️ {arquivos_removidos} arquivo(s) removido(s)")

                    if equipamentos_liberados > 0:
                        print(f"🔧 {equipamentos_liberados} equipamento(s) liberado(s)")
                    else:
                        print("ℹ️ Nenhum equipamento estava alocado ou já havia sido liberado")

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
            from services.gestores.equipamentos.liberador_equipamentos import LiberadorEquipamentos
            
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
            try:
                # Executa apenas pedidos da ordem atual
                sucesso = self.gestor_producao.executar_sequencial(pedidos_ordem)
                
                # 🆕 SEMPRE incrementa ordem após tentativa de execução (sucesso ou falha)
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()  # Salva nova ordem
                
                if sucesso:
                    print(f"\n🎉 Execução sequencial da Ordem {ordem_atual} concluída!")
                    print(f"📈 Sistema avançou para Ordem {nova_ordem}")
                    print("💡 Novos pedidos serão registrados na nova ordem")

                    # 🆕 CAPTURA DE OCUPAÇÕES DETALHADAS DOS EQUIPAMENTOS
                    try:
                        from utils.logs.capturador_ocupacoes_equipamentos import CapturadorOcupacoes
                        print("\n🔍 CAPTURANDO OCUPAÇÕES DETALHADAS DOS EQUIPAMENTOS ATIVOS...")
                        print("=" * 60)

                        capturador = CapturadorOcupacoes()
                        pedidos_ids = [p.id_pedido for p in pedidos_ordem]

                        # Gera relatório com ocupações detalhadas
                        arquivo_relatorio = capturador.gerar_relatorio_ocupacoes_detalhadas(
                            id_ordem=ordem_atual,
                            pedidos_inclusos=pedidos_ids,
                            salvar_arquivo=True
                        )

                        if arquivo_relatorio:
                            print(f"📄 Relatório detalhado salvo: {arquivo_relatorio}")
                        else:
                            print("⚠️ Não foi possível gerar relatório detalhado")

                    except Exception as e:
                        print(f"⚠️ Erro ao capturar ocupações detalhadas: {e}")

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
        """Executa pedidos da ordem atual com otimização PL (Unificado: DETERMINÍSTICO e FLEXÍVEL)"""
        self.utils.limpar_tela()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        pedidos_ordem = self.gerenciador.obter_pedidos_ordem_atual()

        print("🚀 EXECUÇÃO OTIMIZADA PL")
        print("=" * 50)
        print(f"📦 Executando Ordem: {ordem_atual}")
        print("✨ Suporte a janelas temporais flexíveis (tau_max > 0)")
        print("📊 Detecta modo automaticamente (DETERMINÍSTICO ou FLEXÍVEL)")

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
        print("\n🔧 Método: Otimizador PL Unificado")
        print("📋 Características:")
        print("   ✅ FASE 0: Cria atividades modulares")
        print("   ✅ Detecta modo (DETERMINÍSTICO ou FLEXÍVEL)")
        print("   ✅ Calcula janelas temporais se tau_max > 0")
        print("   ✅ Retry dentro das janelas se alocação falhar")
        print("🧹 Ambiente limpo automaticamente")
        print("📦 SISTEMA DE ORDENS: Execução por ordem/sessão")

        # Mostra resumo dos pedidos da ordem atual
        print(f"\n📋 Pedidos da Ordem {ordem_atual} para otimização:")
        for pedido in pedidos_ordem:
            print(f"   • Ordem {pedido.id_ordem} | Pedido {pedido.id_pedido}: {pedido.nome_item} ({pedido.quantidade} uni)")
            print(f"     Prazo: {pedido.fim_jornada.strftime('%d/%m %H:%M')}")

        confirmacao = input(f"\n🎯 Confirma execução otimizada da Ordem {ordem_atual}? (s/N): ").strip().lower()

        if confirmacao in ['s', 'sim', 'y', 'yes']:
            try:
                # Importar Executor
                print("\n📥 Importando Otimizador...")
                from otimizador import Executor

                # Criar executor
                print("🔧 Criando executor...")
                executor = Executor()

                # Inicializar
                print("⚙️ Inicializando ambiente...")
                if not executor.inicializar():
                    print("❌ Erro ao inicializar executor")
                    input("\nPressione Enter para continuar...")
                    return

                # Converter DadosPedidoMenu para PedidoDeProducao
                print("🔄 Convertendo pedidos do menu para formato de produção...")
                from services.gestores.producao.conversor_pedidos import ConversorPedidos
                conversor = ConversorPedidos(
                    gestor_almoxarifado=executor.configurador.gestor_almoxarifado
                )
                pedidos_convertidos = conversor.converter_pedidos(pedidos_ordem)

                if not pedidos_convertidos:
                    print("❌ Erro ao converter pedidos")
                    input("\nPressione Enter para continuar...")
                    return

                print(f"✅ {len(pedidos_convertidos)} pedido(s) convertido(s) com sucesso")

                # Executar otimização
                print(f"\n🚀 Executando otimização com {len(pedidos_convertidos)} pedidos...")
                solucao = executor.otimizar_pedidos(
                    pedidos=pedidos_convertidos,
                    timeout_segundos=600
                )

                # Sempre incrementa ordem após tentativa de execução
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()

                if solucao and solucao.pedidos_atendidos > 0:
                    print(f"\n🎉 Execução otimizada da Ordem {ordem_atual} concluída!")
                    print(f"📈 Sistema avançou para Ordem {nova_ordem}")
                    print("💡 Novos pedidos serão registrados na nova ordem")

                    # Mostrar resumo
                    executor.imprimir_resumo_solucao(solucao, pedidos_convertidos)

                    # Comparar com baseline se for 13 pedidos
                    if len(pedidos_convertidos) == 13:
                        executor.comparar_com_baseline(solucao, 13)

                    # Mostrar estatísticas
                    print(f"\n📊 ESTATÍSTICAS:")
                    print(f"   Status Solver: {solucao.status_solver}")
                    print(f"   Modo Detectado: {solucao.modo_detectado}")
                    print(f"   Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos_convertidos)}")
                    print(f"   Taxa de sucesso: {(solucao.pedidos_atendidos/len(pedidos_convertidos)*100):.1f}%")
                    print(f"   Tempo de resolução: {solucao.tempo_resolucao:.2f}s")
                    print(f"   Makespan: {solucao.makespan_minutos:.0f} min ({solucao.makespan_minutos/60:.1f}h)")

                    # Detalhes do modo
                    print(f"\n📊 Detalhes:")
                    print(f"   Pedidos determinísticos: {solucao.estatisticas.get('pedidos_deterministicos', 0)}")
                    print(f"   Pedidos flexíveis: {solucao.estatisticas.get('pedidos_flexiveis', 0)}")
                    print(f"   Atividades com gap > 0: {solucao.estatisticas.get('atividades_com_gap', 0)}")

                    if solucao.janelas_calculadas:
                        print(f"   Janelas flexíveis calculadas: {len(solucao.janelas_calculadas)} pedidos")

                else:
                    print(f"\n⚡ Execução otimizada não encontrou solução viável para Ordem {ordem_atual}!")
                    print(f"📈 Mesmo assim, sistema avançou para Ordem {nova_ordem}")
                    print("💡 Possíveis causas:")
                    print("   - Deadlines muito apertados")
                    print("   - Conflitos de equipamentos insolúveis")
                    print("   - tau_max insuficiente para flexibilidade")
                    print("   - Timeout atingido antes de encontrar solução")

                    if solucao:
                        print(f"\n   Status do solver: {solucao.status_solver}")
                        print(f"   Modo detectado: {solucao.modo_detectado}")

            except ImportError as e:
                print(f"\n⚡ Erro ao importar Otimizador: {e}")
                print("💡 Verifique se o módulo otimizador está instalado corretamente")
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()
                print(f"📈 Ordem incrementada para {nova_ordem} (devido ao erro)")

            except Exception as e:
                # Mesmo em caso de exception, incrementa ordem
                print(f"\n⚡ Erro durante execução otimizada: {e}")
                import traceback
                traceback.print_exc()
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()
                print(f"📈 Ordem incrementada para {nova_ordem} (devido ao erro)")
                print("💡 Isso evita conflitos de IDs em futuras execuções")
        else:
            print("\nℹ️ Execução cancelada.")

        input("\nPressione Enter para continuar...")

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
        print("6 - Limpar apenas arquivo de pedidos salvos")
        print("7 - Limpar cache Python (__pycache__ e .pyc)")
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
                "4": "logs/equipamentos/erros",
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
        
        elif opcao == "6":
            print(f"\n🧹 Limpando arquivo de pedidos salvos...")
            try:
                from utils.logs.gerenciador_logs import limpar_arquivo_pedidos_salvos
                if limpar_arquivo_pedidos_salvos():
                    print("✅ Arquivo de pedidos salvos removido")
                else:
                    print("📄 Arquivo de pedidos salvos não existia")
            except Exception as e:
                print(f"⚡ Erro ao limpar arquivo de pedidos: {e}")

        elif opcao == "7":
            print(f"\n🧹 Limpando cache Python...")
            try:
                import shutil
                arquivos_removidos = 0
                pastas_removidas = 0

                # Remove __pycache__ directories
                for root, dirs, files in os.walk('.'):
                    if '__pycache__' in dirs:
                        pycache_path = os.path.join(root, '__pycache__')
                        shutil.rmtree(pycache_path)
                        pastas_removidas += 1
                        print(f"   🗑️ Removido: {pycache_path}")

                    # Remove .pyc files
                    for file in files:
                        if file.endswith('.pyc'):
                            pyc_path = os.path.join(root, file)
                            os.remove(pyc_path)
                            arquivos_removidos += 1

                print(f"\n✅ Cache limpo!")
                print(f"   📁 {pastas_removidas} pasta(s) __pycache__ removida(s)")
                print(f"   📄 {arquivos_removidos} arquivo(s) .pyc removido(s)")

            except Exception as e:
                print(f"⚡ Erro ao limpar cache: {e}")

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
    
    # =========================================================================
    #                       🆕 SUBMENU GESTÃO DE ALMOXARIFADO
    # =========================================================================
    
    def mostrar_submenu_almoxarifado(self):
        """Submenu para gestão de almoxarifado"""
        try:
            rodando_almoxarifado = True
            
            while rodando_almoxarifado:
                try:
                    self.utils.limpar_tela()
                    print("📦 GESTÃO DE ALMOXARIFADO")
                    print("=" * 50)
                    
                    # Inicializa sistema se necessário para status
                    if not self.gestor_producao.sistema_inicializado:
                        print("🔧 Sistema não inicializado")
                        print("   (Será inicializado automaticamente ao usar as opções)")
                    else:
                        almox = self.gestor_producao.configurador_ambiente.gestor_almoxarifado
                        total_itens = len(almox.almoxarifado.itens)
                        print(f"📊 Status: {total_itens} itens carregados no almoxarifado")
                    
                    print("\n📋 OPÇÕES DISPONÍVEIS:")
                    print("1️⃣  Processar Comandas (Reservar Itens)")
                    print("2️⃣  Despachar Reservas (Consumir Almoxarifado)")
                    print("3️⃣  Verificar Estoque (Itens Abaixo do Mínimo)")
                    print("4️⃣  Listar Todos os Itens")
                    print("5️⃣  🔄 Executar Ordem de Reabastecimento")
                    print("\nV️⃣  Voltar ao Menu Principal")
                    print("=" * 50)

                    opcao_almox = input("\n🎯 Escolha uma opção: ").strip().upper()

                    if opcao_almox == '1':
                        self.processar_comandas()
                    elif opcao_almox == '2':
                        self.despachar_reservas()
                    elif opcao_almox == '3':
                        self.verificar_estoque_minimo()
                    elif opcao_almox == '4':
                        self.listar_todos_os_itens_almoxarifado()
                    elif opcao_almox == '5':
                        self.executar_ordem_reabastecimento()
                    elif opcao_almox == 'V':
                        rodando_almoxarifado = False
                    else:
                        print(f"\n⚠️ Opção '{opcao_almox}' inválida!")
                        input("Pressione Enter para continuar...")
                        
                except KeyboardInterrupt:
                    print("\n\n📦 Voltando ao menu principal...")
                    rodando_almoxarifado = False
                except Exception as e:
                    print(f"\n⚠️ Erro no submenu de almoxarifado: {e}")
                    input("Pressione Enter para continuar...")
            
        except Exception as e:
            print(f"\n⚠️ Erro inesperado no submenu de almoxarifado: {e}")
            input("Pressione Enter para continuar...")
    
    def verificar_estoque_minimo(self):
        """Verifica itens com estoque abaixo do mínimo"""
        self.utils.limpar_tela()
        print("📊 VERIFICAÇÃO DE ESTOQUE MÍNIMO")
        print("=" * 50)
        
        try:
            # Inicializa o sistema se necessário
            if not self.gestor_producao.sistema_inicializado:
                print("🔧 Inicializando sistema...")
                if not self.gestor_producao._inicializar_sistema():
                    print("❌ Erro ao inicializar sistema")
                    input("\nPressione Enter para continuar...")
                    return
            
            print("🔍 Fazendo varredura no estoque...")
            
            # Usa o método do gestor almoxarifado para verificar estoque mínimo
            itens_alerta = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.verificar_estoque_minimo()
            
            print(f"📋 Varredura concluída!")
            
            if not itens_alerta:
                print("\n✅ Todos os itens estão com estoque adequado!")
                print("🎉 Nenhum item abaixo do mínimo encontrado")
            else:
                print(f"\n⚠️ {len(itens_alerta)} item(ns) abaixo do estoque mínimo:")
                print("\n" + "=" * 80)
                print(f"{'ITEM':<35} {'ATUAL':<12} {'MÍNIMO':<12} {'FALTA':<12} {'DIAS':<8}")
                print("=" * 80)
                
                for item in itens_alerta:
                    nome = item['descricao'][:34]  # Limita o nome para caber na tabela
                    atual = f"{item['estoque_atual']:.1f}"
                    minimo = f"{item['estoque_min']:.1f}"
                    falta = f"{item['falta']:.1f}"
                    unidade = item['unidade']
                    
                    # Calcula dias restantes
                    dias = item.get('dias_restantes')
                    if dias is not None:
                        if dias <= 0:
                            dias_str = "0"
                        elif dias < 1:
                            dias_str = "<1"
                        else:
                            dias_str = f"{dias:.1f}"
                    else:
                        dias_str = "N/A"
                    
                    print(f"{nome:<35} {atual:<12} {minimo:<12} {falta:<12} {dias_str:<8}")
                    print(f"{'ID: ' + str(item['id_item']):<35} {unidade:<12} {unidade:<12} {unidade:<12} {'dias':<8}")
                    print("-" * 80)
                
                # Resumo com dicas
                print(f"\n📊 RESUMO:")
                print(f"   ⚠️ Itens críticos: {len([i for i in itens_alerta if i.get('dias_restantes') is None or (i.get('dias_restantes') is not None and i.get('dias_restantes', 0) <= 1)])}")
                print(f"   📋 Total de itens em alerta: {len(itens_alerta)}")
                
                # Itens mais críticos (sem dias ou com menos de 1 dia)
                criticos = [i for i in itens_alerta if i.get('dias_restantes') is None or (i.get('dias_restantes') is not None and i.get('dias_restantes', 0) <= 1)]
                if criticos:
                    print(f"\n🚨 ATENÇÃO: {len(criticos)} item(ns) em situação crítica:")
                    for item in criticos[:5]:  # Mostra até 5 mais críticos
                        print(f"   • {item['descricao']}: {item['estoque_atual']:.1f} {item['unidade']}")
                    if len(criticos) > 5:
                        print(f"   ... e mais {len(criticos) - 5} itens")
                
                print("\n💡 DICAS:")
                print("   • Verifique fornecedores para itens em falta")
                print("   • Considere ajustar quantidades mínimas se necessário")

                # Oferecer geração de CSV de reabastecimento
                self._oferecer_geracao_csv_reabastecimento()

        except Exception as e:
            print(f"⚠️ Erro ao verificar estoque: {e}")

        input("\nPressione Enter para continuar...")
    
    def listar_todos_os_itens_almoxarifado(self):
        """Lista todos os itens do almoxarifado com informações detalhadas"""
        self.utils.limpar_tela()
        print("📋 LISTAGEM COMPLETA DO ALMOXARIFADO")
        print("=" * 80)
        
        try:
            # Inicializa o sistema se necessário
            if not self.gestor_producao.sistema_inicializado:
                print("🔧 Inicializando sistema...")
                if not self.gestor_producao._inicializar_sistema():
                    print("❌ Erro ao inicializar sistema")
                    input("\nPressione Enter para continuar...")
                    return
            
            print("📦 Carregando todos os itens do almoxarifado...")
            
            # Obter todos os itens através do gestor
            itens = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.listar_todos_os_itens()
            
            if not itens:
                print("📭 Nenhum item encontrado no almoxarifado")
                input("\nPressione Enter para continuar...")
                return
            
            print(f"📊 Total: {len(itens)} itens encontrados")
            print("\n" + "=" * 80)
            print(f"{'ID':<6} {'NOME':<35} {'TIPO':<12} {'ESTOQUE':<12} {'POLÍTICA':<12}")
            print("=" * 80)
            
            # Agrupar por tipo para melhor organização
            tipos = {}
            for item in itens:
                tipo = item.tipo_item.value
                if tipo not in tipos:
                    tipos[tipo] = []
                tipos[tipo].append(item)
            
            # Ordenar tipos e exibir
            for tipo in sorted(tipos.keys()):
                print(f"\n🏷️  {tipo}:")
                print("-" * 80)
                
                itens_do_tipo = sorted(tipos[tipo], key=lambda x: x.id_item)
                
                for item in itens_do_tipo:
                    # Formatação do estoque
                    estoque_str = f"{item.estoque_atual:.1f} {item.unidade_medida.value}"
                    if len(estoque_str) > 12:
                        estoque_str = estoque_str[:12]
                    
                    # Formatação da política
                    politica_str = item.politica_producao.value
                    if len(politica_str) > 12:
                        politica_str = politica_str[:12]
                    
                    # Status do estoque
                    if item.esta_abaixo_do_minimo():
                        status = "⚠️"
                    elif item.estoque_atual == 0:
                        status = "❌"
                    else:
                        status = "✅"
                    
                    nome_item = item.descricao[:34] if len(item.descricao) > 34 else item.descricao
                    
                    print(f"{item.id_item:<6} {nome_item:<35} {tipo[:11]:<12} {estoque_str:<12} {politica_str:<12} {status}")
            
            print("\n" + "=" * 80)
            print("💡 LEGENDA:")
            print("   ✅ Estoque normal")
            print("   ⚠️  Abaixo do mínimo")
            print("   ❌ Sem estoque")
            print("   📊 Políticas: SOB_DEMANDA (produzido quando necessário), ESTOCADO (mantém estoque)")
            
        except Exception as e:
            print(f"⚠️ Erro ao listar itens: {e}")
        
        input("\nPressione Enter para continuar...")

    def processar_comandas(self):
        """Processa comandas e reserva itens do almoxarifado"""
        self.utils.limpar_tela()
        print("📦 PROCESSAR COMANDAS - RESERVAR ITENS")
        print("=" * 50)
        
        try:
            # Inicializa o sistema se necessário
            if not self.gestor_producao.sistema_inicializado:
                print("🔧 Inicializando sistema...")
                if not self.gestor_producao._inicializar_sistema():
                    print("❌ Erro ao inicializar sistema")
                    input("\nPressione Enter para continuar...")
                    return
            
            from parser.gerenciador_json_comandas import ler_comandas_em_pasta
            
            # Lê comandas da pasta padrão
            pasta_comandas = "data/comandas"
            print(f"📂 Lendo comandas da pasta: {pasta_comandas}")
            
            # Verifica se a pasta existe
            if not os.path.exists(pasta_comandas):
                print(f"⚠️ Pasta de comandas não encontrada: {pasta_comandas}")
                print("💡 Execute primeiro um pedido para gerar comandas")
                input("\nPressione Enter para continuar...")
                return
            
            # Lista arquivos de comanda
            import glob
            arquivos_comanda = glob.glob(f"{pasta_comandas}/*.json")
            
            if not arquivos_comanda:
                print(f"📭 Nenhuma comanda encontrada em: {pasta_comandas}")
                print("💡 Execute primeiro um pedido para gerar comandas")
                input("\nPressione Enter para continuar...")
                return
            
            print(f"📋 {len(arquivos_comanda)} arquivo(s) de comanda encontrado(s):")
            for arquivo in sorted(arquivos_comanda):
                nome_arquivo = os.path.basename(arquivo)
                print(f"   • {nome_arquivo}")
            
            print("\n⚠️ ATENÇÃO: Esta operação irá consumir itens do almoxarifado!")
            print("📊 Mostrando preview dos itens que serão consumidos...")
            
            # Carrega comandas para preview
            reservas = ler_comandas_em_pasta(pasta_comandas)
            
            if not reservas:
                print("📭 Nenhuma reserva extraída das comandas")
                input("\nPressione Enter para continuar...")
                return
            
            print(f"\n📋 {len(reservas)} reserva(s) de itens serão processadas:")
            print("-" * 50)
            
            # Agrupa por id_item para mostrar total
            from collections import defaultdict
            itens_total = defaultdict(float)
            nomes_itens = {}
            
            for reserva in reservas:
                id_item = reserva['id_item']
                quantidade = reserva['quantidade_necessaria']
                itens_total[id_item] += quantidade
                
                # Busca nome do item no almoxarifado
                item_almox = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.obter_item_por_id(id_item)
                if item_almox:
                    nomes_itens[id_item] = item_almox.descricao
                else:
                    nomes_itens[id_item] = f"Item {id_item} (não encontrado no almoxarifado)"
            
            # Mostra resumo dos itens
            from datetime import date
            hoje = date.today()
            
            for id_item, quantidade_total in sorted(itens_total.items()):
                nome = nomes_itens[id_item]
                item_almox = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.obter_item_por_id(id_item)
                estoque_atual = item_almox.estoque_atual if item_almox else 0
                saldo_final = max(0, estoque_atual - quantidade_total)  # Não permite negativo
                
                status = "✅" if estoque_atual >= quantidade_total else "⚠️"
                print(f"   {status} {nome}")
                print(f"      Consumir: {quantidade_total:.2f}")
                print(f"      Estoque atual: {estoque_atual:.2f}")
                print(f"      Saldo final: {saldo_final:.2f}")
                
                if estoque_atual < quantidade_total:
                    print(f"      ⚠️ Estoque insuficiente! Será ajustado para 0")
                print()
            
            # Confirmação
            confirmacao = input("🔄 Confirma o processamento das comandas? (s/N): ").strip().lower()
            
            if confirmacao in ['s', 'sim', 'y', 'yes']:
                print("\n🔄 Processando comandas...")
                
                # Processa comandas usando o método de reservas do almoxarifado
                resultado = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.processar_comandas_e_reservar_itens(pasta_comandas)
                
                if resultado['sucesso']:
                    print("✅ Comandas processadas com sucesso! (Sistema de Reservas)")
                    print(f"📋 {resultado['total_reservas']} reservas criadas")
                    print(f"📦 {len(resultado['itens_reservados'])} tipos de itens reservados")
                    
                    if resultado['itens_com_estoque_insuficiente']:
                        print(f"⚠️ {len(resultado['itens_com_estoque_insuficiente'])} item(ns) com estoque insuficiente para reserva")
                    
                    print(f"📂 Comandas processadas da pasta: {resultado['pasta_comandas']}")
                    print("\n💡 Use a opção 'F' para despachar as reservas e consumir estoque")
                    
                    # Mostra saldos finais
                    print("\n📊 SALDOS FINAIS:")
                    print("-" * 30)
                    for id_item in sorted(itens_total.keys()):
                        item_almox = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.obter_item_por_id(id_item)
                        if item_almox:
                            nome = item_almox.descricao
                            saldo = item_almox.estoque_atual
                            print(f"   • {nome}: {saldo:.2f}")
                else:
                    print(f"⚠️ Erro ao processar comandas: {resultado.get('erro', 'Erro desconhecido')}")
            else:
                print("\n❌ Processamento cancelado")
                
        except ImportError as e:
            print(f"⚠️ Erro ao importar módulos: {e}")
        except Exception as e:
            print(f"⚠️ Erro ao processar comandas: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def despachar_reservas(self):
        """Despacha comandas disponíveis e consome itens do almoxarifado"""
        try:
            # Inicializa o sistema se necessário
            if not self.gestor_producao.sistema_inicializado:
                print("🔧 Inicializando sistema...")
                if not self.gestor_producao._inicializar_sistema():
                    print("❌ Erro ao inicializar sistema")
                    input("\nPressione Enter para continuar...")
                    return
            
            from datetime import datetime
            import os
            import glob
            import json
            
            continuar_despachando = True
            
            while continuar_despachando:
                self.utils.limpar_tela()
                print("🚚 DESPACHAR COMANDAS - CONSUMIR ALMOXARIFADO")
                print("=" * 50)
                
                # Lista arquivos de comanda disponíveis
                pasta_comandas = "data/comandas"
                arquivos_comanda = sorted(glob.glob(f"{pasta_comandas}/*.json"))
                
                if not arquivos_comanda:
                    print("📭 Nenhuma comanda disponível para despacho")
                    print("\n💡 Execute primeiro um pedido para gerar comandas")
                    input("\nPressione Enter para voltar...")
                    return
                
                # Carrega todas as comandas
                todas_comandas = []
                for arquivo in arquivos_comanda:
                    try:
                        with open(arquivo, 'r', encoding='utf-8') as f:
                            comanda = json.load(f)
                        
                        id_ordem = comanda.get('id_ordem', 0)
                        id_pedido = comanda.get('id_pedido', 0)
                        data_reserva = comanda.get('data_reserva', 'Sem data')
                        num_itens = len(comanda.get('itens', []))
                        
                        # Pega nome do primeiro item principal
                        nome_principal = "Sem nome"
                        if comanda.get('itens'):
                            nome_principal = comanda['itens'][0].get('nome', 'Sem nome')
                        
                        todas_comandas.append({
                            'arquivo': arquivo,
                            'id_ordem': id_ordem,
                            'id_pedido': id_pedido,
                            'data_reserva': data_reserva,
                            'nome_principal': nome_principal,
                            'num_itens': num_itens
                        })
                    except Exception as e:
                        print(f"   ⚠️ Erro ao ler {os.path.basename(arquivo)}: {e}")
                
                # Pergunta se quer filtrar por data
                print(f"📋 Total de {len(todas_comandas)} comanda(s) disponível(is)")
                print("\n🗓️ Deseja filtrar por data?")
                print("   Digite 'T' para ver TODAS as comandas")
                print("   Digite uma data (YYYY-MM-DD) para filtrar")
                print("   Digite 'V' para voltar ao menu principal")
                print("-" * 50)
                
                filtro = input("\n🎯 Sua escolha: ").strip().upper()
                
                if filtro == 'V':
                    continuar_despachando = False
                    continue
                
                # Define comandas a exibir
                comandas_filtradas = todas_comandas
                data_filtro = None
                
                if filtro != 'T' and filtro != '':
                    # Tenta interpretar como data
                    try:
                        # Remove 'T' se digitado junto e converte para lowercase para testar data
                        teste_data = filtro.lower()
                        if len(teste_data) == 10 and teste_data[4] == '-' and teste_data[7] == '-':
                            data_filtro = teste_data
                            comandas_filtradas = [c for c in todas_comandas if c['data_reserva'] == data_filtro]
                            
                            if not comandas_filtradas:
                                print(f"\n📭 Nenhuma comanda encontrada para a data {data_filtro}")
                                input("Pressione Enter para continuar...")
                                continue
                    except:
                        print("\n⚠️ Formato de data inválido! Use YYYY-MM-DD")
                        input("Pressione Enter para continuar...")
                        continue
                
                # Exibe comandas (filtradas ou todas)
                self.utils.limpar_tela()
                print("🚚 DESPACHAR COMANDAS - CONSUMIR ALMOXARIFADO")
                print("=" * 50)
                
                if data_filtro:
                    print(f"📅 Mostrando comandas da data: {data_filtro}")
                else:
                    print(f"📋 Mostrando TODAS as comandas")
                
                print(f"\n{len(comandas_filtradas)} comanda(s):\n")
                
                # Exibe as comandas
                for comanda in comandas_filtradas:
                    print(f"   📦 Ordem {comanda['id_ordem']} | Pedido {comanda['id_pedido']}")
                    print(f"      📅 Data reserva: {comanda['data_reserva']}")
                    print(f"      🍞 Produto: {comanda['nome_principal']}")
                    print(f"      📊 {comanda['num_itens']} item(ns) principal(is)")
                    print()
                
                print("-" * 50)
                print("Digite 'ordem pedido' para despachar específico (ex: '1 1')")
                if data_filtro:
                    print("Digite '*' para despachar TODAS desta data")
                print("Digite 'V' para voltar")
                print("-" * 50)
                
                escolha = input("\n🎯 Sua escolha: ").strip().upper()
                
                if escolha == 'V':
                    continuar_despachando = False
                    continue
                
                # Verifica se é despacho de todas (*) quando há filtro de data
                if escolha == '*' and data_filtro:
                    print(f"\n📦 Despachando TODAS as comandas da data {data_filtro}")
                    print(f"📊 Total: {len(comandas_filtradas)} comanda(s)")
                    
                    confirmacao = input("\n🚚 Confirma o despacho de TODAS? (s/N): ").strip().lower()
                    
                    if confirmacao in ['s', 'sim', 'y', 'yes']:
                        print("\n🔄 Processando despachos em lote...")
                        
                        sucessos = 0
                        erros = 0
                        
                        for comanda in comandas_filtradas:
                            try:
                                print(f"\n📦 Despachando Ordem {comanda['id_ordem']} | Pedido {comanda['id_pedido']}...")
                                
                                # Extrai a data da comanda
                                data_str = comanda['data_reserva']
                                try:
                                    data_despacho = datetime.strptime(data_str, '%Y-%m-%d')
                                except:
                                    data_despacho = datetime.now()
                                
                                # Despacha
                                resultado = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.despachar_reservas_e_consumir_itens(
                                    data_despacho=data_despacho,
                                    id_ordem=comanda['id_ordem'],
                                    id_pedido=comanda['id_pedido']
                                )
                                
                                if resultado['sucesso']:
                                    sucessos += 1
                                    print(f"   ✅ Sucesso - {resultado['reservas_despachadas']} reservas")
                                    
                                    # Remove arquivo
                                    try:
                                        os.remove(comanda['arquivo'])
                                        print(f"   🗑️ Comanda removida")
                                    except:
                                        pass
                                else:
                                    erros += 1
                                    print(f"   ❌ Erro no despacho")
                                    
                            except Exception as e:
                                erros += 1
                                print(f"   ❌ Erro: {e}")
                        
                        print("\n" + "=" * 50)
                        print(f"📊 RESUMO DO DESPACHO EM LOTE:")
                        print(f"   ✅ Sucessos: {sucessos}")
                        print(f"   ❌ Erros: {erros}")
                        print(f"   📦 Total processado: {sucessos + erros}")
                        
                        input("\n📋 Pressione Enter para continuar...")
                    else:
                        print("\n❌ Despacho em lote cancelado")
                        input("Pressione Enter para continuar...")
                    continue
                
                # Processa escolha de ordem/pedido individual
                try:
                    partes = escolha.split()
                    if len(partes) != 2:
                        print("\n❌ Formato inválido! Use: ordem pedido (ex: '1 1')")
                        input("Pressione Enter para continuar...")
                        continue
                    
                    id_ordem = int(partes[0])
                    id_pedido = int(partes[1])
                    
                    # Busca a comanda correspondente nas comandas filtradas
                    comanda_selecionada = None
                    for info in comandas_filtradas:
                        if info['id_ordem'] == id_ordem and info['id_pedido'] == id_pedido:
                            comanda_selecionada = info
                            break
                    
                    if not comanda_selecionada:
                        print(f"\n❌ Comanda da Ordem {id_ordem} | Pedido {id_pedido} não encontrada!")
                        if data_filtro:
                            print(f"   (Verifique se está na data {data_filtro})")
                        input("Pressione Enter para continuar...")
                        continue
                    
                    # Confirmação
                    print(f"\n📦 Comanda selecionada: Ordem {id_ordem} | Pedido {id_pedido}")
                    print(f"📅 Data reserva: {comanda_selecionada['data_reserva']}")
                    print(f"🍞 Produto: {comanda_selecionada['nome_principal']}")
                    
                    confirmacao = input("\n🚚 Confirma o despacho? (s/N): ").strip().lower()
                    
                    if confirmacao in ['s', 'sim', 'y', 'yes']:
                        print("\n🔄 Processando despacho...")
                        
                        # Extrai a data da comanda para despachar
                        data_str = comanda_selecionada['data_reserva']
                        try:
                            data_despacho = datetime.strptime(data_str, '%Y-%m-%d')
                        except:
                            data_despacho = datetime.now()
                        
                        # Despacha usando o método do almoxarifado
                        resultado = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.despachar_reservas_e_consumir_itens(
                            data_despacho=data_despacho,
                            id_ordem=id_ordem,
                            id_pedido=id_pedido
                        )
                        
                        if resultado['sucesso']:
                            print("✅ Comanda despachada com sucesso!")
                            print(f"🚚 {resultado['reservas_despachadas']} reservas processadas")
                            print(f"📦 {len(resultado['itens_despachados'])} tipos de itens consumidos")
                            
                            # Remove o arquivo de comanda
                            try:
                                os.remove(comanda_selecionada['arquivo'])
                                print(f"🗑️ Comanda removida: {os.path.basename(comanda_selecionada['arquivo'])}")
                            except Exception as e:
                                print(f"⚠️ Erro ao remover arquivo de comanda: {e}")
                            
                            # Mostra resumo do que foi consumido
                            if resultado['itens_despachados']:
                                print("\n📊 ITENS CONSUMIDOS:")
                                print("-" * 30)
                                for item in resultado['itens_despachados'][:5]:  # Mostra só os 5 primeiros
                                    print(f"   • {item['nome']}: {item['quantidade_despachada']:.2f} {item['unidade']}")
                                if len(resultado['itens_despachados']) > 5:
                                    print(f"   ... e mais {len(resultado['itens_despachados']) - 5} itens")
                        else:
                            print(f"⚠️ Erro ao despachar: {resultado.get('erro', 'Erro desconhecido')}")
                        
                        input("\n📋 Pressione Enter para continuar...")
                    else:
                        print("\n❌ Despacho cancelado")
                        input("Pressione Enter para continuar...")
                        
                except ValueError:
                    print("\n❌ IDs devem ser números!")
                    input("Pressione Enter para continuar...")
                except Exception as e:
                    print(f"\n⚠️ Erro ao processar despacho: {e}")
                    input("Pressione Enter para continuar...")
                    
        except Exception as e:
            print(f"⚠️ Erro no sistema de despacho: {e}")
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

    def visualizar_equipamentos(self):
        """🆕 Visualiza todos os equipamentos carregados em memória"""
        self.utils.limpar_tela()
        print("🔧 VISUALIZAR EQUIPAMENTOS EM MEMÓRIA")
        print("=" * 60)

        try:
            # Inicializa o sistema se necessário
            if not self.gestor_producao.sistema_inicializado:
                print("⏳ Inicializando sistema...")
                if not self.gestor_producao._inicializar_sistema():
                    print("❌ Erro ao inicializar sistema")
                    input("\nPressione Enter para continuar...")
                    return

            # Usa o visualizador de equipamentos
            from menu.visualizador_equipamentos import VisualizadorEquipamentos

            visualizador = VisualizadorEquipamentos()
            visualizador.visualizar()

        except Exception as e:
            print(f"\n❌ Erro ao visualizar equipamentos: {e}")
            import traceback
            traceback.print_exc()

        input("\nPressione Enter para continuar...")

    def sair(self):
        """Encerra o sistema"""
        print("\nEncerrando Sistema de Producao...")
        print("Sistema salvo automaticamente.")
        print("Ate a proxima!")
        self.rodando = False

    # =========================================================================
    #                       🆕 SUBMENU GESTÃO DE FUNCIONÁRIOS
    # =========================================================================

    def mostrar_submenu_funcionarios(self):
        """Submenu para gestão de funcionários"""
        try:
            rodando_funcionarios = True

            while rodando_funcionarios:
                try:
                    self.utils.limpar_tela()
                    print("👥 SISTEMA DE PRODUÇÃO - GESTÃO DE FUNCIONÁRIOS")
                    print("=" * 60)
                    print()

                    # Status do sistema de funcionários
                    print("📊 STATUS DO SISTEMA:")
                    print("✅ GestorFuncionarios: ATIVO")
                    print("✅ AnalisadorConflitos: ATIVO")
                    print("✅ Logs de funcionários: DISPONÍVEL")
                    print()

                    # Mostrar pedidos alocados
                    pedidos_alocados = self.gestor_funcionarios.listar_pedidos_alocados()
                    if pedidos_alocados:
                        print(f"📋 Pedidos com funcionários alocados: {len(pedidos_alocados)}")
                    print()

                    # Menu de opções
                    print("OPÇÕES DISPONÍVEIS:")
                    print()
                    print("🚀 EXECUÇÃO E ALOCAÇÃO:")
                    print("1️⃣  Alocar Funcionários para Pedidos")
                    print()
                    print("🔍 ANÁLISE E MONITORAMENTO:")
                    print("2️⃣  Analisar Conflitos de Funcionários")
                    print("3️⃣  Mostrar Agenda de Funcionários (dos Logs)")
                    print("4️⃣  Mostrar Agenda de Funcionários (da Memória)")
                    print()
                    print("🧹 GERENCIAMENTO:")
                    print("5️⃣  Listar Pedidos Alocados")
                    print("6️⃣  Limpar Alocação de Pedido Específico")
                    print("7️⃣  Limpar Todas as Alocações")
                    print()
                    print("🔧 NAVEGAÇÃO:")
                    print("V️⃣  Voltar ao Menu Principal")
                    print()
                    print("─" * 60)

                    opcao = input("🎯 Escolha uma opção: ").strip()

                    if opcao == "1":
                        self.executar_alocacao_funcionarios()

                    elif opcao == "2":
                        self.executar_analise_conflitos()

                    elif opcao == "3":
                        self.executar_agenda_funcionarios()

                    elif opcao == "4":
                        self.executar_agenda_funcionarios_memoria()

                    elif opcao == "5":
                        self.listar_pedidos_alocados_funcionarios()

                    elif opcao == "6":
                        self.limpar_alocacao_pedido_especifico()

                    elif opcao == "7":
                        self.limpar_todas_alocacoes_funcionarios()

                    elif opcao.lower() == "v":
                        rodando_funcionarios = False

                    else:
                        print(f"\n⚡ Opção '{opcao}' inválida!")
                        input("Pressione Enter para continuar...")

                except KeyboardInterrupt:
                    print("\n🔄 Voltando ao menu de funcionários...")
                    input("Pressione Enter para continuar...")

        except Exception as e:
            print(f"\n❌ Erro no submenu de funcionários: {e}")
            input("Pressione Enter para voltar ao menu principal...")

    def executar_alocacao_funcionarios(self):
        """Executa alocação de funcionários usando o gestor integrado (singleton)"""
        import os
        import re

        try:
            print("\n🚀 ALOCAÇÃO DE FUNCIONÁRIOS")
            print("=" * 50)
            print()

            # Listar arquivos disponíveis
            diretorio = "logs/tipos_funcionarios_requeridos"

            if not os.path.exists(diretorio):
                print(f"❌ Diretório não encontrado: {diretorio}")
                input("Pressione Enter para continuar...")
                return

            arquivos = [f for f in os.listdir(diretorio) if f.endswith('.log')]

            if not arquivos:
                print(f"❌ Nenhum arquivo de requisitos encontrado em {diretorio}")
                print("💡 Execute primeiro um pedido para gerar os requisitos de funcionários")
                input("Pressione Enter para continuar...")
                return

            # Extrair ordem|pedido dos arquivos
            requisitos = []
            requisitos_ignorados = []
            padrao = r'ordem: (\d+) \| pedido: (\d+)\.log'

            # Diretório de sucesso de equipamentos
            dir_sucesso_equip = "logs/equipamentos/sucesso"

            for arquivo in arquivos:
                match = re.match(padrao, arquivo)
                if match:
                    id_ordem = int(match.group(1))
                    id_pedido = int(match.group(2))

                    # Verificar se o pedido teve sucesso na alocação de equipamentos
                    arquivo_sucesso = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
                    caminho_sucesso = os.path.join(dir_sucesso_equip, arquivo_sucesso)

                    if os.path.exists(caminho_sucesso):
                        requisitos.append((id_ordem, id_pedido, arquivo))
                    else:
                        requisitos_ignorados.append((id_ordem, id_pedido))

            if not requisitos:
                print("❌ Nenhum requisito válido encontrado")
                if requisitos_ignorados:
                    print(f"⚠️ {len(requisitos_ignorados)} pedido(s) ignorado(s) por falha na alocação de equipamentos:")
                    for id_ordem, id_pedido in requisitos_ignorados:
                        print(f"   - Ordem {id_ordem} | Pedido {id_pedido}")
                input("Pressione Enter para continuar...")
                return

            # Mostrar pedidos ignorados se houver
            if requisitos_ignorados:
                print(f"⚠️ {len(requisitos_ignorados)} pedido(s) ignorado(s) (falha em equipamentos):")
                for id_ordem, id_pedido in requisitos_ignorados:
                    print(f"   - Ordem {id_ordem} | Pedido {id_pedido}")
                print()

            print(f"📋 {len(requisitos)} ordem|pedido disponível(is) para alocação:")
            print()
            for i, (id_ordem, id_pedido, arquivo) in enumerate(requisitos, 1):
                # Verificar se já foi alocado
                ja_alocado = self.gestor_funcionarios.pedido_ja_alocado(id_ordem, id_pedido)
                status = "✅ JÁ ALOCADO" if ja_alocado else "⏳ Pendente"
                print(f"{i}. Ordem {id_ordem} | Pedido {id_pedido} - {status}")
            print()
            print("0. Alocar TODOS (apenas pendentes)")
            print()

            # Mostrar resumo
            total_alocados = sum(1 for o, p, _ in requisitos if self.gestor_funcionarios.pedido_ja_alocado(o, p))
            total_pendentes = len(requisitos) - total_alocados
            print(f"📊 Resumo: {total_pendentes} pendente(s) | {total_alocados} já alocado(s)")
            print()

            escolha = input("🎯 Escolha uma opção (0 para todos, Enter para voltar): ").strip()

            if not escolha:
                return

            if escolha == "0":
                # Alocar todos (apenas pendentes)
                sucessos = 0
                falhas = 0
                pulados = 0

                print()
                print("🚀 Alocando todos os pedidos pendentes...")
                print("=" * 50)

                for id_ordem, id_pedido, _ in requisitos:
                    # Pular se já foi alocado
                    if self.gestor_funcionarios.pedido_ja_alocado(id_ordem, id_pedido):
                        pulados += 1
                        print(f"⏭️ Ordem {id_ordem} | Pedido {id_pedido}: Pulado (já alocado)")
                        continue

                    print(f"\n📦 Processando Ordem {id_ordem} | Pedido {id_pedido}...")
                    sucesso = self.gestor_funcionarios.alocar_funcionarios_para_ordem_pedido(id_ordem, id_pedido)

                    if sucesso:
                        sucessos += 1
                        print(f"✅ Ordem {id_ordem} | Pedido {id_pedido}: Alocação bem-sucedida")
                    else:
                        falhas += 1
                        print(f"⚠️ Ordem {id_ordem} | Pedido {id_pedido}: Alocação com falhas (verifique logs)")

                print()
                print("=" * 50)
                print(f"📊 RESULTADO: {sucessos} sucesso(s) | {falhas} falha(s) | {pulados} pulado(s)")

                if pulados > 0:
                    print(f"💡 Use a opção de gestão para limpar alocações se quiser realocar")

            else:
                # Alocar específico
                try:
                    indice = int(escolha) - 1
                    if 0 <= indice < len(requisitos):
                        id_ordem, id_pedido, _ = requisitos[indice]

                        # Verificar se já está alocado
                        if self.gestor_funcionarios.pedido_ja_alocado(id_ordem, id_pedido):
                            print()
                            print(f"🚫 Ordem {id_ordem} | Pedido {id_pedido} já teve funcionários alocados!")
                            print()
                            resposta = input("Deseja limpar e realocar? (s/N): ").strip().lower()

                            if resposta == 's':
                                self.gestor_funcionarios.limpar_alocacao_pedido(id_ordem, id_pedido)
                                print("🧹 Alocação anterior limpa")
                            else:
                                print("❌ Operação cancelada")
                                input("Pressione Enter para continuar...")
                                return

                        print()
                        print(f"🚀 Alocando Ordem {id_ordem} | Pedido {id_pedido}...")
                        print("=" * 50)

                        sucesso = self.gestor_funcionarios.alocar_funcionarios_para_ordem_pedido(id_ordem, id_pedido)

                        print()
                        if sucesso:
                            print("✅ Alocação concluída com sucesso!")
                            print(f"📄 Log salvo em: logs/funcionarios/ordem: {id_ordem} | pedido: {id_pedido}.log")
                        else:
                            print("⚠️ Alocação concluída com algumas falhas")
                            print("🔍 Verifique os logs para mais detalhes")
                    else:
                        print("❌ Opção inválida")
                except ValueError:
                    print("❌ Entrada inválida")

        except Exception as e:
            print(f"❌ Erro ao executar alocação: {e}")
            import traceback
            traceback.print_exc()

        print()
        input("Pressione Enter para continuar...")

    def executar_analise_conflitos(self):
        """Executa o script de análise de conflitos"""
        import subprocess
        import os

        try:
            print("\n🔍 EXECUTANDO ANÁLISE DE CONFLITOS DE FUNCIONÁRIOS")
            print("=" * 50)
            print("📋 Carregando análise genérica de conflitos...")
            print()

            # Executar o script de análise
            resultado = subprocess.run([
                "python3", "analise_conflitos_generica.py"
            ], capture_output=False, text=True, cwd=os.getcwd())

            print()
            if resultado.returncode == 0:
                print("✅ Análise de conflitos executada com sucesso!")
            else:
                print("❌ Erro durante a análise de conflitos")

        except Exception as e:
            print(f"❌ Erro ao executar análise: {e}")

        print()
        input("Pressione Enter para continuar...")

    def executar_agenda_funcionarios(self):
        """Executa o script de agenda de funcionários (carrega dos logs)"""
        import subprocess
        import os

        try:
            print("\n📅 EXECUTANDO VISUALIZAÇÃO DA AGENDA DE FUNCIONÁRIOS (DOS LOGS)")
            print("=" * 50)
            print("📋 Carregando agenda de funcionários dos arquivos .log...")
            print()

            # Executar o script de agenda
            resultado = subprocess.run([
                "python3", "mostrar_agenda_funcionarios.py"
            ], capture_output=False, text=True, cwd=os.getcwd())

            print()
            if resultado.returncode == 0:
                print("✅ Agenda de funcionários exibida com sucesso!")
            else:
                print("❌ Erro durante a exibição da agenda")

        except Exception as e:
            print(f"❌ Erro ao executar agenda: {e}")

        print()
        input("Pressione Enter para continuar...")

    def executar_agenda_funcionarios_memoria(self):
        """Executa o script de agenda de funcionários (usa dados em memória)"""
        try:
            print("\n📅 EXECUTANDO VISUALIZAÇÃO DA AGENDA DE FUNCIONÁRIOS (DA MEMÓRIA)")
            print("=" * 50)
            print("📋 Exibindo ocupações atuais em memória (sem recarregar logs)...")
            print()

            # Verificar quantas ocupações existem em memória
            total_ocupacoes_memoria = sum(len(f.ocupacoes) for f in self.gestor_funcionarios.funcionarios_disponiveis)

            print(f"📊 Total de ocupações em memória: {total_ocupacoes_memoria}")
            print()

            if total_ocupacoes_memoria == 0:
                print("⚠️ Nenhuma ocupação encontrada em memória.")
                print("💡 Dica: Execute a opção 1 (Alocar Funcionários) primeiro ou use a opção 3 para carregar dos logs.")
                print()

            # Obter e exibir a agenda (baseada no atributo ocupacoes em memória)
            agenda = self.gestor_funcionarios.mostrar_agenda_todos_funcionarios()
            print(agenda)

            print("\n✅ Agenda de funcionários exibida com sucesso!")

        except Exception as e:
            print(f"❌ Erro ao executar agenda: {e}")
            import traceback
            traceback.print_exc()

        print()
        input("Pressione Enter para continuar...")

    def listar_pedidos_alocados_funcionarios(self):
        """Lista todos os pedidos que já tiveram funcionários alocados"""
        try:
            print("\n📋 PEDIDOS COM FUNCIONÁRIOS ALOCADOS")
            print("=" * 50)

            pedidos = self.gestor_funcionarios.listar_pedidos_alocados()

            if not pedidos:
                print("📭 Nenhum pedido com funcionários alocados")
            else:
                print(f"Total: {len(pedidos)} pedido(s)")
                print()
                for i, (id_ordem, id_pedido) in enumerate(pedidos, 1):
                    print(f"{i}. Ordem {id_ordem} | Pedido {id_pedido}")

        except Exception as e:
            print(f"❌ Erro: {e}")

        print()
        input("Pressione Enter para continuar...")

    def limpar_alocacao_pedido_especifico(self):
        """Limpa a alocação de um pedido específico"""
        try:
            print("\n🧹 LIMPAR ALOCAÇÃO DE PEDIDO ESPECÍFICO")
            print("=" * 50)

            pedidos = self.gestor_funcionarios.listar_pedidos_alocados()

            if not pedidos:
                print("📭 Nenhum pedido com funcionários alocados")
                input("Pressione Enter para continuar...")
                return

            print(f"Pedidos disponíveis: {len(pedidos)}")
            print()
            for i, (id_ordem, id_pedido) in enumerate(pedidos, 1):
                print(f"{i}. Ordem {id_ordem} | Pedido {id_pedido}")
            print()

            escolha = input("🎯 Escolha o pedido para limpar (Enter para cancelar): ").strip()

            if not escolha:
                print("❌ Operação cancelada")
                input("Pressione Enter para continuar...")
                return

            try:
                indice = int(escolha) - 1
                if 0 <= indice < len(pedidos):
                    id_ordem, id_pedido = pedidos[indice]

                    print()
                    print(f"⚠️ Isso irá limpar a alocação de funcionários para Ordem {id_ordem} | Pedido {id_pedido}")
                    confirma = input("Confirma? (s/N): ").strip().lower()

                    if confirma == 's':
                        self.gestor_funcionarios.limpar_alocacao_pedido(id_ordem, id_pedido)
                        print(f"✅ Alocação de Ordem {id_ordem} | Pedido {id_pedido} limpa com sucesso!")
                    else:
                        print("❌ Operação cancelada")
                else:
                    print("❌ Opção inválida")
            except ValueError:
                print("❌ Entrada inválida")

        except Exception as e:
            print(f"❌ Erro: {e}")

        print()
        input("Pressione Enter para continuar...")

    def limpar_todas_alocacoes_funcionarios(self):
        """Limpa todas as alocações de funcionários"""
        try:
            print("\n🧹 LIMPAR TODAS AS ALOCAÇÕES")
            print("=" * 50)

            pedidos = self.gestor_funcionarios.listar_pedidos_alocados()

            if not pedidos:
                print("📭 Nenhum pedido com funcionários alocados")
                input("Pressione Enter para continuar...")
                return

            print(f"⚠️ Isso irá limpar a alocação de {len(pedidos)} pedido(s):")
            print()
            for id_ordem, id_pedido in pedidos:
                print(f"  • Ordem {id_ordem} | Pedido {id_pedido}")
            print()

            confirma = input("Confirma a limpeza de TODAS as alocações? (s/N): ").strip().lower()

            if confirma == 's':
                self.gestor_funcionarios.limpar_todas_alocacoes()
                print(f"✅ Todas as alocações foram limpas com sucesso!")
                print("💡 Agora você pode realocar os funcionários")
            else:
                print("❌ Operação cancelada")

        except Exception as e:
            print(f"❌ Erro: {e}")

        print()
        input("Pressione Enter para continuar...")

    # =========================================================================
    #                   📊 GERAÇÃO DE ESCALAS
    # =========================================================================

    def gerar_escala_funcionarios(self):
        """Gera planilha Excel com escala de funcionários"""
        try:
            self.utils.limpar_tela()
            print("📊 GERAÇÃO DE ESCALA DE FUNCIONÁRIOS")
            print("=" * 60)
            print()

            # Verificar se há logs de funcionários
            dir_sucesso = "logs/funcionarios/sucesso"
            if not os.path.exists(dir_sucesso) or not os.listdir(dir_sucesso):
                print("❌ Nenhum log de alocação de funcionários encontrado!")
                print("   Execute primeiro a alocação de funcionários.")
                input("\nPressione Enter para voltar...")
                return

            # Contar arquivos
            arquivos = [f for f in os.listdir(dir_sucesso) if f.endswith('.log')]
            print(f"📁 Logs encontrados: {len(arquivos)} pedido(s) com funcionários alocados")
            print()

            # Confirmar geração
            confirma = input("Deseja gerar a planilha de escala? (S/N): ").strip().upper()
            if confirma != 'S':
                print("❌ Operação cancelada.")
                input("\nPressione Enter para voltar...")
                return

            print()
            print("⏳ Gerando planilha Excel...")
            print()

            # Importar e gerar
            from services.exportacao.escalas import gerar_escala_funcionarios as gerar_escala

            # Limpar diretório de saída
            dir_saida = "data/escalas"
            if os.path.exists(dir_saida):
                for arquivo in os.listdir(dir_saida):
                    caminho = os.path.join(dir_saida, arquivo)
                    if os.path.isfile(caminho):
                        os.remove(caminho)
                print(f"🧹 Diretório {dir_saida} limpo")

            # Gerar escala
            caminho = gerar_escala()

            if caminho:
                print()
                print("=" * 60)
                print(f"✅ ESCALA GERADA COM SUCESSO!")
                print(f"📄 Arquivo: {caminho}")
                print("=" * 60)

                # Gerar gráfico de Gantt automaticamente
                print()
                print("⏳ Gerando gráfico de Gantt...")
                try:
                    from utils.graficos import gerar_gantt_funcionarios
                    caminho_gantt = gerar_gantt_funcionarios()
                    if caminho_gantt:
                        print(f"📊 Gantt: {caminho_gantt}")
                except ImportError:
                    print("⚠️  Matplotlib não instalado. Gantt não gerado.")
                except Exception as e_gantt:
                    print(f"⚠️  Erro ao gerar Gantt: {e_gantt}")
            else:
                print()
                print("❌ Falha ao gerar escala. Verifique os logs.")

        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
            print("   Verifique se o módulo openpyxl está instalado: pip install openpyxl")
        except Exception as e:
            print(f"❌ Erro ao gerar escala: {e}")

        input("\nPressione Enter para voltar...")

    # =========================================================================
    #                   ✅ SUBMENU VALIDAÇÃO E EXPORTAÇÃO
    # =========================================================================

    def mostrar_submenu_validacao_exportacao(self):
        """Submenu para validação e exportação de pedidos"""
        try:
            rodando_validacao = True

            while rodando_validacao:
                try:
                    self.utils.limpar_tela()
                    print("✅ SISTEMA DE PRODUÇÃO - VALIDAÇÃO E EXPORTAÇÃO")
                    print("=" * 60)
                    print()

                    # Status do sistema
                    print("📊 STATUS DO SISTEMA:")
                    aprovados = self.validador_pedidos.listar_pedidos_aprovados()
                    cancelados = self.validador_pedidos.listar_pedidos_cancelados()
                    pendentes = self.exportador_banco.listar_pedidos_pendentes_exportacao()

                    print(f"   ✅ Pedidos aprovados: {len(aprovados)}")
                    print(f"   ❌ Pedidos cancelados: {len(cancelados)}")
                    print(f"   ⏳ Pendentes de exportação: {len(pendentes)}")
                    print()

                    # Menu de opções
                    print("OPÇÕES DISPONÍVEIS:")
                    print()
                    print("🔍 VALIDAÇÃO:")
                    print("1️⃣  Validar Pedido Específico")
                    print("2️⃣  Validar Todos os Pedidos Disponíveis")
                    print()
                    print("📋 RELATÓRIOS:")
                    print("3️⃣  Relatório de Validação")
                    print("4️⃣  Dashboard de Exportação")
                    print()
                    print("💾 EXPORTAÇÃO:")
                    print("5️⃣  Exportar Pedidos Aprovados para Banco")
                    print("6️⃣  Histórico de Exportações")
                    print()
                    print("🔧 NAVEGAÇÃO:")
                    print("V️⃣  Voltar ao Menu Principal")
                    print()
                    print("─" * 60)

                    opcao = input("🎯 Escolha uma opção: ").strip()

                    if opcao == "1":
                        self.validar_pedido_especifico()

                    elif opcao == "2":
                        self.validar_todos_pedidos()

                    elif opcao == "3":
                        self.mostrar_relatorio_validacao()

                    elif opcao == "4":
                        self.mostrar_dashboard_exportacao()

                    elif opcao == "5":
                        self.exportar_pedidos_aprovados()

                    elif opcao == "6":
                        self.mostrar_historico_exportacoes()

                    elif opcao.lower() == "v":
                        rodando_validacao = False

                    else:
                        print(f"\n⚡ Opção '{opcao}' inválida!")
                        input("Pressione Enter para continuar...")

                except KeyboardInterrupt:
                    print("\n🔄 Voltando ao menu de validação...")
                    input("Pressione Enter para continuar...")

        except Exception as e:
            print(f"\n❌ Erro no submenu de validação: {e}")
            input("Pressione Enter para voltar ao menu principal...")

    def validar_pedido_especifico(self):
        """Valida um pedido específico"""
        try:
            print("\n🔍 VALIDAR PEDIDO ESPECÍFICO")
            print("=" * 50)
            print()

            id_ordem = input("ID da Ordem: ").strip()
            id_pedido = input("ID do Pedido: ").strip()

            if not id_ordem or not id_pedido:
                print("❌ IDs não fornecidos")
                input("Pressione Enter para continuar...")
                return

            id_ordem = int(id_ordem)
            id_pedido = int(id_pedido)

            print()
            print(f"🔍 Validando Ordem {id_ordem} | Pedido {id_pedido}...")
            print()

            resultado = self.validador_pedidos.validar_pedido(id_ordem, id_pedido, cancelar_se_invalido=True)

            print(f"📊 RESULTADO DA VALIDAÇÃO:")
            print(f"   Status: {resultado['status'].upper()}")
            print(f"   Válido: {'✅ SIM' if resultado['valido'] else '❌ NÃO'}")
            print()
            print(f"   Equipamentos: {'✅' if resultado['equipamentos_ok'] else '❌'} {resultado['detalhes']['equipamentos']['atividades_sucesso']}/{resultado['detalhes']['equipamentos']['total_atividades']}")
            print(f"   Funcionários: {'✅' if resultado['funcionarios_ok'] else '❌'} {resultado['detalhes']['funcionarios']['atividades_sucesso']}/{resultado['detalhes']['funcionarios']['total_atividades']}")

            if not resultado['valido']:
                print()
                print(f"❌ Motivo do cancelamento:")
                print(f"   {resultado.get('motivo_cancelamento', 'N/A')}")

        except ValueError:
            print("❌ IDs inválidos. Use números inteiros.")
        except Exception as e:
            print(f"❌ Erro ao validar pedido: {e}")

        print()
        input("Pressione Enter para continuar...")

    def validar_todos_pedidos(self):
        """Valida todos os pedidos disponíveis nos logs"""
        try:
            print("\n🔍 VALIDAR TODOS OS PEDIDOS")
            print("=" * 50)
            print()

            # Listar pedidos disponíveis dos logs
            import os
            import re

            pedidos_disponiveis = set()

            # Verificar logs de equipamentos
            if os.path.exists("logs/equipamentos"):
                for arquivo in os.listdir("logs/equipamentos"):
                    match = re.match(r'ordem: (\d+) \| pedido: (\d+)\.log', arquivo)
                    if match:
                        pedidos_disponiveis.add((int(match.group(1)), int(match.group(2))))

            # Verificar logs de funcionários
            if os.path.exists("logs/funcionarios"):
                for arquivo in os.listdir("logs/funcionarios"):
                    match = re.match(r'ordem: (\d+) \| pedido: (\d+)\.log', arquivo)
                    if match:
                        pedidos_disponiveis.add((int(match.group(1)), int(match.group(2))))

            if not pedidos_disponiveis:
                print("📭 Nenhum pedido encontrado nos logs")
                input("Pressione Enter para continuar...")
                return

            pedidos_ordenados = sorted(list(pedidos_disponiveis))
            print(f"📋 Encontrados {len(pedidos_ordenados)} pedido(s) para validar:")
            for ordem, pedido in pedidos_ordenados:
                print(f"   • Ordem {ordem} | Pedido {pedido}")
            print()

            confirmacao = input("Deseja validar todos? (S/N): ").strip().upper()
            if confirmacao != 'S':
                print("❌ Operação cancelada")
                input("Pressione Enter para continuar...")
                return

            print()
            print("🔄 Validando pedidos...")
            print("-" * 50)

            aprovados = 0
            cancelados = 0

            for ordem, pedido in pedidos_ordenados:
                resultado = self.validador_pedidos.validar_pedido(ordem, pedido, cancelar_se_invalido=True)
                if resultado['valido']:
                    print(f"✅ Ordem {ordem} | Pedido {pedido} - APROVADO")
                    aprovados += 1
                else:
                    print(f"❌ Ordem {ordem} | Pedido {pedido} - CANCELADO")
                    cancelados += 1

            print()
            print("📊 RESUMO:")
            print(f"   ✅ Aprovados: {aprovados}")
            print(f"   ❌ Cancelados: {cancelados}")

        except Exception as e:
            print(f"❌ Erro ao validar pedidos: {e}")

        print()
        input("Pressione Enter para continuar...")

    def mostrar_relatorio_validacao(self):
        """Exibe relatório de validação"""
        try:
            print("\n📊 RELATÓRIO DE VALIDAÇÃO")
            print("=" * 50)
            print()

            relatorio = self.validador_pedidos.gerar_relatorio_validacao()
            print(relatorio)

        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")

        print()
        input("Pressione Enter para continuar...")

    def mostrar_dashboard_exportacao(self):
        """Exibe dashboard de exportação"""
        try:
            print("\n📊 DASHBOARD DE EXPORTAÇÃO")
            print("=" * 50)
            print()

            dashboard = self.exportador_banco.gerar_dashboard()
            print(dashboard)

        except Exception as e:
            print(f"❌ Erro ao gerar dashboard: {e}")

        print()
        input("Pressione Enter para continuar...")

    def exportar_pedidos_aprovados(self):
        """Exporta pedidos aprovados para o banco"""
        try:
            print("\n💾 EXPORTAR PEDIDOS PARA BANCO")
            print("=" * 50)
            print()

            pendentes = self.exportador_banco.listar_pedidos_pendentes_exportacao()

            if not pendentes:
                print("✅ Nenhum pedido pendente de exportação")
                print("💡 Todos os pedidos aprovados já foram exportados")
                input("Pressione Enter para continuar...")
                return

            print(f"📋 {len(pendentes)} pedido(s) pendente(s) de exportação:")
            for pedido in pendentes:
                print(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']}")
            print()

            confirmacao = input("Deseja exportar todos? (S/N): ").strip().upper()
            if confirmacao != 'S':
                print("❌ Operação cancelada")
                input("Pressione Enter para continuar...")
                return

            print()
            print("🔄 Exportando pedidos...")
            resultado = self.exportador_banco.exportar_lote(pendentes, executar_sql=False)

            if resultado['sucesso']:
                print(f"✅ Exportação concluída com sucesso!")
                print()
                print(f"📦 Lote ID: {resultado['lote_id']}")
                print(f"📄 Script SQL: {resultado['arquivo_sql']}")
                print(f"📊 Relatório: {resultado['arquivo_relatorio']}")
                print()
                print("⚠️ NOTA: SQL não foi executado (executar_sql=False)")
                print("   Os scripts foram gerados e estão prontos para uso futuro")
            else:
                print(f"❌ Erro na exportação: {resultado.get('erro', 'Desconhecido')}")

        except Exception as e:
            print(f"❌ Erro ao exportar pedidos: {e}")

        print()
        input("Pressione Enter para continuar...")

    def mostrar_historico_exportacoes(self):
        """Exibe histórico de exportações"""
        try:
            print("\n📜 HISTÓRICO DE EXPORTAÇÕES")
            print("=" * 50)
            print()

            historico = self.exportador_banco.listar_historico_exportacoes()

            if not historico:
                print("📭 Nenhuma exportação realizada ainda")
            else:
                print(f"Total de exportações: {len(historico)}")
                print()
                for lote in historico:
                    print(f"📦 Lote {lote['lote_id']}")
                    print(f"   Data: {lote['data_preparacao']}")
                    print(f"   Pedidos: {lote['total_pedidos']}")
                    print(f"   Status: {lote['status']}")
                    print()

        except Exception as e:
            print(f"❌ Erro ao listar histórico: {e}")

        print()
        input("Pressione Enter para continuar...")


    def mostrar_submenu_avaliador_pedidos(self):
        """Submenu para avaliação de pedidos"""
        try:
            rodando_avaliador = True
            
            while rodando_avaliador:
                try:
                    self.utils.limpar_tela()
                    print("🔍 AVALIADOR DE PEDIDOS")
                    print("=" * 50)
                    print("\n📄 ANÁLISE DE ATIVIDADES E REAGENDAMENTO")
                    print()
                    print("📄 OPÇÕES DISPONÍVEIS:")
                    print("1️⃣  Analisar Atividades Compartilhadas")
                    print("2️⃣  Estimar Fim de Jornada")
                    print("\nV️⃣  Voltar ao Menu Principal")
                    print("=" * 50)
                    
                    opcao_avaliador = input("\n🎯 Escolha uma opção: ").strip().upper()
                    
                    if opcao_avaliador == '1':
                        self.analisar_atividades_compartilhadas()
                    elif opcao_avaliador == '2':
                        self.estimar_fim_jornada()
                    elif opcao_avaliador == 'V':
                        rodando_avaliador = False
                    else:
                        print(f"\n⚠️ Opção '{opcao_avaliador}' inválida!")
                        input("Pressione Enter para continuar...")
                        
                except KeyboardInterrupt:
                    print("\n\n🔍 Voltando ao menu principal...")
                    rodando_avaliador = False
                except Exception as e:
                    print(f"\n⚠️ Erro no submenu avaliador: {e}")
                    input("Pressione Enter para continuar...")
            
        except Exception as e:
            print(f"\n⚠️ Erro inesperado no submenu avaliador: {e}")
            input("Pressione Enter para continuar...")
    
    def analisar_atividades_compartilhadas(self):
        """Analisa atividades compartilhadas entre pedidos"""
        self.utils.limpar_tela()
        print("🔍 ANÁLISE DE ATIVIDADES COMPARTILHADAS")
        print("=" * 50)
        
        try:
            # Define o diretório de logs
            diretorio_logs = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/equipamentos"
            
            if not os.path.exists(diretorio_logs):
                print(f"⚠️ Diretório de logs não encontrado: {diretorio_logs}")
                print("💡 Execute primeiro alguns pedidos para gerar logs")
                input("\nPressione Enter para continuar...")
                return
            
            print(f"📂 Analisando logs em: {diretorio_logs}")
            print("\n🔄 Carregando dados...")
            
            # Cria o analisador e carrega os logs
            analisador = AnalisadorPedidos(diretorio_logs)
            analisador.carregar_logs()
            
            # Detecta e exibe duplicatas
            print("\n🔍 Buscando atividades compartilhadas...")
            duplicatas = analisador.exibir_relatorio_duplicatas()
            
            if not duplicatas:
                print("\n✅ Nenhuma atividade compartilhada encontrada!")
                print("🎆 Todos os pedidos estão usando equipamentos exclusivos")
            else:
                print(f"\n📈 Resumo:")
                print(f"   • Total de IDs compartilhados: {len(duplicatas)}")
                total_ocorrencias = sum(len(ocorrencias) for ocorrencias in duplicatas.values())
                print(f"   • Total de ocorrências: {total_ocorrencias}")
                
                # Identifica pedidos afetados
                pedidos_afetados = set()
                for id_atividade, ocorrencias in duplicatas.items():
                    for ordem, pedido, _ in ocorrencias:
                        pedidos_afetados.add((ordem, pedido))
                
                print(f"   • Pedidos afetados: {len(pedidos_afetados)}")
                
                print("\n💡 RECOMENDAÇÕES:")
                print("   • Use a opção 'Estimar Fim de Jornada' para reagendar pedidos")
                print("   • Considere executar pedidos em ordem diferente")
                print("   • Verifique se há equipamentos alternativos disponíveis")
            
        except Exception as e:
            print(f"\n⚠️ Erro ao analisar atividades: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPressione Enter para continuar...")
    
    def estimar_fim_jornada(self):
        """Estima fim de jornada com base em reagendamento"""
        self.utils.limpar_tela()
        print("⏰ ESTIMATIVA DE FIM DE JORNADA")
        print("=" * 50)
        
        try:
            # Define o diretório de logs
            diretorio_logs = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/equipamentos"
            
            if not os.path.exists(diretorio_logs):
                print(f"⚠️ Diretório de logs não encontrado: {diretorio_logs}")
                print("💡 Execute primeiro alguns pedidos para gerar logs")
                input("\nPressione Enter para continuar...")
                return
            
            print(f"📂 Analisando logs em: {diretorio_logs}")
            print("\n🔄 Carregando dados...")
            
            # Cria o analisador e carrega os logs
            analisador = AnalisadorPedidos(diretorio_logs)
            analisador.carregar_logs()
            duplicatas = analisador.detectar_atividades_duplicadas()
            
            if not duplicatas:
                print("\nℹ️ Nenhuma atividade compartilhada encontrada")
                print("🎆 Não há necessidade de reagendamento")
                input("\nPressione Enter para continuar...")
                return
            
            print("\n🔍 Atividades compartilhadas detectadas!")
            print("🔄 Calculando reagendamentos...")
            
            # Cria o calculador e executa reagendamento
            calculador = CalculadorReagendamento(analisador)
            ordem_base, pedido_base, resultados = calculador.calcular_reagendamentos(duplicatas)
            
            if not resultados:
                print("\n⚠️ Não foi possível calcular reagendamentos")
            else:
                print(f"\n🎚️ Pedido Base: Ordem {ordem_base} | Pedido {pedido_base}")
                print("   (Este pedido mantém seus horários originais)")
                
                print("\n📈 REAGENDAMENTOS CALCULADOS:")
                print("=" * 50)
                
                for (ordem, pedido), dados in resultados.items():
                    print(f"\n📦 Ordem {ordem} | Pedido {pedido}:")
                    print(f"   • Horário Final da Jornada: {dados['horario_final_jornada']}")
                    print(f"   • Total de Atividades: {len(dados['atividades'])}")
                
                # Calcula fim de jornada
                from datetime import datetime
                fim_max = None
                for (ordem, pedido), dados in resultados.items():
                    horario_final = dados['horario_final_jornada']
                    if isinstance(horario_final, datetime):
                        if fim_max is None or horario_final > fim_max:
                            fim_max = horario_final
                
                # Adiciona o fim do pedido base
                if ordem_base and pedido_base:
                    pedido_base_data = analisador.pedidos.get((ordem_base, pedido_base), [])
                    if pedido_base_data:
                        ultima_atividade = pedido_base_data[-1]
                        fim_str = ultima_atividade['fim']
                        match = re.match(r'(\d{2}):(\d{2}) \[(\d{2})/(\d{2})\]', fim_str)
                        if match:
                            hora, minuto, dia, mes = match.groups()
                            fim_dt = datetime(2024, int(mes), int(dia), int(hora), int(minuto))
                            if fim_max is None or fim_dt > fim_max:
                                fim_max = fim_dt
                
                if fim_max:
                    print("\n⏰ ESTIMATIVA DE FIM DE JORNADA:")
                    print("=" * 50)
                    print(f"   🏁 Fim estimado: {fim_max.strftime('%H:%M')} [{fim_max.strftime('%d/%m')}]")
                    print(f"   📅 Data: {fim_max.strftime('%d/%m/%Y')}")
                    print(f"   ⏱️ Hora: {fim_max.strftime('%H:%M')}")
                    
                print("\n💡 OBSERVAÇÕES:")
                print("   • Reagendamento baseado em backward scheduling")
                print("   • Pedidos são deslocados para evitar conflitos")
                print("   • Tempo de produção de cada atividade é mantido")
            
        except Exception as e:
            print(f"\n⚠️ Erro ao estimar fim de jornada: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPressione Enter para continuar...")

    def executar_ordem_reabastecimento(self):
        """Executa ordem de reabastecimento a partir de CSV"""
        self.utils.limpar_tela()
        print("🔄 EXECUTAR ORDEM DE REABASTECIMENTO")
        print("=" * 80)
        print()
        print("📁 Pasta: data/csv/reabastecimento/")
        print("📋 Os pedidos de reabastecimento serão processados e executados")
        print()

        # Diretório de reabastecimento
        csv_dir = "data/csv/reabastecimento"

        if not os.path.exists(csv_dir):
            print("❌ Pasta 'data/csv/reabastecimento' não encontrada!")
            print("💡 Gere primeiro um CSV de reabastecimento na opção 3")
            input("\nPressione Enter para continuar...")
            return

        # Listar arquivos CSV disponíveis
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]

        if not csv_files:
            print("❌ Nenhum arquivo CSV de reabastecimento encontrado!")
            print("💡 Gere primeiro um CSV de reabastecimento:")
            print("   1. Vá em 'Verificar Estoque (Opção 3)'")
            print("   2. Responda 'S' para gerar o CSV")
            input("\nPressione Enter para continuar...")
            return

        # Ordenar por data (mais recente primeiro)
        csv_files.sort(reverse=True)

        print("📂 Arquivos CSV de reabastecimento disponíveis:")
        print()
        for i, arquivo in enumerate(csv_files, 1):
            caminho = os.path.join(csv_dir, arquivo)

            # Contar itens no CSV
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    total_itens = sum(1 for _ in f) - 1  # -1 para excluir cabeçalho

                # Extrair data do nome do arquivo (pedidos_YYYY_MM_DD.csv)
                if arquivo.startswith('pedidos_'):
                    data_str = arquivo.replace('pedidos_', '').replace('.csv', '')
                    try:
                        data_obj = datetime.strptime(data_str, '%Y_%m_%d')
                        data_formatada = data_obj.strftime('%d/%m/%Y')
                        print(f"   {i}. {arquivo}")
                        print(f"      📅 Data: {data_formatada} | 📦 Itens: {total_itens}")
                    except:
                        print(f"   {i}. {arquivo} ({total_itens} itens)")
                else:
                    print(f"   {i}. {arquivo} ({total_itens} itens)")
            except Exception as e:
                print(f"   {i}. {arquivo} (erro ao ler)")

        print()

        try:
            escolha = input("🎯 Digite o número do arquivo ou 'V' para voltar: ").strip()

            if escolha.upper() == 'V':
                return

            indice = int(escolha) - 1
            if 0 <= indice < len(csv_files):
                arquivo_escolhido = csv_files[indice]
                caminho_completo = os.path.join(csv_dir, arquivo_escolhido)

                print(f"\n📂 Arquivo selecionado: {arquivo_escolhido}")

                # Confirmar execução
                confirmar = input("\n⚠️ Deseja executar esta ordem de reabastecimento? (S/N): ").strip().upper()

                if confirmar != 'S':
                    print("❌ Execução cancelada")
                    input("\nPressione Enter para continuar...")
                    return

                # Processar o CSV de reabastecimento
                self._processar_csv_reabastecimento(caminho_completo)
            else:
                print("❌ Número inválido!")
                input("\nPressione Enter para continuar...")

        except ValueError:
            print("❌ Entrada inválida!")
            input("\nPressione Enter para continuar...")
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            input("\nPressione Enter para continuar...")

    def _processar_csv_reabastecimento(self, caminho_arquivo):
        """Processa arquivo CSV de reabastecimento e executa pedidos"""
        try:
            pedidos_registrados = []
            erros = []

            print(f"\n{'=' * 80}")
            print(f"📂 PROCESSANDO: {os.path.basename(caminho_arquivo)}")
            print(f"{'=' * 80}")
            print()

            # Ler CSV
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                reader = csv.DictReader(arquivo)

                # Validar cabeçalhos
                colunas_esperadas = {'id', 'tipo_produto', 'quantidade', 'fim_jornada'}
                if not colunas_esperadas.issubset(set(reader.fieldnames)):
                    print(f"❌ Colunas inválidas no CSV!")
                    print(f"📋 Esperado: {', '.join(colunas_esperadas)}")
                    print(f"📋 Encontrado: {', '.join(reader.fieldnames)}")
                    input("\nPressione Enter para continuar...")
                    return

                for linha_num, linha in enumerate(reader, 2):  # +2 pois linha 1 é cabeçalho
                    try:
                        # Converter dados
                        id_item = int(linha['id'].strip())
                        tipo_item = linha['tipo_produto'].strip().upper()
                        quantidade = int(linha['quantidade'].strip())
                        fim_jornada_str = linha['fim_jornada'].strip()

                        # Converter data
                        fim_jornada = datetime.strptime(fim_jornada_str, '%Y-%m-%d %H:%M:%S')

                        # Validar tipo (deve ser SUBPRODUTO)
                        if tipo_item != 'SUBPRODUTO':
                            raise ValueError(f"Tipo inválido: {tipo_item} (esperado: SUBPRODUTO)")

                        # Registrar pedido
                        sucesso, mensagem = self.gerenciador.registrar_pedido(
                            id_item=id_item,
                            tipo_item=tipo_item,
                            quantidade=quantidade,
                            fim_jornada=fim_jornada
                        )

                        if sucesso:
                            pedidos_registrados.append({
                                'id': id_item,
                                'quantidade': quantidade,
                                'fim_jornada': fim_jornada
                            })
                            print(f"✅ Linha {linha_num}: Pedido {id_item} registrado (Qtd: {quantidade})")
                        else:
                            erros.append(f"Linha {linha_num}: {mensagem}")
                            print(f"❌ Linha {linha_num}: {mensagem}")

                    except Exception as e:
                        erros.append(f"Linha {linha_num}: {str(e)}")
                        print(f"❌ Linha {linha_num}: Erro - {e}")

            # Resumo do processamento
            print(f"\n{'=' * 80}")
            print(f"📊 RESUMO DO PROCESSAMENTO")
            print(f"{'=' * 80}")
            print(f"✅ Pedidos registrados: {len(pedidos_registrados)}")
            print(f"❌ Erros: {len(erros)}")

            if not pedidos_registrados:
                print("\n⚠️ Nenhum pedido foi registrado com sucesso!")
                input("\nPressione Enter para continuar...")
                return

            # Perguntar se deseja executar agora
            print(f"\n{'=' * 80}")
            executar = input(f"\n🚀 Deseja executar os {len(pedidos_registrados)} pedidos agora? (S/N): ").strip().upper()

            if executar != 'S':
                print("\n💡 Os pedidos foram registrados mas não executados")
                print("   Você pode executá-los depois no Menu Principal > Opção 7 ou 8")
                input("\nPressione Enter para continuar...")
                return

            # Escolher modo de execução
            print(f"\n{'=' * 80}")
            print("📋 ESCOLHA O MODO DE EXECUÇÃO:")
            print(f"{'=' * 80}")
            print("1️⃣  SEQUENCIAL - Execução otimizada sem dependências externas")
            print("2️⃣  OTIMIZADO (PL) - Programação Linear para melhor resultado")
            print()

            modo = input("🎯 Escolha o modo (1 ou 2): ").strip()

            if modo not in ['1', '2']:
                print("\n❌ Opção inválida! Execução cancelada.")
                print("💡 Use o Menu Principal > Opção 7 ou 8 para executar depois")
                input("\nPressione Enter para continuar...")
                return

            # Obter pedidos da ordem atual (que acabamos de registrar)
            ordem_atual = self.gerenciador.obter_ordem_atual()
            pedidos_ordem = self.gerenciador.obter_pedidos_ordem_atual()

            if not pedidos_ordem:
                print("\n⚠️ Erro: Nenhum pedido encontrado na ordem atual!")
                input("\nPressione Enter para continuar...")
                return

            # Executar pedidos
            print(f"\n{'=' * 80}")
            print(f"🚀 EXECUTANDO PEDIDOS DE REABASTECIMENTO - ORDEM {ordem_atual}")
            print(f"{'=' * 80}")
            print(f"📦 Total de pedidos: {len(pedidos_ordem)}")
            print(f"⚙️ Modo: {'SEQUENCIAL' if modo == '1' else 'OTIMIZADO (PL)'}")
            print()

            try:
                if modo == '1':
                    # Execução SEQUENCIAL
                    sucesso = self.gestor_producao.executar_sequencial(pedidos_ordem)
                else:
                    # Execução OTIMIZADA
                    sucesso = self.gestor_producao.executar_otimizado(pedidos_ordem)

                # Incrementar ordem após execução
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()

                if sucesso:
                    print(f"\n{'=' * 80}")
                    print("✅ EXECUÇÃO CONCLUÍDA COM SUCESSO!")
                    print(f"{'=' * 80}")
                    print(f"📈 Ordem {ordem_atual} executada")
                    print(f"🔄 Sistema avançou para Ordem {nova_ordem}")
                    print("\n💡 Verifique os logs em:")
                    print("   📁 logs/equipamentos/sucesso/")
                    print(f"   📄 ordem: {ordem_atual} | pedido: X.log")
                else:
                    print(f"\n{'=' * 80}")
                    print("⚠️ EXECUÇÃO CONCLUÍDA COM ERROS")
                    print(f"{'=' * 80}")
                    print("\n💡 Verifique os logs de erro em:")
                    print("   📁 logs/equipamentos/erros/")

            except Exception as e:
                print(f"\n❌ Erro durante a execução: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"\n❌ Erro ao processar CSV: {e}")
            import traceback
            traceback.print_exc()

        input("\nPressione Enter para continuar...")

    def _oferecer_geracao_csv_reabastecimento(self):
        """Oferece opção de gerar CSV de reabastecimento após verificar estoque"""
        from datetime import datetime
        from services.gestores.reabastecimento.detector_itens_criticos import DetectorItensCriticos
        from services.gestores.reabastecimento.gerador_csv_reabastecimento import GeradorCSVReabastecimento

        print("\n" + "=" * 80)
        print("🔄 GERAÇÃO DE CSV DE REABASTECIMENTO")
        print("=" * 80)

        # Perguntar se deseja gerar CSV
        resposta = input("\n📝 Deseja gerar o CSV com a ordem de reabastecimento de estoque? (S/N): ").strip().upper()

        if resposta != 'S':
            print("❌ Geração de CSV cancelada")
            return

        try:
            # Obter almoxarifado
            almoxarifado = self.gestor_producao.configurador_ambiente.gestor_almoxarifado.almoxarifado

            # Detectar itens críticos (SUBPRODUTO + ESTOCADO + abaixo do mínimo)
            print("\n🔍 Detectando subprodutos críticos...")
            detector = DetectorItensCriticos(almoxarifado)
            itens_criticos = detector.detectar_itens_criticos()

            if not itens_criticos:
                print("\n✅ Nenhum subproduto estocado abaixo do mínimo!")
                print("💡 Somente SUBPRODUTOS com política ESTOCADO são incluídos no CSV")
                return

            # Mostrar itens que serão incluídos
            print(f"\n📋 {len(itens_criticos)} subproduto(s) será(ão) incluído(s) no CSV:")
            print("\n" + "=" * 80)
            print(f"{'ID':<6} {'NOME':<30} {'ATUAL':<12} {'REABASTECER':<15}")
            print("=" * 80)

            for item in itens_criticos[:10]:  # Mostrar até 10 itens
                print(f"{item['id']:<6} {item['nome'][:29]:<30} {item['estoque_atual']:<12.1f} {item['quantidade_reabastecer']:<15.0f}")

            if len(itens_criticos) > 10:
                print(f"... e mais {len(itens_criticos) - 10} item(ns)")

            print("=" * 80)

            # Gerar e mostrar resumo
            resumo = detector.obter_resumo_criticos(itens_criticos)
            print(f"\n📊 RESUMO:")
            print(f"   • Total de itens: {resumo['total_itens']}")
            print(f"   • Quantidade total a reabastecer: {resumo['quantidade_total_reabastecer']:.0f}")

            # Escolher modo de geração do CSV
            gerador = GeradorCSVReabastecimento()

            print("\n" + "=" * 80)
            print("⚙️  MODO DE GERAÇÃO DO CSV")
            print("=" * 80)
            print("\n1️⃣  Data única para todos os pedidos")
            print("    → Todos os pedidos terão a mesma data de conclusão")
            print("\n2️⃣  Datas individuais calculadas por duração")
            print("    → Cada pedido terá sua data calculada: hora atual + buffer + duração")

            modo = input("\n📝 Escolha o modo (1 ou 2): ").strip()

            if modo == '1':
                # Modo 1: Data única
                self._gerar_csv_data_unica(gerador, itens_criticos)
            elif modo == '2':
                # Modo 2: Datas individuais
                self._gerar_csv_datas_individuais(gerador, itens_criticos)
            else:
                print("❌ Opção inválida. Cancelando geração do CSV.")

        except Exception as e:
            print(f"\n❌ Erro ao gerar CSV: {e}")
            import traceback
            traceback.print_exc()

    def _gerar_csv_data_unica(self, gerador, itens_criticos):
        """Gera CSV com data única para todos os pedidos"""
        data_sugerida = gerador.obter_data_sugerida()

        print(f"\n📅 Data sugerida para conclusão: {gerador.formatar_data_para_exibicao(data_sugerida)}")
        alterar_data = input("   Deseja alterar a data? (S/N): ").strip().upper()

        data_entrega = data_sugerida
        if alterar_data == 'S':
            data_entrega = self._solicitar_data_hora_entrega(data_sugerida)

        # Gerar CSV
        print("\n🔄 Gerando arquivo CSV...")
        sucesso, caminho, mensagem = gerador.gerar_csv_reabastecimento(itens_criticos, data_entrega)

        print(f"\n{mensagem}")

        if sucesso:
            print(f"\n📁 Arquivo gerado em:")
            print(f"   {caminho}")
            print(f"\n✅ O arquivo pode ser usado para importar pedidos de reabastecimento")

    def _gerar_csv_datas_individuais(self, gerador, itens_criticos):
        """Gera CSV com datas individuais calculadas por duração"""
        print("\n⏱️  CONFIGURAÇÃO DO BUFFER DE TEMPO")
        print("=" * 80)
        print("O buffer é o tempo adicional antes do início da produção.")
        print("Fórmula: Data de conclusão = hora atual + buffer + duração do pedido")

        buffer_padrao = 2.0
        buffer_str = input(f"📝 Digite o buffer em horas [{buffer_padrao:.1f}h]: ").strip()

        try:
            if buffer_str:
                buffer_horas = float(buffer_str)
                if buffer_horas < 0:
                    print("⚠️ Buffer não pode ser negativo. Usando padrão.")
                    buffer_horas = buffer_padrao
            else:
                buffer_horas = buffer_padrao
        except ValueError:
            print("⚠️ Valor inválido. Usando buffer padrão.")
            buffer_horas = buffer_padrao

        print(f"\n✅ Buffer configurado: {buffer_horas:.1f}h")

        # Gerar CSV com datas individuais
        print("\n🔄 Calculando durações e gerando arquivo CSV...")
        sucesso, caminho, mensagem = gerador.gerar_csv_com_datas_individuais(itens_criticos, buffer_horas)

        print(f"\n{mensagem}")

        if sucesso:
            print(f"\n📁 Arquivo gerado em:")
            print(f"   {caminho}")
            print(f"\n✅ O arquivo pode ser usado para importar pedidos de reabastecimento")
            print(f"💡 Cada pedido possui sua data de conclusão individual calculada")

    def _solicitar_data_hora_entrega(self, data_padrao: datetime) -> datetime:
        """Solicita data e hora de entrega ao usuário"""
        from datetime import datetime

        print("\n📅 CONFIGURAR DATA/HORA DE ENTREGA")
        print("=" * 50)

        try:
            # Solicitar data
            data_str = input(f"Digite a data (DD/MM/YYYY) [{data_padrao.strftime('%d/%m/%Y')}]: ").strip()

            if not data_str:
                data_str = data_padrao.strftime('%d/%m/%Y')

            # Solicitar hora
            hora_str = input(f"Digite a hora (HH:MM) [{data_padrao.strftime('%H:%M')}]: ").strip()

            if not hora_str:
                hora_str = data_padrao.strftime('%H:%M')

            # Parsear data e hora
            datetime_str = f"{data_str} {hora_str}"
            data_entrega = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M')

            print(f"✅ Data configurada: {data_entrega.strftime('%d/%m/%Y %H:%M')}")
            return data_entrega

        except Exception as e:
            print(f"⚠️ Erro ao processar data: {e}")
            print(f"💡 Usando data padrão: {data_padrao.strftime('%d/%m/%Y %H:%M')}")
            return data_padrao


    def recuperar_estado_logs(self):
        """Recupera estado do sistema a partir dos logs detalhados"""
        from utils.recuperacao.detector_logs import DetectorLogs
        from utils.recuperacao.recuperador_estado import RecuperadorEstado

        self.utils.limpar_tela()
        print("=" * 80)
        print("📸 RECUPERAR ESTADO DO SISTEMA")
        print("=" * 80)

        try:
            # Detectar logs disponíveis
            detector = DetectorLogs()
            logs_disponiveis = detector.detectar_logs()

            if not logs_disponiveis:
                print("\nℹ️  Nenhum log detalhado encontrado.")
                print("💡 Execute pelo menos uma ordem para gerar logs de equipamentos.")
                input("\nPressione Enter para continuar...")
                return

            print(f"\n📋 Logs detalhados encontrados: {len(logs_disponiveis)}")
            print("=" * 80)

            # Mostrar os 5 logs mais recentes
            for idx, log_info in enumerate(logs_disponiveis[:5], 1):
                print(f"\n{idx}. {log_info['nome']}")
                print(f"   📅 Data: {log_info['data_modificacao'].strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"   📦 Tamanho: {log_info['tamanho'] / 1024:.1f} KB")
                if log_info.get('ordem'):
                    print(f"   📋 Ordem: {log_info['ordem']} | Pedidos: {', '.join(map(str, log_info.get('pedidos', [])))}")

            if len(logs_disponiveis) > 5:
                print(f"\n... e mais {len(logs_disponiveis) - 5} log(s)")

            # Perguntar qual log usar
            print("\n" + "=" * 80)
            print("🔍 SELECIONAR LOG PARA RECUPERAÇÃO")
            print("=" * 80)

            escolha = input("\nDeseja usar o log mais recente? (S/n): ").strip().lower()

            if escolha in ['n', 'nao', 'não']:
                print("\n📋 Logs disponíveis:")
                for idx, log_info in enumerate(logs_disponiveis, 1):
                    print(f"{idx}. {log_info['nome']}")

                try:
                    num = int(input(f"\nEscolha um log (1-{len(logs_disponiveis)}): "))
                    if 1 <= num <= len(logs_disponiveis):
                        log_selecionado = logs_disponiveis[num - 1]
                    else:
                        print("❌ Opção inválida. Usando log mais recente.")
                        log_selecionado = logs_disponiveis[0]
                except ValueError:
                    print("❌ Entrada inválida. Usando log mais recente.")
                    log_selecionado = logs_disponiveis[0]
            else:
                log_selecionado = logs_disponiveis[0]

            print("\n" + "=" * 80)
            print("🔄 RECUPERANDO ESTADO DOS EQUIPAMENTOS")
            print("=" * 80)
            print(f"\n📁 Arquivo: {log_selecionado['nome']}")

            # Confirmar aplicação
            aplicar = input("\n⚠️  Aplicar restauração aos equipamentos? (s/N): ").strip().lower()
            aplicar_restauracao = aplicar in ['s', 'sim', 'yes']

            if not aplicar_restauracao:
                print("\nℹ️  Modo SOMENTE LEITURA - Nenhuma alteração será feita nos equipamentos")

            # Executar recuperação
            recuperador = RecuperadorEstado(self.gestor_producao)
            relatorio = recuperador.recuperar_de_log(
                log_selecionado['caminho'],
                aplicar_restauracao=aplicar_restauracao
            )

            # Mostrar relatório
            print("\n" + "=" * 80)
            print("📊 RELATÓRIO DE RECUPERAÇÃO")
            print("=" * 80)
            print(relatorio.gerar_resumo())

            # Estatísticas por tipo
            stats_tipo = relatorio.estatisticas_por_tipo()
            if stats_tipo:
                print("\n📈 Ocupações por tipo de equipamento:")
                for tipo, count in sorted(stats_tipo.items(), key=lambda x: x[1], reverse=True):
                    print(f"   • {tipo}: {count}")

            # Mostrar erros se houver
            if relatorio.tem_erros:
                print(f"\n⚠️  Erros encontrados ({relatorio.total_erros}):")

                # Mostrar erros globais
                if relatorio.erros_globais:
                    print("\n   📋 Erros globais:")
                    for erro in relatorio.erros_globais[:5]:
                        print(f"      • {erro}")
                    if len(relatorio.erros_globais) > 5:
                        print(f"      ... e mais {len(relatorio.erros_globais) - 5} erro(s)")

                # Mostrar equipamentos com erros
                equipamentos_com_erro = [e for e in relatorio.equipamentos if e.erros]
                if equipamentos_com_erro:
                    print(f"\n   🔧 Equipamentos com erros ({len(equipamentos_com_erro)}):")
                    for equip in equipamentos_com_erro[:3]:
                        print(f"      • {equip.nome_equipamento}: {len(equip.erros)} erro(s)")
                    if len(equipamentos_com_erro) > 3:
                        print(f"      ... e mais {len(equipamentos_com_erro) - 3} equipamento(s)")

            # Status final
            print("\n" + "=" * 80)
            if relatorio.sucesso:
                print("✅ RECUPERAÇÃO CONCLUÍDA COM SUCESSO!")
                if aplicar_restauracao:
                    print("✅ Estado dos equipamentos foi restaurado")
                else:
                    print("ℹ️  Nenhuma alteração foi feita (modo leitura)")
            else:
                print("❌ RECUPERAÇÃO FALHOU")
                print("💡 Verifique os erros acima para mais detalhes")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ Erro ao recuperar estado: {e}")
            import traceback
            traceback.print_exc()

        input("\nPressione Enter para continuar...")


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