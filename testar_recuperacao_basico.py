"""
Teste Básico do Módulo de Recuperação
======================================

Testa a estrutura básica do módulo de recuperação sem aplicar restauração.
"""

from utils.recuperacao import RecuperadorEstado, DetectorLogs


def testar_detector_logs():
    """Testa o detector de logs"""
    print("=" * 70)
    print("TESTE 1: Detector de Logs")
    print("=" * 70)

    detector = DetectorLogs()
    logs = detector.detectar_logs()

    if not logs:
        print("❌ Nenhum log encontrado")
        return False

    print(f"✅ Encontrados {len(logs)} log(s)\n")
    print(detector.gerar_resumo_logs())

    return True


def testar_parsing_sem_restauracao():
    """Testa parsing sem aplicar restauração"""
    print("\n" + "=" * 70)
    print("TESTE 2: Parsing (sem restauração)")
    print("=" * 70)

    detector = DetectorLogs()
    logs = detector.detectar_logs()

    if not logs:
        print("❌ Nenhum log disponível para teste")
        return False

    # Usar log mais recente
    log_mais_recente = logs[0]
    caminho = log_mais_recente['caminho']

    print(f"\n📄 Testando com: {log_mais_recente['nome']}")

    # Criar recuperador
    recuperador = RecuperadorEstado()

    # Executar parsing (sem restauração)
    print("\n🔄 Executando parsing...")
    relatorio = recuperador.recuperar_de_log(caminho, aplicar_restauracao=False)

    # Exibir resultado
    print("\n" + "=" * 70)
    print("RESULTADO DO PARSING")
    print("=" * 70)
    print(relatorio.gerar_resumo())

    return relatorio.sucesso or relatorio.total_ocupacoes_recuperadas > 0


def main():
    """Função principal de testes"""
    print("\n🧪 TESTES BÁSICOS DO MÓDULO DE RECUPERAÇÃO")
    print("=" * 70)
    print("Estes testes validam a estrutura básica do módulo.")
    print("=" * 70)

    testes_sucesso = []

    # Teste 1: Detector
    try:
        resultado = testar_detector_logs()
        testes_sucesso.append(("Detector de Logs", resultado))
    except Exception as e:
        print(f"\n❌ ERRO no teste de detector: {e}")
        testes_sucesso.append(("Detector de Logs", False))

    # Teste 2: Parsing
    try:
        resultado = testar_parsing_sem_restauracao()
        testes_sucesso.append(("Parsing sem Restauração", resultado))
    except Exception as e:
        print(f"\n❌ ERRO no teste de parsing: {e}")
        import traceback
        traceback.print_exc()
        testes_sucesso.append(("Parsing sem Restauração", False))

    # Resumo final
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)

    total = len(testes_sucesso)
    passou = sum(1 for _, sucesso in testes_sucesso if sucesso)

    for nome, sucesso in testes_sucesso:
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{status}: {nome}")

    print("\n" + "=" * 70)
    print(f"Resultado: {passou}/{total} testes passaram")
    print("=" * 70)

    if passou == total:
        print("\n🎉 Todos os testes passaram!")
    else:
        print(f"\n⚠️  {total - passou} teste(s) falharam")


if __name__ == "__main__":
    main()
