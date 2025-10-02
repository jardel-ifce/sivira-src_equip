#!/usr/bin/env python3
"""
Script para exibir a agenda completa de todos os funcionários ordenada por objeto.

Executa o método mostrar_agenda_todos_funcionarios() do GestorFuncionarios
e exibe o resultado formatado no console.
"""

import sys
import os

# Adicionar o diretório src_equip ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios


def main():
    """
    Função principal que executa a exibição da agenda de funcionários.
    """
    print("🚀 Iniciando exibição da agenda de funcionários...")
    print()

    try:
        # Criar instância do gestor
        gestor = GestorFuncionarios()

        # Carregar alocações dos logs existentes
        print("📋 Carregando alocações dos logs...")
        if gestor.carregar_alocacoes_dos_logs():
            print("✅ Alocações carregadas com sucesso!")
        else:
            print("⚠️ Nenhuma alocação encontrada nos logs")
        print()

        # Obter e exibir a agenda
        agenda = gestor.mostrar_agenda_todos_funcionarios()
        print(agenda)

    except Exception as e:
        print(f"❌ Erro ao executar o script: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)