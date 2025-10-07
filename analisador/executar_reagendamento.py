"""
Script interativo para reagendamento de pedidos com atividades duplicadas.

Fornece interface de linha de comando para seleção de atividades duplicadas
e cálculo de reagendamentos baseados em backward scheduling.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from analisador.analisador_pedidos import AnalisadorPedidos
from analisador.calculador_reagendamento import CalculadorReagendamento


def exibir_menu_atividades(duplicatas):
    """
    Exibe menu numerado das atividades duplicadas para escolha do usuário.

    Args:
        duplicatas (dict): Dicionário de atividades duplicadas

    Returns:
        list: Lista de tuplas (id_atividade, ocorrencias)
    """
    print("\n📋 ATIVIDADES DUPLICADAS DISPONÍVEIS:")
    print("-" * 60)

    atividades_lista = list(duplicatas.items())

    for i, (id_atividade, ocorrencias) in enumerate(atividades_lista, 1):
        primeira_ocorrencia = ocorrencias[0][2]
        print(f"{i:2d}. ID {id_atividade} - {primeira_ocorrencia['atividade']}")
        print(f"     🔧 Equipamento: {primeira_ocorrencia['equipamento']}")
        print(f"     📦 {len(ocorrencias)} pedidos compartilham esta atividade")

    print(f"\n{len(atividades_lista) + 1:2d}. V - Voltar")
    return atividades_lista


def executar_reagendamento_interativo():
    """
    Execução interativa do reagendamento com escolha de atividades.

    Carrega logs, detecta duplicatas e permite ao usuário selecionar
    interativamente quais atividades reagendar.
    """
    print("🔍 REAGENDADOR INTERATIVO DE ATIVIDADES")
    print("=" * 60)

    diretorio_logs = os.path.join(os.path.dirname(__file__), "../logs/equipamentos")
    print(f"📂 Analisando logs em: {diretorio_logs}")

    if not os.path.exists(diretorio_logs):
        print(f"❌ Diretório de logs não encontrado: {diretorio_logs}")
        print("💡 Execute primeiro um script de produção para gerar logs")
        return

    arquivos_log = [f for f in os.listdir(diretorio_logs) if f.endswith('.log')]
    if not arquivos_log:
        print(f"❌ Nenhum arquivo .log encontrado em: {diretorio_logs}")
        print("💡 Execute primeiro um script de produção para gerar logs")
        return

    print(f"📋 Encontrados {len(arquivos_log)} arquivos de log")

    print("\n🔄 Carregando logs...")
    analisador = AnalisadorPedidos(diretorio_logs)
    analisador.carregar_logs()

    if not analisador.pedidos:
        print("❌ Nenhum pedido foi carregado dos logs")
        return

    total_pedidos = len(analisador.pedidos)
    total_atividades = sum(len(atividades) for atividades in analisador.pedidos.values())
    print(f"✅ Carregados {total_pedidos} pedidos com {total_atividades} atividades")

    print("\n🔍 Detectando atividades duplicadas...")
    duplicatas = analisador.detectar_atividades_duplicadas()

    if not duplicatas:
        print("✅ Nenhuma atividade duplicada encontrada!")
        print("💡 Todos os pedidos podem ser executados sem conflitos de equipamentos")
        return

    print(f"⚠️ Encontradas {len(duplicatas)} atividades duplicadas")

    calculador = CalculadorReagendamento(analisador)

    while True:
        try:
            atividades_lista = exibir_menu_atividades(duplicatas)

            escolha = input(f"\n👆 Escolha uma atividade para reagendar (1-{len(atividades_lista)} ou V): ").strip().upper()

            if escolha == 'V':
                print("\n👋 Voltando ao menu principal...")
                break

            try:
                indice = int(escolha) - 1
                if 0 <= indice < len(atividades_lista):
                    id_atividade, ocorrencias = atividades_lista[indice]

                    print(f"\n🔄 Reagendando atividade ID {id_atividade}...")

                    # Criar dicionário com apenas a atividade selecionada
                    duplicata_selecionada = {id_atividade: ocorrencias}

                    # Calcular reagendamento
                    ordem_base, pedido_base, resultados = calculador.calcular_reagendamentos(duplicata_selecionada)

                    if resultados:
                        print(f"\n✅ Reagendamento calculado!")
                        print(f"📌 Pedido base (mantém horários): Ordem {ordem_base}, Pedido {pedido_base}")

                        print(f"\n🔄 Pedidos reagendados:")
                        for (ordem, pedido), dados in resultados.items():
                            horario_final = calculador.formatar_horario(dados['horario_final_jornada'])
                            print(f"   📦 Ordem {ordem}, Pedido {pedido}")
                            print(f"       🕒 Novo término da jornada: {horario_final}")

                        # Exibir cronogramas reagendados detalhados
                        print(f"\n{'='*60}")
                        print("CRONOGRAMAS REAGENDADOS DETALHADOS")
                        print(f"{'='*60}")

                        for (ordem, pedido), dados in resultados.items():
                            calculador.exibir_cronograma_reagendado(ordem, pedido, dados['atividades'])

                        # Mostrar detalhes da atividade reagendada
                        print(f"\n📋 DETALHES DA ATIVIDADE REAGENDADA:")
                        for ordem, pedido, dados in ocorrencias:
                            print(f"   📦 Ordem {ordem}, Pedido {pedido}: {dados['atividade']}")
                            print(f"       ⏰ {dados['inicio']} → {dados['fim']}")
                            print(f"       🔧 Equipamento: {dados['equipamento']}")
                    else:
                        print(f"\n⚠️ Não foi possível calcular reagendamento para esta atividade")

                    input(f"\n⏳ Pressione ENTER para continuar...")
                else:
                    print(f"❌ Opção inválida. Escolha um número entre 1 e {len(atividades_lista)} ou V")

            except ValueError:
                print("❌ Entrada inválida. Digite um número ou V")

        except KeyboardInterrupt:
            print("\n\n❌ Operação cancelada pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro durante o reagendamento: {e}")
            import traceback
            print(f"Detalhes: {traceback.format_exc()}")

def main():
    """
    Ponto de entrada principal do script.

    Executa o reagendador interativo de atividades.
    """
    executar_reagendamento_interativo()


if __name__ == "__main__":
    main()