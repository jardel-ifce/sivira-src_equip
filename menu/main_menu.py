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
        
        # 🆕 LIMPEZA AUTOMÁTICA DE LOGS
        try:
            # 🆕 MODIFICAÇÃO: Agora limpar_logs_inicializacao() já inclui limpeza de pedidos salvos
            relatorio_limpeza = limpar_logs_inicializacao()
            
            # Como agora retorna string formatada, vamos exibir
            if isinstance(relatorio_limpeza, str):
                print(relatorio_limpeza)
            else:
                # Compatibilidade com versão antiga
                if relatorio_limpeza['sucesso']:
                    if relatorio_limpeza['total_arquivos_removidos'] > 0:
                        print("✅ Ambiente de logs limpo e pronto!")
                    else:
                        print("📭 Ambiente de logs já estava limpo!")
                else:
                    print("⚠️ Limpeza de logs concluída com alguns erros (sistema continuará)")
                
        except Exception as e:
            print(f"⚠️ Erro durante limpeza de logs: {e}")
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
                print(f"\n⌨ Erro inesperado: {e}")
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
        print("🧹 Limpeza automática integrada")
        print("📦 Sistema de Ordens/Sessões para agrupamento")
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
        print("🏗️ Arquitetura: Independente (services/gestor_producao)")
        print("🧹 Limpeza: Automática (logs limpos na inicialização)")
        print("📦 Sistema: Ordens/Sessões ativo")
        
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
        print("4️⃣  Limpar Pedidos da Ordem Atual")
        print("5️⃣  Limpar Todos os Pedidos")
        print()
        print("🚀 EXECUÇÃO:")
        print("6️⃣  Executar Ordem Atual (SEQUENCIAL)")
        print("7️⃣  Executar Ordem Atual (OTIMIZADO PL)")
        print()
        print("⚙️ SISTEMA:")
        print("8️⃣  Testar Sistema")
        print("9️⃣  Configurações")
        print("A️⃣  Limpar Logs Manualmente")
        print("B️⃣  Histórico de Ordens")  # 🆕 Nova opção
        print("C️⃣  Debug Sistema Ordens")  # 🆕 Debug option
        print("0️⃣  Ajuda")
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
            self.limpar_ordem_atual()
        
        elif opcao == "5":
            self.limpar_todos_pedidos()
        
        elif opcao == "6":
            self.executar_sequencial()
        
        elif opcao == "7":
            self.executar_otimizado()
        
        elif opcao == "8":
            self.testar_sistema()
        
        elif opcao == "9":
            self.mostrar_configuracoes()
        
        elif opcao.lower() == "a":
            self.limpar_logs_manualmente()
        
        elif opcao.lower() == "b":  # 🆕 Nova opção
            self.mostrar_historico_ordens()
        
        elif opcao.lower() == "c":  # 🆕 Debug option
            self.debug_sistema_ordens()
        
        elif opcao == "0":
            self.mostrar_ajuda()
        
        elif opcao.lower() in ["sair", "s", "quit", "exit"]:
            self.sair()
        
        else:
            print(f"\n⌨ Opção '{opcao}' inválida!")
            input("Pressione Enter para continuar...")
    
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
                    print(f"\n⌨ {mensagem}")
            else:
                print("\nℹ️ Registro cancelado.")
                
        except Exception as e:
            print(f"\n⌨ Erro ao registrar pedido: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def listar_pedidos(self):
        """Lista todos os pedidos registrados"""
        self.utils.limpar_tela()
        print("📋 PEDIDOS REGISTRADOS")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("📭 Nenhum pedido registrado ainda.")
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
        print("🗑️ REMOVER PEDIDO")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("📭 Nenhum pedido para remover.")
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
                    print("\n⌨ Formato inválido!")
                    input("Pressione Enter para continuar...")
                    return
                
                print(f"\n{'✅' if sucesso else '⌨'} {mensagem}")
                
                if sucesso:
                    # Auto-salva após remoção
                    self.gerenciador.salvar_pedidos()
            else:
                print("\nℹ️ Remoção cancelada.")
                
        except ValueError:
            print("\n⌨ Formato inválido! Use números.")
        except Exception as e:
            print(f"\n⌨ Erro ao remover pedido: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def limpar_ordem_atual(self):
        """🆕 Remove apenas pedidos da ordem atual"""
        self.utils.limpar_tela()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        pedidos_ordem = self.gerenciador.obter_pedidos_ordem_atual()
        
        print("🗑️ LIMPAR ORDEM ATUAL")
        print("=" * 40)
        
        if not pedidos_ordem:
            print(f"📭 Ordem {ordem_atual} não possui pedidos para limpar.")
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
        print("🗑️ LIMPAR TODOS OS PEDIDOS")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("📭 Nenhum pedido para limpar.")
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
        
        print("🔄 EXECUÇÃO SEQUENCIAL")
        print("=" * 40)
        print(f"📦 Executando Ordem: {ordem_atual}")
        
        if not pedidos_ordem:
            print(f"📭 Ordem {ordem_atual} não possui pedidos para executar.")
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
                    print(f"\n⌨ Falha na execução sequencial da Ordem {ordem_atual}!")
                    print(f"📈 Mesmo assim, sistema avançou para Ordem {nova_ordem}")
                    print("💡 Isso evita conflitos de IDs entre ordens com erro e novas ordens")
                    
            except Exception as e:
                # 🆕 MESMO EM CASO DE EXCEPTION, incrementa ordem
                print(f"\n⌨ Erro durante execução: {e}")
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
            print(f"📭 Ordem {ordem_atual} não possui pedidos para executar.")
            print("\n💡 Use a opção '1' para registrar pedidos primeiro")
            input("\nPressione Enter para continuar...")
            return
        
        # Verifica OR-Tools primeiro
        ortools_ok, ortools_msg = self.utils.validar_or_tools()
        print(f"🔧 OR-Tools: {'✅' if ortools_ok else '⌨'} {ortools_msg}")
        
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
            try:
                # Executa apenas pedidos da ordem atual
                sucesso = self.gestor_producao.executar_otimizado(pedidos_ordem)
                
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
                    print(f"\n⌨ Falha na execução otimizada da Ordem {ordem_atual}!")
                    print(f"📈 Mesmo assim, sistema avançou para Ordem {nova_ordem}")
                    print("💡 Isso evita conflitos de IDs entre ordens com erro e novas ordens")
                    
            except Exception as e:
                # 🆕 MESMO EM CASO DE EXCEPTION, incrementa ordem
                print(f"\n⌨ Erro durante execução otimizada: {e}")
                nova_ordem = self.gerenciador.incrementar_ordem()
                self.gerenciador.salvar_pedidos()
                print(f"📈 Ordem incrementada para {nova_ordem} (devido ao erro)")
                print("💡 Isso evita conflitos de IDs em futuras execuções")
        else:
            print("\nℹ️ Execução cancelada.")
        
        input("\nPressione Enter para continuar...")
    
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
            
            print(f"🏗️ Arquitetura: Independente (services/gestor_producao)")
            print(f"📦 Sistema de Ordens: Ativo (Ordem atual: {self.gerenciador.obter_ordem_atual()})")
            
        except Exception as e:
            print(f"⌨ Erro durante teste: {e}")
        
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
        print(f"🏗️ Nova Arquitetura:")
        print(f"   Gestor: services/gestor_producao/")
        print(f"   Independente: ✅ Desacoplado dos scripts de teste")
        print(f"   Limpeza: ✅ Automática integrada")
        print(f"   Ordens: ✅ Sistema de sessões ativo")
        print()
        
        # Status do sistema
        stats = self.gerenciador.obter_estatisticas()
        print(f"📋 Status:")
        print(f"   OR-Tools: {'✅ Disponível' if info_sistema['ortools_disponivel'] else '⌨ Não encontrado'}")
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
                print("⌨ Valores inválidos!")
        
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
                print(f"⌨ Erro durante limpeza: {e}")
        
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
                print(f"⌨ Erro ao limpar {pasta}: {e}")
        
        elif opcao == "6":  # 🆕 MODIFICAÇÃO: Nova opção
            print(f"\n🧹 Limpando arquivo de pedidos salvos...")
            try:
                from utils.logs.gerenciador_logs import limpar_arquivo_pedidos_salvos
                if limpar_arquivo_pedidos_salvos():
                    print("✅ Arquivo de pedidos salvos removido")
                else:
                    print("📄 Arquivo de pedidos salvos não existia")
            except Exception as e:
                print(f"⌨ Erro ao limpar arquivo de pedidos: {e}")
        
        elif opcao == "0":
            return
        else:
            print("⌨ Opção inválida!")
        
        input("\nPressione Enter para continuar...")
    
    def mostrar_historico_ordens(self):
        """🆕 Mostra histórico de ordens executadas"""
        self.utils.limpar_tela()
        print("📈 HISTÓRICO DE ORDENS")
        print("=" * 40)
        
        ordens_existentes = self.gerenciador.listar_ordens_existentes()
        ordem_atual = self.gerenciador.obter_ordem_atual()
        
        if not ordens_existentes:
            print("📭 Nenhuma ordem registrada ainda.")
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
        """🆕 Debug do sistema de ordens"""
        self.utils.limpar_tela()
        print("🔍 DEBUG - SISTEMA DE ORDENS")
        print("=" * 40)
        
        self.gerenciador.debug_sistema_ordens()
        
        print("\n🔍 DEBUG - ESTRUTURA DE DIRETÓRIOS")
        print("=" * 40)
        
        estrutura = self.gerenciador.verificar_estrutura_diretorios()
        for nome, info in estrutura.items():
            status = "✅" if info["existe"] and info["eh_diretorio"] else "❌"
            print(f"{status} {nome.upper()}:")
            print(f"   📁 Caminho: {info['caminho']}")
            print(f"   📂 Existe: {info['existe']}")
            print(f"   📋 É diretório: {info['eh_diretorio']}")
            
            if nome == "pedidos_salvos":
                print(f"   📄 Arquivo de pedidos: {info.get('arquivo_pedidos_existe', False)}")
                if info.get('tamanho_arquivo'):
                    print(f"   📊 Tamanho: {info['tamanho_arquivo']} bytes")
                    print(f"   🕒 Modificado: {info.get('modificado_em', 'N/A')}")
            print()
        
        input("\nPressione Enter para continuar...")
    
    def mostrar_ajuda(self):
        """Mostra ajuda do sistema"""
        self.utils.limpar_tela()
        print("❓ AJUDA DO SISTEMA")
        print("=" * 40)
        
        print("📋 COMO USAR:")
        print()
        print("1️⃣ SISTEMA DE ORDENS:")
        print("   • Cada sessão de trabalho tem uma ordem (ex: Ordem 1)")
        print("   • Pedidos são numerados dentro da ordem (ex: Pedido 1, 2, 3...)")
        print("   • Formato: Ordem X | Pedido Y")
        print("   • Após execução, ordem é incrementada automaticamente")
        print()
        print("2️⃣ REGISTRAR PEDIDOS:")
        print("   • Digite o ID do item (ex: 1001)")
        print("   • Escolha PRODUTO ou SUBPRODUTO")
        print("   • Informe a quantidade")
        print("   • Digite fim da jornada (ex: 07:00:00 11/08/2025)")
        print("   • O início será calculado automaticamente (3 dias antes)")
        print("   • Pedido será registrado na ordem atual")
        print()
        print("3️⃣ EXECUÇÃO:")
        print("   • Executa APENAS pedidos da ordem atual")
        print("   • Sequencial: Rápido e eficiente")
        print("   • Otimizado: Usa Programação Linear (requer OR-Tools)")
        print("   • Ordem SEMPRE incrementa após execução (sucesso ou falha)")
        print("   • Isso evita conflitos de IDs entre ordens")
        print()
        print("4️⃣ GERENCIAMENTO:")
        print("   • Listar: Mostra todos os pedidos agrupados por ordem")
        print("   • Remover: Remove pedido específico (Ordem X | Pedido Y)")
        print("   • Limpar Ordem: Remove apenas pedidos da ordem atual")
        print("   • Limpar Todos: Remove todos os pedidos de todas as ordens")
        print()
        print("🏗️ ARQUITETURA:")
        print("   • Independente: Não depende de scripts de teste")
        print("   • Modular: services/gestor_producao")
        print("   • Limpa: Limpeza automática de logs")
        print("   • Organizada: Sistema de ordens para sessões")
        print()
        print("📦 EXEMPLO DE FLUXO:")
        print("   1. Registrar: Ordem 1 | Pedido 1 (Pão)")
        print("   2. Registrar: Ordem 1 | Pedido 2 (Bolo)")
        print("   3. Executar Ordem 1 → Sistema avança para Ordem 2")
        print("   4. Registrar: Ordem 2 | Pedido 1 (Cookie)")
        print("   5. Executar Ordem 2 com ERRO → Sistema ainda avança para Ordem 3")
        print("   6. Registrar: Ordem 3 | Pedido 1 (Torta) - SEM conflito de IDs")
        print("   * Ordens incrementam SEMPRE, evitando conflitos")
        print()
        print("⚠️ REQUISITOS:")
        print("   • OR-Tools: pip install ortools (para otimização)")
        print("   • Python 3.8+")
        print("   • Arquivos de atividades nos diretórios corretos")
        
        input("\nPressione Enter para continuar...")
    
    def sair(self):
        """Sai do sistema"""
        self.utils.limpar_tela()
        print("👋 SAINDO DO SISTEMA")
        print("=" * 40)
        
        if self.gerenciador.pedidos:
            stats = self.gerenciador.obter_estatisticas()
            print(f"⚠️ Você tem {stats['total']} pedido(s) registrado(s).")
            print(f"📦 Ordem atual: {stats['ordem_atual']} ({stats['pedidos_ordem_atual']} pedidos)")
            if stats['total_ordens'] > 1:
                print(f"📈 Ordens existentes: {stats['ordens_existentes']}")
            
            salvar = input("💾 Deseja salvar pedidos antes de sair? (S/n): ").strip().lower()
            
            if salvar in ['', 's', 'sim', 'y', 'yes']:
                try:
                    self.gerenciador.salvar_pedidos()
                    print("✅ Pedidos salvos com sucesso!")
                except Exception as e:
                    print(f"⌨ Erro ao salvar: {e}")
        
        print("\n🎉 Obrigado por usar o Sistema de Produção!")
        print("🏗️ Nova arquitetura independente (services/gestor_producao)")
        print("🧹 Limpeza automática ativa")
        print("📦 Sistema de Ordens/Sessões implementado")
        print("=" * 40)
        self.rodando = False


def main():
    """Função principal"""
    try:
        menu = MenuPrincipal()
        menu.executar()
    except Exception as e:
        print(f"\n⌨ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n📚 Sistema encerrado.")


if __name__ == "__main__":
    main()