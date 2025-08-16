#!/usr/bin/env python3
"""
Sistema de Menu Principal - Produção - ATUALIZADO
===============================================

Menu interativo para registro e execução de pedidos de produção
com suporte a otimização PL usando TesteSistemaProducao diretamente.

✅ NOVIDADES:
- Limpeza automática de logs na inicialização
- Método de limpeza completa adicional
- Feedback melhorado sobre status de logs
- 🆕 NOVO: Limpeza automática de arquivos de erro na inicialização
"""

import os
import sys
import shutil
from typing import Optional

# Adiciona paths necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu.gerenciador_pedidos import GerenciadorPedidos
from menu.executor_producao import ExecutorProducao
from menu.utils_menu import MenuUtils


class MenuPrincipal:
    """Menu principal do sistema de produção"""
    
    def __init__(self):
        # ✅ MUDANÇA: Limpa pedidos anteriores antes de carregar gerenciador
        print("🚀 Inicializando Sistema de Produção...")
        print("🗑️ Limpando dados de execuções anteriores...")
        
        # 🆕 NOVO: Limpa arquivos de erro antes de qualquer outra coisa
        self._limpar_arquivos_erro_inicializacao()
        
        # Limpa arquivo de pedidos salvos antes de inicializar gerenciador
        self._limpar_pedidos_salvos_inicializacao()
        
        # Inicializa gerenciador (que tentará carregar pedidos, mas arquivo já foi limpo)
        self.gerenciador = GerenciadorPedidos()
        
        # ✅ MUDANÇA: ExecutorProducao agora limpa logs e pedidos automaticamente na inicialização
        self.executor = ExecutorProducao()  # Limpa logs automaticamente aqui
        self.utils = MenuUtils()
        self.rodando = True
    
    def _limpar_arquivos_erro_inicializacao(self):
        """
        🆕 NOVO: Limpa todos os arquivos da pasta /logs/erros na inicialização do menu.
        Garante que cada execução do menu comece sem arquivos de erro anteriores.
        """
        try:
            diretorio_erros = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/erros"
            
            print("🧹 Limpando arquivos de erro anteriores...")
            
            if os.path.exists(diretorio_erros):
                # Lista arquivos antes da limpeza
                arquivos = [f for f in os.listdir(diretorio_erros) if os.path.isfile(os.path.join(diretorio_erros, f))]
                
                if arquivos:
                    print(f"   📄 Encontrados {len(arquivos)} arquivo(s) de erro para remover...")
                    
                    # Remove cada arquivo
                    arquivos_removidos = 0
                    for arquivo in arquivos:
                        try:
                            caminho_arquivo = os.path.join(diretorio_erros, arquivo)
                            os.remove(caminho_arquivo)
                            arquivos_removidos += 1
                        except Exception as e:
                            print(f"   ⚠️ Erro ao remover {arquivo}: {e}")
                    
                    if arquivos_removidos > 0:
                        print(f"   ✅ {arquivos_removidos} arquivo(s) de erro removido(s)")
                    
                    # Verifica se ainda há arquivos
                    arquivos_restantes = [f for f in os.listdir(diretorio_erros) if os.path.isfile(os.path.join(diretorio_erros, f))]
                    if not arquivos_restantes:
                        print(f"   🎉 Diretório {diretorio_erros} limpo completamente")
                    else:
                        print(f"   ⚠️ {len(arquivos_restantes)} arquivo(s) não puderam ser removidos")
                        
                else:
                    print("   🔭 Nenhum arquivo de erro encontrado")
            else:
                print(f"   📁 Diretório {diretorio_erros} não existe")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao limpar arquivos de erro: {e}")
    
    def _limpar_pedidos_salvos_inicializacao(self):
        """
        ✅ NOVO: Limpa arquivo de pedidos salvos na inicialização do menu.
        Garante que cada execução do menu comece sem pedidos anteriores.
        """
        try:
            import json
            arquivo_pedidos = "menu/pedidos_salvos.json"
            
            if os.path.exists(arquivo_pedidos):
                # Lê arquivo para mostrar quantos pedidos serão removidos
                try:
                    with open(arquivo_pedidos, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    
                    total_pedidos = len(dados.get('pedidos', []))
                    if total_pedidos > 0:
                        print(f"   📋 Removendo {total_pedidos} pedido(s) de execuções anteriores...")
                    else:
                        print("   🔭 Arquivo de pedidos vazio, removendo...")
                        
                except (json.JSONDecodeError, KeyError):
                    print(f"   ⚠️ Arquivo de pedidos corrompido, removendo...")
                
                # Remove o arquivo
                os.remove(arquivo_pedidos)
                print(f"   ✅ Pedidos anteriores limpos")
            else:
                print("   🔭 Nenhum pedido anterior encontrado")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao limpar pedidos salvos: {e}")
    
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
                print(f"\n❌ Erro inesperado: {e}")
                input("\nPressione Enter para continuar...")
    
    def mostrar_banner(self):
        """Mostra banner do sistema"""
        print("=" * 80)
        print("🏭 SISTEMA DE PRODUÇÃO - MENU INTERATIVO")
        print("=" * 80)
        print("📋 Registre pedidos e execute com TesteSistemaProducao")
        print("🔧 Suporte a execução sequencial e otimizada (PL)")
        print("✅ Logs e pedidos limpos automaticamente a cada inicialização")
        print("🆕 Arquivos de erro removidos automaticamente na inicialização")
        print("🚫 Menu independente: Não usa pedidos hardcoded do baseline")
        print()
    
    def mostrar_menu_principal(self):
        """Mostra opções do menu principal"""
        print("\n" + "─" * 60)
        print("📋 MENU PRINCIPAL")
        print("─" * 60)
        
        # Status atual
        total_pedidos = len(self.gerenciador.pedidos)
        print(f"📊 Status: {total_pedidos} pedido(s) registrado(s)")
        
        # Debug: verifica duplicatas
        if total_pedidos > 0:
            ids_pedidos = [p.id_pedido for p in self.gerenciador.pedidos]
            ids_unicos = len(set(ids_pedidos))
            if ids_unicos != total_pedidos:
                print(f"⚠️ ATENÇÃO: {total_pedidos - ids_unicos} duplicata(s) detectada(s)")
        
        # ✅ ATUALIZADO: Verifica se há logs (com info de limpeza automática)
        logs_existem = os.path.exists('logs') and os.listdir('logs')
        if logs_existem:
            total_logs = len([f for f in os.listdir('logs') if f.endswith('.log')])
            print(f"📄 Logs atuais: {total_logs} arquivo(s) (logs anteriores foram limpos)")
        else:
            print("🧹 Logs: Ambiente limpo (limpeza automática ativa)")
        
        # 🆕 NOVO: Status de arquivos de erro
        diretorio_erros = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/erros"
        if os.path.exists(diretorio_erros):
            arquivos_erro = [f for f in os.listdir(diretorio_erros) if os.path.isfile(os.path.join(diretorio_erros, f))]
            if arquivos_erro:
                print(f"⚠️ Arquivos de erro: {len(arquivos_erro)} arquivo(s) (serão limpos automaticamente)")
            else:
                print("🧹 Arquivos de erro: Ambiente limpo (limpeza automática ativa)")
        else:
            print("📁 Diretório de erros: Não existe")
        
        # ✅ NOVO: Status de pedidos salvos
        if total_pedidos == 0:
            print("🗑️ Pedidos: Ambiente limpo (pedidos anteriores removidos)")
        
        print()
        
        # Opções do menu
        print("📝 GESTÃO DE PEDIDOS:")
        print("1️⃣  Registrar Novo Pedido")
        print("2️⃣  Listar Pedidos Registrados")
        print("3️⃣  Remover Pedido")
        print("4️⃣  Limpar Todos os Pedidos")
        print()
        print("🚀 EXECUÇÃO:")
        print("5️⃣  Executar Pedidos (SEQUENCIAL)")
        print("6️⃣  Executar Pedidos (OTIMIZADO PL)")
        print()
        print("⚙️ SISTEMA:")
        print("7️⃣  Testar Sistema")
        print("8️⃣  Configurações")
        print("9️⃣  Limpeza Manual de Logs")
        print("🔟  Limpeza Completa de Logs")
        print("1️⃣1️⃣  Limpeza Completa de Pedidos")
        print("1️⃣2️⃣  Limpeza Manual de Arquivos de Erro")  # 🆕 NOVA OPÇÃO
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
            self.limpar_pedidos()
        
        elif opcao == "5":
            self.executar_sequencial()
        
        elif opcao == "6":
            self.executar_otimizado()
        
        elif opcao == "7":
            self.testar_sistema()
        
        elif opcao == "8":
            self.mostrar_configuracoes()
        
        elif opcao == "9":
            self.limpar_logs_manual()
        
        elif opcao == "10":
            self.limpar_logs_completo()
        
        elif opcao == "11":
            self.limpar_pedidos_completo()
        
        elif opcao == "12":
            self.limpar_arquivos_erro_manual()  # 🆕 NOVA FUNCIONALIDADE
        
        elif opcao == "0":
            self.mostrar_ajuda()
        
        elif opcao.lower() in ["sair", "s", "quit", "exit"]:
            self.sair()
        
        else:
            print(f"\n❌ Opção '{opcao}' inválida!")
            input("Pressione Enter para continuar...")
    
    def limpar_arquivos_erro_manual(self):
        """🆕 NOVO: Limpa arquivos de erro manualmente via menu"""
        self.utils.limpar_tela()
        print("🧹 LIMPEZA MANUAL DE ARQUIVOS DE ERRO")
        print("=" * 40)
        print("ℹ️ Nota: Limpeza automática já é executada na inicialização")
        print()
        
        diretorio_erros = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/erros"
        
        # Verifica se diretório existe
        if not os.path.exists(diretorio_erros):
            print(f"📁 Diretório {diretorio_erros} não existe.")
            input("\nPressione Enter para continuar...")
            return
        
        # Verifica se há arquivos de erro
        arquivos_erro = [f for f in os.listdir(diretorio_erros) if os.path.isfile(os.path.join(diretorio_erros, f))]
        
        if not arquivos_erro:
            print("🔭 Nenhum arquivo de erro encontrado para limpar.")
            print("✅ Diretório já está limpo!")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"📄 Encontrados {len(arquivos_erro)} arquivo(s) de erro:")
        
        # Lista os primeiros 10 arquivos
        for i, arquivo in enumerate(arquivos_erro[:10]):
            tamanho = os.path.getsize(os.path.join(diretorio_erros, arquivo))
            print(f"   • {arquivo} ({tamanho} bytes)")
        
        if len(arquivos_erro) > 10:
            print(f"   ... e mais {len(arquivos_erro) - 10} arquivo(s)")
        
        confirmacao = input(f"\n🎯 Confirma limpeza de {len(arquivos_erro)} arquivo(s) de erro? (s/N): ").strip().lower()
        
        if confirmacao in ['s', 'sim', 'y', 'yes']:
            try:
                arquivos_removidos = 0
                arquivos_com_erro = 0
                
                for arquivo in arquivos_erro:
                    try:
                        caminho_arquivo = os.path.join(diretorio_erros, arquivo)
                        os.remove(caminho_arquivo)
                        arquivos_removidos += 1
                    except Exception as e:
                        print(f"   ⚠️ Erro ao remover {arquivo}: {e}")
                        arquivos_com_erro += 1
                
                print(f"\n✅ {arquivos_removidos} arquivo(s) de erro removido(s)")
                if arquivos_com_erro > 0:
                    print(f"⚠️ {arquivos_com_erro} arquivo(s) não puderam ser removidos")
                
            except Exception as e:
                print(f"\n❌ Erro durante limpeza de arquivos de erro: {e}")
        else:
            print("\nℹ️ Limpeza cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def limpar_arquivos_erro_completo(self):
        """🆕 NOVO: Limpeza completa de arquivos de erro com remoção do diretório"""
        try:
            diretorio_erros = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/erros"
            
            print("🧹 LIMPEZA COMPLETA DE ARQUIVOS DE ERRO")
            print("=" * 40)
            
            if os.path.exists(diretorio_erros):
                # Remove todo o diretório e recria vazio
                shutil.rmtree(diretorio_erros)
                os.makedirs(diretorio_erros, exist_ok=True)
                print(f"✅ Diretório {diretorio_erros} completamente limpo e recriado")
            else:
                # Cria o diretório se não existir
                os.makedirs(diretorio_erros, exist_ok=True)
                print(f"📁 Diretório {diretorio_erros} criado")
            
            print("🎉 Limpeza completa de arquivos de erro finalizada!")
            
        except Exception as e:
            print(f"❌ Erro durante limpeza completa de arquivos de erro: {e}")
            import traceback
            traceback.print_exc()
    
    # [Resto dos métodos permanecem inalterados...]
    def registrar_pedido(self):
        """Interface para registrar novo pedido"""
        self.utils.limpar_tela()
        print("📝 REGISTRAR NOVO PEDIDO")
        print("=" * 40)
        
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
                    print(f"\n❌ {mensagem}")
            else:
                print("\nℹ️ Registro cancelado.")
                
        except Exception as e:
            print(f"\n❌ Erro ao registrar pedido: {e}")
        
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
                print("📊 RESUMO:")
                print(f"   Total: {stats['total']} pedidos")
                print(f"   Produtos: {stats['produtos']} | Subprodutos: {stats['subprodutos']}")
                print(f"   Quantidade total: {stats['quantidade_total']} unidades")
                print(f"   Período: {stats['inicio_mais_cedo'].strftime('%d/%m %H:%M')} → {stats['fim_mais_tarde'].strftime('%d/%m %H:%M')}")
        
        input("\nPressione Enter para continuar...")
    
    def remover_pedido(self):
        """Remove um pedido específico"""
        self.utils.limpar_tela()
        print("🗑️ REMOVER PEDIDO")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("🔭 Nenhum pedido para remover.")
            input("\nPressione Enter para continuar...")
            return
        
        # Lista pedidos primeiro
        self.gerenciador.listar_pedidos()
        
        try:
            pedido_id = input("\n🎯 Digite o ID do pedido para remover (ou Enter para cancelar): ").strip()
            
            if pedido_id:
                pedido_id = int(pedido_id)
                sucesso, mensagem = self.gerenciador.remover_pedido(pedido_id)
                print(f"\n{'✅' if sucesso else '❌'} {mensagem}")
                
                if sucesso:
                    # Auto-salva após remoção
                    self.gerenciador.salvar_pedidos()
            else:
                print("\nℹ️ Remoção cancelada.")
                
        except ValueError:
            print("\n❌ ID inválido!")
        except Exception as e:
            print(f"\n❌ Erro ao remover pedido: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def limpar_pedidos(self):
        """Remove todos os pedidos"""
        self.utils.limpar_tela()
        print("🗑️ LIMPAR TODOS OS PEDIDOS")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("🔭 Nenhum pedido para limpar.")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"⚠️ Isso removerá TODOS os {len(self.gerenciador.pedidos)} pedidos registrados!")
        confirmacao = input("Digite 'CONFIRMAR' para prosseguir: ").strip()
        
        if confirmacao == "CONFIRMAR":
            self.gerenciador.limpar_pedidos()
            self.gerenciador.salvar_pedidos()  # Salva estado vazio
            print("\n✅ Todos os pedidos foram removidos.")
        else:
            print("\nℹ️ Operação cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def executar_sequencial(self):
        """Executa pedidos em modo sequencial"""
        self.utils.limpar_tela()
        print("📄 EXECUÇÃO SEQUENCIAL")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("🔭 Nenhum pedido registrado para executar.")
            print("\n💡 MENU INDEPENDENTE: Este menu funciona apenas com pedidos que você registrar")
            print("💡 Use a opção '1' para registrar pedidos primeiro")
            print("🚫 MENU: Não usa pedidos hardcoded do script baseline")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"📊 {len(self.gerenciador.pedidos)} pedido(s) será(ão) executado(s) em ordem sequencial.")
        print("⏱️ Isso pode levar alguns minutos...")
        print("\n🔧 Método: TesteSistemaProducao SEQUENCIAL (producao_paes_backup.py)")
        print("📋 SEQUENCIAL: Fluxo = Almoxarifado → Pedidos → Ordenação → Execução")
        print("🧹 Logs foram limpos automaticamente para esta execução")
        print("📋 MENU: Usando APENAS pedidos registrados pelo usuário")
        
        # Mostra resumo dos pedidos
        for pedido in self.gerenciador.pedidos:
            print(f"   • {pedido.nome_item} ({pedido.quantidade} uni) - Prazo: {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
        
        confirmacao = input("\n🎯 Confirma execução? (s/N): ").strip().lower()
        
        if confirmacao in ['s', 'sim', 'y', 'yes']:
            try:
                sucesso = self.executor.executar_sequencial(self.gerenciador.pedidos)
                if sucesso:
                    print("\n🎉 Execução sequencial concluída!")
                else:
                    print("\n❌ Falha na execução sequencial!")
            except Exception as e:
                print(f"\n❌ Erro durante execução: {e}")
        else:
            print("\nℹ️ Execução cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def executar_otimizado(self):
        """Executa pedidos com otimização PL"""
        self.utils.limpar_tela()
        print("🚀 EXECUÇÃO OTIMIZADA (PL)")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("🔭 Nenhum pedido registrado para executar.")
            print("\n💡 MENU INDEPENDENTE: Este menu funciona apenas com pedidos que você registrar")
            print("💡 Use a opção '1' para registrar pedidos primeiro")
            print("🚫 MENU: Não usa pedidos hardcoded do script baseline")
            input("\nPressione Enter para continuar...")
            return
        
        # Verifica OR-Tools primeiro
        ortools_ok, ortools_msg = self.utils.validar_or_tools()
        print(f"🔧 OR-Tools: {'✅' if ortools_ok else '❌'} {ortools_msg}")
        
        if not ortools_ok:
            print("\n💡 Para instalar: pip install ortools")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"\n📊 {len(self.gerenciador.pedidos)} pedido(s) será(ão) otimizado(s) com Programação Linear.")
        print("⏱️ Isso pode levar alguns minutos para encontrar a solução ótima...")
        print("\n🔧 Método: TesteSistemaProducao OTIMIZADO (producao_paes.py)")
        print("📋 OTIMIZADO: Usa Programação Linear para encontrar solução ótima")
        print("🧹 Logs foram limpos automaticamente para esta execução")
        print("📋 MENU: Usando APENAS pedidos registrados pelo usuário")
        
        # Configurações de otimização
        config = self.executor.obter_configuracoes()
        print(f"\n⚙️ Configurações de Otimização:")
        print(f"   Resolução temporal: {config['resolucao_minutos']} minutos")
        print(f"   Timeout: {config['timeout_pl']} segundos")
        
        # Mostra resumo dos pedidos
        print(f"\n📋 Pedidos para otimização:")
        for pedido in self.gerenciador.pedidos:
            print(f"   • {pedido.nome_item} ({pedido.quantidade} uni) - Prazo: {pedido.fim_jornada.strftime('%d/%m %H:%M')}")
        
        confirmacao = input("\n🎯 Confirma execução otimizada? (s/N): ").strip().lower()
        
        if confirmacao in ['s', 'sim', 'y', 'yes']:
            try:
                sucesso = self.executor.executar_otimizado(self.gerenciador.pedidos)
                if sucesso:
                    print("\n🎉 Execução otimizada concluída!")
                else:
                    print("\n❌ Falha na execução otimizada!")
            except Exception as e:
                print(f"\n❌ Erro durante execução otimizada: {e}")
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
            resultados = self.executor.testar_sistema()
            
            # Resumo final
            print(f"\n🎯 DIAGNÓSTICO CONCLUÍDO")
            
            testes_ok = sum(1 for r in resultados.values() if isinstance(r, dict) and r.get('ok', False))
            total_testes = sum(1 for r in resultados.values() if isinstance(r, dict) and 'ok' in r)
            
            if testes_ok == total_testes:
                print("✅ Sistema pronto para execução!")
            else:
                print(f"⚠️ {total_testes - testes_ok} problema(s) encontrado(s)")
            
        except Exception as e:
            print(f"❌ Erro durante teste: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def mostrar_configuracoes(self):
        """Mostra configurações do sistema"""
        self.utils.limpar_tela()
        print("⚙️ CONFIGURAÇÕES DO SISTEMA")
        print("=" * 40)
        
        config = self.executor.obter_configuracoes()
        info_sistema = self.utils.obter_info_sistema()
        
        print(f"🐍 Python: {info_sistema['python_version']}")
        print(f"💻 Sistema: {info_sistema['platform']} {info_sistema['platform_version']}")
        print()
        print(f"📂 Diretórios:")
        print(f"   Produtos: {self.gerenciador.dir_produtos}")
        print(f"   Subprodutos: {self.gerenciador.dir_subprodutos}")
        print()
        print(f"⚙️ Otimização PL:")
        print(f"   Resolução temporal: {config['resolucao_minutos']} minutos")
        print(f"   Timeout: {config['timeout_pl']} segundos")
        print()
        print(f"🧹 Sistema de Limpeza:")
        print(f"   Limpeza automática: ✅ Ativa (na inicialização)")
        print(f"   Limpeza manual: ✅ Disponível (opção 9)")
        print(f"   Limpeza completa: ✅ Disponível (opção 10)")
        print(f"   Limpeza arquivos erro: ✅ Automática + Manual (opção 12)")
        print()
        print(f"📋 Status:")
        print(f"   OR-Tools: {'✅ Disponível' if config['ortools_disponivel'] else '❌ Não encontrado'}")
        print(f"   Total de pedidos: {len(self.gerenciador.pedidos)}")
        
        # Opções de configuração
        print(f"\n🔧 ALTERAR CONFIGURAÇÕES:")
        print("1 - Alterar resolução temporal PL")
        print("2 - Alterar timeout PL")
        print("0 - Voltar")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            try:
                nova_resolucao = int(input("Nova resolução em minutos (30 recomendado): "))
                if nova_resolucao > 0:
                    self.executor.configurar(resolucao_minutos=nova_resolucao)
                else:
                    print("❌ Valor deve ser positivo!")
            except ValueError:
                print("❌ Valor inválido!")
        
        elif opcao == "2":
            try:
                novo_timeout = int(input("Novo timeout em segundos (300 recomendado): "))
                if novo_timeout > 0:
                    self.executor.configurar(timeout_pl=novo_timeout)
                else:
                    print("❌ Valor deve ser positivo!")
            except ValueError:
                print("❌ Valor inválido!")
        
        input("\nPressione Enter para continuar...")
    
    def limpar_logs_manual(self):
        """✅ RENOMEADO: Limpa logs manualmente via menu"""
        self.utils.limpar_tela()
        print("🧹 LIMPEZA MANUAL DE LOGS")
        print("=" * 40)
        print("ℹ️ Nota: Limpeza automática já é executada na inicialização")
        print()
        
        # Verifica se há logs
        logs_existem = os.path.exists('logs') and os.listdir('logs')
        
        if not logs_existem:
            print("🔭 Nenhum log encontrado para limpar.")
            print("✅ Sistema já está limpo!")
            input("\nPressione Enter para continuar...")
            return
        
        total_logs = len([f for f in os.listdir('logs') if f.endswith('.log')])
        print(f"📄 Encontrados {total_logs} arquivo(s) de log")
        
        confirmacao = input("\n🎯 Confirma limpeza manual de logs? (s/N): ").strip().lower()
        
        if confirmacao in ['s', 'sim', 'y', 'yes']:
            try:
                self.executor.limpar_logs_anteriores()
                print("\n✅ Logs limpos manualmente com sucesso!")
            except Exception as e:
                print(f"\n❌ Erro ao limpar logs: {e}")
        else:
            print("\nℹ️ Limpeza cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def limpar_logs_completo(self):
        """✅ NOVO: Limpeza completa e detalhada de todos os logs"""
        self.utils.limpar_tela()
        print("🧹 LIMPEZA COMPLETA DE LOGS")
        print("=" * 40)
        print("⚠️ Esta opção remove TODOS os arquivos de log, comandas e temporários")
        print("📂 Inclui limpeza de diretórios: logs/, comandas/, temp/")
        print()
        
        confirmacao = input("🎯 Confirma limpeza COMPLETA? Digite 'LIMPAR' para confirmar: ").strip()
        
        if confirmacao == "LIMPAR":
            try:
                self.executor.limpar_logs_completo()
                print("\n🎉 Limpeza completa finalizada com sucesso!")
            except Exception as e:
                print(f"\n❌ Erro durante limpeza completa: {e}")
        else:
            print("\nℹ️ Limpeza completa cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def limpar_pedidos_completo(self):
        """✅ NOVO: Limpeza completa de pedidos salvos"""
        self.utils.limpar_tela()
        print("🗑️ LIMPEZA COMPLETA DE PEDIDOS")
        print("=" * 40)
        print("⚠️ Esta opção remove TODOS os pedidos salvos em arquivos")
        print("📂 Remove: menu/pedidos_salvos.json e arquivos relacionados")
        print("💾 Pedidos em memória também serão limpos")
        print()
        
        # Mostra pedidos atuais se houver
        if self.gerenciador.pedidos:
            print(f"📋 Pedidos atuais em memória: {len(self.gerenciador.pedidos)}")
        else:
            print("🔭 Nenhum pedido em memória atualmente")
        
        confirmacao = input("\n🎯 Confirma limpeza COMPLETA de pedidos? Digite 'LIMPAR' para confirmar: ").strip()
        
        if confirmacao == "LIMPAR":
            try:
                # Limpa pedidos em memória
                if self.gerenciador.pedidos:
                    total_memoria = len(self.gerenciador.pedidos)
                    self.gerenciador.limpar_pedidos()
                    print(f"✅ {total_memoria} pedido(s) removido(s) da memória")
                
                # Limpa arquivos salvos
                self.executor.limpar_pedidos_completo()
                
                print("\n🎉 Limpeza completa de pedidos finalizada!")
                
            except Exception as e:
                print(f"\n❌ Erro durante limpeza completa de pedidos: {e}")
        else:
            print("\nℹ️ Limpeza completa de pedidos cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def mostrar_ajuda(self):
        """Mostra ajuda do sistema"""
        self.utils.limpar_tela()
        print("❓ AJUDA DO SISTEMA")
        print("=" * 40)
        
        print("📋 COMO USAR:")
        print()
        print("1️⃣ REGISTRAR PEDIDOS:")
        print("   • Digite o ID do item (ex: 1001)")
        print("   • Escolha PRODUTO ou SUBPRODUTO")
        print("   • Informe a quantidade")
        print("   • Digite fim da jornada (ex: 07:00:00 11/08/2025)")
        print("   • O início será calculado automaticamente (3 dias antes)")
        print()
        print("2️⃣ EXECUÇÃO SEQUENCIAL:")
        print("   • Usa TesteSistemaProducao(usar_otimizacao=False)")
        print("   • Executa pedidos em ordem de registro")
        print("   • Mais rápido, mas pode não ser ótimo")
        print("   • Fluxo: Almoxarifado → Pedidos → Ordenação → Execução")
        print()
        print("3️⃣ EXECUÇÃO OTIMIZADA:")
        print("   • Usa TesteSistemaProducao(usar_otimizacao=True)")
        print("   • Usa Programação Linear para otimizar")
        print("   • Maximiza pedidos atendidos")
        print("   • Minimiza conflitos de equipamentos")
        print("   • Requer OR-Tools instalado")
        print()
        print("🧹 SISTEMA DE LIMPEZA:")
        print("   • Limpeza automática: Executada na inicialização")
        print("   • Logs limpos automaticamente a cada início")
        print("   • Pedidos anteriores removidos automaticamente")
        print("   • Arquivos de erro removidos automaticamente")
        print("   • Limpeza manual: Remove logs atuais (opção 9)")
        print("   • Limpeza completa logs: Remove todos os arquivos (opção 10)")
        print("   • Limpeza completa pedidos: Remove arquivos salvos (opção 11)")
        print("   • Limpeza manual erros: Remove arquivos de erro (opção 12)")
        print()
        print("📂 ESTRUTURA DE ARQUIVOS:")
        print("   • Produtos: /data/produtos/atividades/ID_nome.json")
        print("   • Subprodutos: /data/subprodutos/atividades/ID_nome.json")
        print("   • Logs: /logs/execucao_pedidos_TIMESTAMP.log")
        print("   • Erros: /logs/erros/ (limpos automaticamente)")
        print()
        print("⚠️ REQUISITOS:")
        print("   • OR-Tools: pip install ortools")
        print("   • Almoxarifado inicializado")
        print("   • Funcionários disponíveis")
        print("   • TesteSistemaProducao acessível")
        print()
        print("🔧 DIFERENÇAS DOS MODOS:")
        print("   • Sequencial: como producao_paes_backup.py (ordem fixa)")
        print("   • Otimizado: como producao_paes.py (Programação Linear)")
        print("   • Ambos: limpam logs automaticamente")
        print("   • Ambos: usam apenas pedidos do menu")
        print("   • Ambos: removem arquivos de erro automaticamente")
        
        input("\nPressione Enter para continuar...")
    
    def sair(self):
        """Sai do sistema"""
        self.utils.limpar_tela()
        print("👋 SAINDO DO SISTEMA")
        print("=" * 40)
        
        if self.gerenciador.pedidos:
            print(f"⚠️ Você tem {len(self.gerenciador.pedidos)} pedido(s) registrado(s).")
            salvar = input("💾 Deseja salvar pedidos antes de sair? (S/n): ").strip().lower()
            
            if salvar in ['', 's', 'sim', 'y', 'yes']:
                try:
                    self.gerenciador.salvar_pedidos()
                    print("✅ Pedidos salvos com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao salvar: {e}")
        
        print("\n🎉 Obrigado por usar o Sistema de Produção!")
        print("🔧 Baseado em TesteSistemaProducao")
        print("🧹 Logs serão limpos automaticamente na próxima inicialização")
        print("🗑️ Arquivos de erro serão removidos automaticamente na próxima inicialização")
        print("=" * 40)
        self.rodando = False


def main():
    """Função principal"""
    try:
        menu = MenuPrincipal()
        menu.executar()
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n📚 Sistema encerrado.")


if __name__ == "__main__":
    main()