#!/usr/bin/env python3
"""
Sistema de Menu Principal - Produção
===================================

Menu interativo para registro e execução de pedidos de produção
com suporte a otimização PL usando TesteSistemaProducao diretamente.
"""

import os
import sys
from typing import Optional

# Adiciona paths necessários
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from menu.gerenciador_pedidos import GerenciadorPedidos
from menu.executor_producao import ExecutorProducao
from menu.utils_menu import MenuUtils


class MenuPrincipal:
    """Menu principal do sistema de produção"""
    
    def __init__(self):
        self.gerenciador = GerenciadorPedidos()
        self.executor = ExecutorProducao()
        self.utils = MenuUtils()
        self.rodando = True
    
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
        
        # Verifica se há logs anteriores
        if os.path.exists('logs') and os.listdir('logs'):
            total_logs = len([f for f in os.listdir('logs') if f.endswith('.log')])
            print(f"📄 Logs anteriores: {total_logs} arquivo(s)")
        
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
        print("9️⃣  Limpar Logs Anteriores")
        print("0️⃣  Ajuda")
        print("❌  Sair")
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
            self.limpar_logs()
        
        elif opcao == "0":
            self.mostrar_ajuda()
        
        elif opcao.lower() in ["sair", "s", "quit", "exit"]:
            self.sair()
        
        else:
            print(f"\n❌ Opção '{opcao}' inválida!")
            input("Pressione Enter para continuar...")
    
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
                print("\n⏹️ Registro cancelado.")
                
        except Exception as e:
            print(f"\n❌ Erro ao registrar pedido: {e}")
        
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
            print("📭 Nenhum pedido para remover.")
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
                print("\n⏹️ Remoção cancelada.")
                
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
            print("📭 Nenhum pedido para limpar.")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"⚠️ Isso removerá TODOS os {len(self.gerenciador.pedidos)} pedidos registrados!")
        confirmacao = input("Digite 'CONFIRMAR' para prosseguir: ").strip()
        
        if confirmacao == "CONFIRMAR":
            self.gerenciador.limpar_pedidos()
            self.gerenciador.salvar_pedidos()  # Salva estado vazio
            print("\n✅ Todos os pedidos foram removidos.")
        else:
            print("\n⏹️ Operação cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def executar_sequencial(self):
        """Executa pedidos em modo sequencial"""
        self.utils.limpar_tela()
        print("🔄 EXECUÇÃO SEQUENCIAL")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("📭 Nenhum pedido para executar.")
            print("\n💡 Use a opção '1' para registrar pedidos primeiro")
            input("\nPressione Enter para continuar...")
            return
        
        print(f"📊 {len(self.gerenciador.pedidos)} pedido(s) será(ão) executado(s) em ordem sequencial.")
        print("⏱️ Isso pode levar alguns minutos...")
        print("\n🔧 Método: TesteSistemaProducao (usar_otimizacao=False)")
        
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
            print("\n⏹️ Execução cancelada.")
        
        input("\nPressione Enter para continuar...")
    
    def executar_otimizado(self):
        """Executa pedidos com otimização PL"""
        self.utils.limpar_tela()
        print("🚀 EXECUÇÃO OTIMIZADA (PL)")
        print("=" * 40)
        
        if not self.gerenciador.pedidos:
            print("📭 Nenhum pedido para executar.")
            print("\n💡 Use a opção '1' para registrar pedidos primeiro")
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
        print("\n🔧 Método: TesteSistemaProducao (usar_otimizacao=True)")
        
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
            print("\n⏹️ Execução cancelada.")
        
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
        print(f"📁 Diretórios:")
        print(f"   Produtos: {self.gerenciador.dir_produtos}")
        print(f"   Subprodutos: {self.gerenciador.dir_subprodutos}")
        print()
        print(f"⚙️ Otimização PL:")
        print(f"   Resolução temporal: {config['resolucao_minutos']} minutos")
        print(f"   Timeout: {config['timeout_pl']} segundos")
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
    
    def limpar_logs(self):
        """Limpa logs anteriores"""
        self.utils.limpar_tela()
        print("🧹 LIMPAR LOGS ANTERIORES")
        print("=" * 40)
        
        # Verifica se há logs
        logs_existem = os.path.exists('logs') and os.listdir('logs')
        
        if not logs_existem:
            print("📭 Nenhum log encontrado para limpar.")
            input("\nPressione Enter para continuar...")
            return
        
        total_logs = len([f for f in os.listdir('logs') if f.endswith('.log')])
        print(f"📄 Encontrados {total_logs} arquivo(s) de log")
        
        confirmacao = input("\n🎯 Confirma limpeza de logs? (s/N): ").strip().lower()
        
        if confirmacao in ['s', 'sim', 'y', 'yes']:
            try:
                self.executor.limpar_logs_anteriores()
                print("\n✅ Logs limpos com sucesso!")
            except Exception as e:
                print(f"\n❌ Erro ao limpar logs: {e}")
        else:
            print("\n⏹️ Limpeza cancelada.")
        
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
        print("📁 ESTRUTURA DE ARQUIVOS:")
        print("   • Produtos: /data/produtos/atividades/ID_nome.json")
        print("   • Subprodutos: /data/subprodutos/atividades/ID_nome.json")
        print("   • Logs: /logs/execucao_pedidos_TIMESTAMP.log")
        print()
        print("⚠️ REQUISITOS:")
        print("   • OR-Tools: pip install ortools")
        print("   • Almoxarifado inicializado")
        print("   • Funcionários disponíveis")
        print("   • TesteSistemaProducao acessível")
        print()
        print("🔧 DIFERENÇAS DOS MODOS:")
        print("   • Sequencial: como producao_paes_backup.py")
        print("   • Otimizado: como producao_paes.py atual")
        
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
        print("\n🔚 Sistema encerrado.")


if __name__ == "__main__":
    main()