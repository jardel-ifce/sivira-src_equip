#!/usr/bin/env python3
"""
🏭 ALOCAÇÃO AUTOMÁTICA DE FUNCIONÁRIOS
=====================================

Este script lê os arquivos de requisitos em tipos_funcionarios_requeridos/
e gera automaticamente os logs de alocação de funcionários reais em logs/funcionarios/.

Funcionalidades:
- Lê todos os arquivos de requisitos disponíveis
- Aloca funcionários baseado em compatibilidade de tipos e FIPs
- Gera logs estruturados de alocações
- Relatórios detalhados de ocupação e horas trabalhadas
- Sistema de prioridade por ordem/pedido

Uso:
    python3 examples/alocacao_funcionarios.py
    python3 examples/alocacao_funcionarios.py --ordem 1 --pedido 1
    python3 examples/alocacao_funcionarios.py --relatorio
    python3 examples/alocacao_funcionarios.py --limpar
"""

import argparse
import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios
from utils.logs.gerenciador_logs import apagar_todos_logs_funcionarios


def mostrar_banner():
    """Exibe banner do sistema."""
    print("=" * 80)
    print("🏭 SISTEMA DE ALOCAÇÃO AUTOMÁTICA DE FUNCIONÁRIOS")
    print("=" * 80)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()


def processar_ordem_pedido_especifico(id_ordem: int, id_pedido: int):
    """
    Processa uma ordem e pedido específicos.

    Args:
        id_ordem: ID da ordem
        id_pedido: ID do pedido
    """
    print(f"🎯 Processando Ordem {id_ordem} | Pedido {id_pedido}")
    print("-" * 50)

    gestor = GestorFuncionarios()

    # Tentar alocar
    sucesso = gestor.alocar_funcionarios_para_ordem_pedido(id_ordem, id_pedido)

    if sucesso:
        print("✅ Alocação realizada com SUCESSO!")

        # Mostrar relatório específico
        print("\n📊 Relatório de Alocações:")
        relatorio = gestor.obter_relatorio_alocacoes(id_ordem, id_pedido)
        print(relatorio)

        # Mostrar relatório de horas dos funcionários alocados
        print("\n⏰ Relatório de Horas por Funcionário:")
        funcionarios_alocados = []
        for funcionario in gestor.funcionarios_disponiveis:
            # Verificar se tem ocupações para esta ordem/pedido
            ocupacoes_filtradas = [
                ocup for ocup in funcionario.ocupacoes
                if ocup[0] == id_ordem and ocup[1] == id_pedido
            ]
            if ocupacoes_filtradas:
                funcionarios_alocados.append(funcionario)

        if funcionarios_alocados:
            for funcionario in funcionarios_alocados:
                horas_hoje = funcionario.obter_total_horas_periodo()
                tipos_str = ", ".join([t.name for t in funcionario.tipo_profissional])
                print(f"   👤 {funcionario.nome} ({tipos_str}): {horas_hoje:.2f}h")

    else:
        print("❌ FALHA na alocação - Verificar logs para detalhes")

    print()


def processar_todas_ordens():
    """Processa automaticamente todas as ordens/pedidos disponíveis."""
    print("🚀 Processamento Automático de Todas as Ordens/Pedidos")
    print("-" * 60)

    gestor = GestorFuncionarios()

    # Verificar se há arquivos disponíveis
    diretorio = "logs/tipos_funcionarios_requeridos"
    if not os.path.exists(diretorio):
        print(f"❌ Diretório não encontrado: {diretorio}")
        return

    arquivos = [f for f in os.listdir(diretorio) if f.endswith('.log')]
    if not arquivos:
        print(f"⚠️ Nenhum arquivo de requisitos encontrado em {diretorio}")
        return

    print(f"📁 Encontrados {len(arquivos)} arquivos de requisitos:")
    for arquivo in arquivos:
        print(f"   • {arquivo}")
    print()

    # Processar todos
    resultados = gestor.processar_todas_ordens_pedidos_disponiveis()

    # Mostrar resultados
    print("📊 RESULTADOS DO PROCESSAMENTO:")
    print("-" * 40)

    sucessos = 0
    for (ordem, pedido), sucesso in resultados.items():
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        print(f"   Ordem {ordem} | Pedido {pedido}: {status}")
        if sucesso:
            sucessos += 1

    print()
    print(f"🏁 RESUMO FINAL: {sucessos}/{len(resultados)} alocações bem-sucedidas")

    if sucessos > 0:
        print("\n📊 Relatório Geral de Ocupação:")
        relatorio_geral = gestor.obter_relatorio_alocacoes()
        print(relatorio_geral)


def mostrar_relatorio_completo():
    """Mostra relatório completo das alocações atuais."""
    print("📊 RELATÓRIO COMPLETO DE ALOCAÇÕES")
    print("-" * 50)

    gestor = GestorFuncionarios()

    # Relatório geral
    relatorio = gestor.obter_relatorio_alocacoes()
    print(relatorio)

    # Relatório de horas por funcionário
    print("\n⏰ RELATÓRIO DETALHADO DE HORAS POR FUNCIONÁRIO:")
    print("-" * 60)

    total_horas_sistema = 0
    funcionarios_ativos = 0

    for funcionario in gestor.funcionarios_disponiveis:
        if funcionario.ocupacoes:
            funcionarios_ativos += 1
            horas_funcionario = funcionario.obter_total_horas_periodo()
            total_horas_sistema += horas_funcionario

            tipos_str = ", ".join([t.name for t in funcionario.tipo_profissional])
            setores_str = ", ".join([s.name for s in funcionario.setor])

            print(f"\n👤 {funcionario.nome}")
            print(f"   💼 Tipos: {tipos_str}")
            print(f"   🏢 Setores: {setores_str}")
            print(f"   ⏰ Total de horas: {horas_funcionario:.2f}h")
            print(f"   📋 Atividades: {len(funcionario.ocupacoes)}")

    print(f"\n📈 ESTATÍSTICAS GERAIS:")
    print(f"   👥 Funcionários ativos: {funcionarios_ativos}/{len(gestor.funcionarios_disponiveis)}")
    print(f"   ⏰ Total de horas alocadas: {total_horas_sistema:.2f}h")
    if funcionarios_ativos > 0:
        media_horas = total_horas_sistema / funcionarios_ativos
        print(f"   📊 Média de horas por funcionário: {media_horas:.2f}h")


def limpar_ocupacoes():
    """Limpa todas as ocupações dos funcionários."""
    print("🧹 LIMPEZA DE OCUPAÇÕES")
    print("-" * 30)

    resposta = input("⚠️ Tem certeza que deseja limpar todas as ocupações? (s/N): ")
    if resposta.lower() not in ['s', 'sim', 'y', 'yes']:
        print("❌ Operação cancelada.")
        return

    gestor = GestorFuncionarios()
    gestor._limpar_ocupacoes_funcionarios()

    print("✅ Todas as ocupações foram limpas!")

    # Limpar todos os logs de funcionários usando o gerenciador de logs
    print("\n🧹 Limpando logs de funcionários...")
    apagar_todos_logs_funcionarios()


def mostrar_help():
    """Mostra ajuda detalhada do sistema."""
    print("📚 AJUDA - SISTEMA DE ALOCAÇÃO DE FUNCIONÁRIOS")
    print("=" * 60)
    print()
    print("FLUXO DO SISTEMA:")
    print("1. 📄 Requisitos são gerados em /logs/tipos_funcionarios_requeridos/")
    print("2. 🤖 Este script lê os requisitos e aloca funcionários reais")
    print("3. 📋 Logs de alocação são salvos em /logs/funcionarios/")
    print()
    print("FUNCIONÁRIOS DISPONÍVEIS:")

    gestor = GestorFuncionarios()
    for funcionario in gestor.funcionarios_disponiveis:
        tipos_str = ", ".join([t.name for t in funcionario.tipo_profissional])
        setores_str = ", ".join([s.name for s in funcionario.setor])
        print(f"   👤 {funcionario.nome}: {tipos_str} | {setores_str} | FIP:{funcionario.fip}")

    print()
    print("COMANDOS DISPONÍVEIS:")
    print("   python3 examples/alocacao_funcionarios.py                    # Processa tudo")
    print("   python3 examples/alocacao_funcionarios.py --ordem 1 --pedido 1  # Específico")
    print("   python3 examples/alocacao_funcionarios.py --relatorio        # Ver alocações")
    print("   python3 examples/alocacao_funcionarios.py --limpar           # Limpar tudo")
    print("   python3 examples/alocacao_funcionarios.py --help             # Esta ajuda")


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Sistema de Alocação Automática de Funcionários",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s                          Processa todas as ordens/pedidos
  %(prog)s --ordem 1 --pedido 1     Processa ordem/pedido específico
  %(prog)s --relatorio              Mostra relatório das alocações
  %(prog)s --limpar                 Limpa todas as ocupações
  %(prog)s --help-completo          Ajuda detalhada
        """
    )

    parser.add_argument('--ordem', type=int, help='ID da ordem específica')
    parser.add_argument('--pedido', type=int, help='ID do pedido específico')
    parser.add_argument('--relatorio', action='store_true', help='Mostrar relatório completo')
    parser.add_argument('--limpar', action='store_true', help='Limpar todas as ocupações')
    parser.add_argument('--help-completo', action='store_true', help='Mostrar ajuda detalhada')

    args = parser.parse_args()

    mostrar_banner()

    try:
        if args.help_completo:
            mostrar_help()
        elif args.relatorio:
            mostrar_relatorio_completo()
        elif args.limpar:
            limpar_ocupacoes()
        elif args.ordem and args.pedido:
            processar_ordem_pedido_especifico(args.ordem, args.pedido)
        else:
            processar_todas_ordens()

    except KeyboardInterrupt:
        print("\n⛔ Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80)
    print("🏁 Execução finalizada.")
    print("=" * 80)


if __name__ == "__main__":
    main()