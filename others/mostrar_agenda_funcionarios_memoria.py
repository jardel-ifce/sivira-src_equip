#!/usr/bin/env python3
"""
Script para exibir a agenda de funcionários baseada nas ocupações em memória.

Diferente do mostrar_agenda_funcionarios.py, este script NÃO recarrega dos logs.
Ele mostra exatamente o que está no atributo 'ocupacoes' dos funcionários em memória.
"""

import sys
import os

# Adicionar o diretório src_equip ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios


def main():
    """
    Função principal que executa a exibição da agenda de funcionários em memória.
    """
    print("🚀 Exibindo agenda de funcionários (MEMÓRIA - sem recarregar logs)...")
    print()

    try:
        # Criar instância do gestor (singleton - mantém dados em memória)
        gestor = GestorFuncionarios()

        # Verificar quantas ocupações existem em memória
        total_ocupacoes_memoria = sum(len(f.ocupacoes) for f in gestor.funcionarios_disponiveis)

        print(f"📊 Total de ocupações em memória: {total_ocupacoes_memoria}")
        print()

        if total_ocupacoes_memoria == 0:
            print("⚠️ Nenhuma ocupação encontrada em memória.")
            print("💡 Dica: Execute a alocação de funcionários primeiro ou use mostrar_agenda_funcionarios.py para carregar dos logs.")
            print()

        # Obter e exibir a agenda (baseada no atributo ocupacoes em memória)
        agenda = gestor.mostrar_agenda_todos_funcionarios()
        print(agenda)

    except Exception as e:
        print(f"❌ Erro ao executar o script: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
