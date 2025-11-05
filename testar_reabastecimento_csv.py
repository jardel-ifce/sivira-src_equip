#!/usr/bin/env python3
"""
Script de teste para o sistema de reabastecimento via CSV.

Testa:
1. Detecção de itens críticos
2. Geração de CSV
3. Validação do formato
"""

from datetime import datetime
from services.gestores.almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from services.gestores.reabastecimento.detector_itens_criticos import DetectorItensCriticos
from services.gestores.reabastecimento.gerador_csv_reabastecimento import GeradorCSVReabastecimento


def main():
    print("=" * 80)
    print("TESTE DO SISTEMA DE REABASTECIMENTO VIA CSV")
    print("=" * 80)

    try:
        # Inicializar almoxarifado
        print("\n1️⃣ Inicializando almoxarifado...")
        gestor_almox = GestorAlmoxarifado()
        almoxarifado = gestor_almox.almoxarifado
        print(f"   ✅ {len(almoxarifado.itens)} itens carregados")

        # Detectar itens críticos
        print("\n2️⃣ Detectando itens críticos...")
        detector = DetectorItensCriticos(almoxarifado)
        itens_criticos = detector.detectar_itens_criticos()

        if not itens_criticos:
            print("   ✅ Nenhum item crítico detectado!")
            print("   💡 Todos os SUBPRODUTOS ESTOCADOS estão com estoque adequado")
            return

        print(f"   ⚠️ {len(itens_criticos)} item(ns) crítico(s) encontrado(s):")

        for item in itens_criticos:
            print(f"\n   📦 {item['nome']} (ID: {item['id']})")
            print(f"      Estoque atual: {item['estoque_atual']:.1f} {item['unidade_medida']}")
            print(f"      Estoque mínimo: {item['estoque_minimo']:.1f} {item['unidade_medida']}")
            print(f"      Quantidade a reabastecer: {item['quantidade_reabastecer']:.1f} {item['unidade_medida']}")
            print(f"      Déficit: {item['percentual_deficit']:.1f}%")

        # Resumo
        resumo = detector.obter_resumo_criticos(itens_criticos)
        print(f"\n   📊 RESUMO:")
        print(f"      Total de itens críticos: {resumo['total_itens']}")
        print(f"      Quantidade total a reabastecer: {resumo['quantidade_total_reabastecer']:.0f}")

        # Gerar CSV
        print("\n3️⃣ Gerando CSV de reabastecimento...")
        gerador = GeradorCSVReabastecimento()

        data_sugerida = gerador.obter_data_sugerida()
        print(f"   📅 Data sugerida: {gerador.formatar_data_para_exibicao(data_sugerida)}")

        sucesso, caminho, mensagem = gerador.gerar_csv_reabastecimento(itens_criticos, data_sugerida)

        print(f"\n   {mensagem}")

        if sucesso:
            print(f"\n   📁 Arquivo gerado:")
            print(f"      {caminho}")

            # Ler e mostrar conteúdo
            print(f"\n4️⃣ Conteúdo do CSV:")
            print("   " + "=" * 76)
            with open(caminho, 'r', encoding='utf-8') as f:
                for linha in f:
                    print(f"   {linha.strip()}")
            print("   " + "=" * 76)

            # Listar CSVs gerados
            print(f"\n5️⃣ Histórico de CSVs gerados:")
            arquivos = gerador.listar_csvs_gerados()
            if arquivos:
                for arq in arquivos:
                    print(f"   📄 {arq['nome']}")
                    print(f"      Criado em: {arq['data_criacao'].strftime('%d/%m/%Y %H:%M:%S')}")
                    print(f"      Itens: {arq['total_itens']}")
                    print(f"      Tamanho: {arq['tamanho_bytes']} bytes")
            else:
                print("   (Nenhum arquivo encontrado)")

        print("\n" + "=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
