#!/usr/bin/env python3
"""
Script para testar o cálculo de datas individuais para pedidos de reabastecimento.
"""

import sys
from datetime import datetime
from services.gestores.reabastecimento.gerador_csv_reabastecimento import GeradorCSVReabastecimento


def testar_datas_individuais():
    """Testa o cálculo de datas individuais"""

    # Simular itens críticos (baseados nos pedidos existentes)
    itens_criticos = [
        {
            'id': 2010,
            'nome': 'Creme De Queijo',
            'estoque_atual': 0,
            'quantidade_reabastecer': 2990
        },
        {
            'id': 2012,
            'nome': 'Creme De Frango',
            'estoque_atual': 0,
            'quantidade_reabastecer': 19500
        }
    ]

    print("=" * 80)
    print("TESTE DE GERAÇÃO DE CSV COM DATAS INDIVIDUAIS")
    print("=" * 80)

    print(f"\n📋 Itens para teste:")
    for item in itens_criticos:
        print(f"  • [{item['id']}] {item['nome']}: {item['quantidade_reabastecer']:.0f}g")

    # Testar com diferentes buffers
    buffers_teste = [2.0, 3.0, 1.5]

    for buffer_horas in buffers_teste:
        print(f"\n\n{'='*80}")
        print(f"TESTE COM BUFFER DE {buffer_horas:.1f} HORAS")
        print(f"{'='*80}")

        gerador = GeradorCSVReabastecimento()

        try:
            sucesso, caminho, mensagem = gerador.gerar_csv_com_datas_individuais(
                itens_criticos,
                buffer_horas
            )

            print(f"\n{mensagem}")

            if sucesso:
                print(f"\n📁 Arquivo gerado: {caminho}")

                # Ler e exibir conteúdo
                print(f"\n📄 Conteúdo do CSV:")
                print("-" * 80)
                with open(caminho, 'r', encoding='utf-8') as f:
                    print(f.read())
                print("-" * 80)

        except Exception as e:
            print(f"\n❌ Erro: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n\n{'='*80}")
    print("TESTE CONCLUÍDO")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    testar_datas_individuais()
