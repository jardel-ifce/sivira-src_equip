#!/usr/bin/env python3
"""
Script para calcular a duração total dos pedidos salvos usando calculadora_duracao.
"""

import json
from datetime import timedelta
from utils.producao.calculadora_duracao import consultar_duracao_por_faixas


def carregar_json(caminho: str) -> dict:
    """Carrega um arquivo JSON."""
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


def formatar_duracao(duracao: timedelta) -> str:
    """Formata timedelta para HH:MM:SS."""
    total_segundos = int(duracao.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def calcular_duracao_pedido(pedido: dict) -> dict:
    """
    Calcula a duração total de um pedido somando todas as suas atividades.

    Args:
        pedido: Dicionário com dados do pedido

    Returns:
        Dicionário com informações do pedido e duração calculada
    """
    try:
        # Carregar arquivo de atividades do pedido
        dados_item = carregar_json(pedido['arquivo_atividades'])
        quantidade = pedido['quantidade']

        print(f"\n{'='*80}")
        print(f"PEDIDO #{pedido['id_pedido']} - {pedido['nome_item']}")
        print(f"{'='*80}")
        print(f"Quantidade: {quantidade:,} gramas")
        print(f"ID Item: {pedido['id_item']}")
        print(f"Tipo: {pedido['tipo_item']}")
        print(f"Início da Jornada: {pedido['inicio_jornada']}")
        print(f"Fim da Jornada: {pedido['fim_jornada']}")
        print(f"\n{'─'*80}")
        print("ATIVIDADES:")
        print(f"{'─'*80}")

        duracao_total = timedelta()
        detalhes_atividades = []

        # Calcular duração de cada atividade
        for atividade in dados_item.get('atividades', []):
            try:
                duracao_atividade = consultar_duracao_por_faixas(atividade, quantidade)
                duracao_total += duracao_atividade

                # Informações sobre tipos de equipamento
                tipo_equipamento = atividade.get('tipo_equipamento', {})
                num_tipos = len(tipo_equipamento) if isinstance(tipo_equipamento, dict) else 1
                multiplicador_info = f" (x{num_tipos} tipos de equipamento)" if num_tipos > 1 else ""

                detalhe = {
                    'id_atividade': atividade['id_atividade'],
                    'nome': atividade['nome'],
                    'tipo': atividade['tipo_atividade'],
                    'duracao': formatar_duracao(duracao_atividade),
                    'duracao_segundos': int(duracao_atividade.total_seconds()),
                    'tipos_equipamento': tipo_equipamento
                }
                detalhes_atividades.append(detalhe)

                print(f"\n  [{atividade['id_atividade']}] {atividade['nome']}")
                print(f"  └─ Tipo: {atividade['tipo_atividade']}")
                print(f"  └─ Equipamentos: {', '.join(tipo_equipamento.keys())}{multiplicador_info}")
                print(f"  └─ Duração: {formatar_duracao(duracao_atividade)}")

            except ValueError as e:
                print(f"\n  ⚠️  ERRO na atividade {atividade.get('id_atividade', '?')}: {e}")
                continue

        print(f"\n{'─'*80}")
        print(f"DURAÇÃO TOTAL: {formatar_duracao(duracao_total)}")
        print(f"{'='*80}")

        return {
            'id_pedido': pedido['id_pedido'],
            'id_ordem': pedido['id_ordem'],
            'nome_item': pedido['nome_item'],
            'id_item': pedido['id_item'],
            'tipo_item': pedido['tipo_item'],
            'quantidade': quantidade,
            'inicio_jornada': pedido['inicio_jornada'],
            'fim_jornada': pedido['fim_jornada'],
            'duracao_total': formatar_duracao(duracao_total),
            'duracao_total_segundos': int(duracao_total.total_seconds()),
            'duracao_total_horas': round(duracao_total.total_seconds() / 3600, 2),
            'atividades': detalhes_atividades,
            'numero_atividades': len(detalhes_atividades),
            'sucesso': True
        }

    except Exception as e:
        print(f"\n❌ ERRO ao processar pedido {pedido.get('id_pedido', '?')}: {e}")
        return {
            'id_pedido': pedido.get('id_pedido'),
            'nome_item': pedido.get('nome_item'),
            'erro': str(e),
            'sucesso': False
        }


def main():
    """Função principal."""
    caminho_pedidos = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/pedidos/pedidos_salvos.json"

    print("\n" + "="*80)
    print("CÁLCULO DE DURAÇÃO DE PEDIDOS")
    print("="*80)
    print(f"\nArquivo: {caminho_pedidos}")

    try:
        # Carregar pedidos
        dados_pedidos = carregar_json(caminho_pedidos)
        pedidos = dados_pedidos.get('pedidos', [])

        print(f"\nTotal de pedidos encontrados: {len(pedidos)}")

        if not pedidos:
            print("\n⚠️  Nenhum pedido encontrado no arquivo.")
            return

        # Processar cada pedido
        resultados = []
        for pedido in pedidos:
            resultado = calcular_duracao_pedido(pedido)
            resultados.append(resultado)

        # Resumo final
        print(f"\n\n{'='*80}")
        print("RESUMO GERAL")
        print(f"{'='*80}\n")

        duracao_total_geral = timedelta()
        pedidos_sucesso = 0
        pedidos_erro = 0

        for resultado in resultados:
            if resultado['sucesso']:
                pedidos_sucesso += 1
                duracao_total_geral += timedelta(seconds=resultado['duracao_total_segundos'])
                print(f"  Pedido #{resultado['id_pedido']:02d} - {resultado['nome_item']:<30} | "
                      f"Duração: {resultado['duracao_total']:>8} | "
                      f"Atividades: {resultado['numero_atividades']}")
            else:
                pedidos_erro += 1
                print(f"  Pedido #{resultado['id_pedido']:02d} - {resultado['nome_item']:<30} | ❌ ERRO")

        print(f"\n{'─'*80}")
        print(f"Total de pedidos processados: {len(resultados)}")
        print(f"  ✓ Sucesso: {pedidos_sucesso}")
        print(f"  ✗ Erros: {pedidos_erro}")
        print(f"\nDuração total somada: {formatar_duracao(duracao_total_geral)}")
        print(f"Duração total em horas: {duracao_total_geral.total_seconds() / 3600:.2f}h")
        print(f"{'='*80}\n")

        # Salvar resultados em JSON
        caminho_saida = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/pedidos/duracoes_calculadas.json"
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            json.dump({
                'resultados': resultados,
                'resumo': {
                    'total_pedidos': len(resultados),
                    'pedidos_sucesso': pedidos_sucesso,
                    'pedidos_erro': pedidos_erro,
                    'duracao_total_geral': formatar_duracao(duracao_total_geral),
                    'duracao_total_segundos': int(duracao_total_geral.total_seconds()),
                    'duracao_total_horas': round(duracao_total_geral.total_seconds() / 3600, 2)
                },
                'arquivo_origem': caminho_pedidos,
                'calculado_em': dados_pedidos.get('salvo_em', 'N/A')
            }, f, indent=2, ensure_ascii=False)

        print(f"✓ Resultados salvos em: {caminho_saida}\n")

    except FileNotFoundError:
        print(f"\n❌ Arquivo não encontrado: {caminho_pedidos}")
    except json.JSONDecodeError:
        print(f"\n❌ Erro ao decodificar JSON do arquivo: {caminho_pedidos}")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


if __name__ == "__main__":
    main()