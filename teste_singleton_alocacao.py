#!/usr/bin/env python3
"""
Teste de Singleton para Alocação de Funcionários
=================================================

Simula o comportamento do menu principal ao alocar funcionários
múltiplas vezes para o mesmo pedido.

Testa se:
1. O singleton mantém as ocupações entre chamadas
2. Alocações conflitantes são bloqueadas
3. O mesmo comportamento ocorre via scripts externos
"""

from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios
from datetime import datetime

def teste_alocacao_multipla():
    """Simula alocação múltipla do mesmo pedido via menu"""

    print("=" * 70)
    print("🧪 TESTE: ALOCAÇÃO MÚLTIPLA DO MESMO PEDIDO (SINGLETON)")
    print("=" * 70)
    print()

    # =========================================================================
    # CENÁRIO 1: Primeira execução (simula usuário escolhendo opção F > 1)
    # =========================================================================
    print("📋 CENÁRIO 1: Primeira alocação (usuário executa via menu)")
    print("-" * 70)

    gestor1 = GestorFuncionarios()
    print(f"✅ GestorFuncionarios instanciado - ID: {id(gestor1)}")

    # Limpar ocupações para simular início limpo
    for func in gestor1.funcionarios_disponiveis:
        func.ocupacoes.clear()

    func1 = gestor1.funcionarios_disponiveis[0]  # Funcionário 1
    func3 = gestor1.funcionarios_disponiveis[2]  # Funcionário 3

    print(f"👤 {func1.nome} - Ocupações iniciais: {len(func1.ocupacoes)}")
    print(f"👤 {func3.nome} - Ocupações iniciais: {len(func3.ocupacoes)}")
    print()

    # Simular alocação manual (o que o gestor faria)
    inicio = datetime(2025, 10, 11, 2, 1)
    fim = datetime(2025, 10, 11, 2, 12)

    print(f"📝 Alocando Ordem 1 | Pedido 1 - Atividade 20011")
    print(f"   Período: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}")

    func1.registrar_ocupacao(1, 1, 20011, "mistura_de_massas_crocantes", inicio, fim)
    func3.registrar_ocupacao(1, 1, 20011, "mistura_de_massas_crocantes", inicio, fim)

    print(f"✅ {func1.nome} - Ocupações após alocação: {len(func1.ocupacoes)}")
    print(f"✅ {func3.nome} - Ocupações após alocação: {len(func3.ocupacoes)}")
    print()

    # =========================================================================
    # CENÁRIO 2: Segunda execução (usuário executa novamente via menu)
    # =========================================================================
    print()
    print("📋 CENÁRIO 2: Segunda alocação do MESMO pedido (usuário reexecuta)")
    print("-" * 70)

    # Simula nova instância do gestor (como se fosse uma nova chamada do menu)
    gestor2 = GestorFuncionarios()
    print(f"✅ GestorFuncionarios instanciado novamente - ID: {id(gestor2)}")

    # Verificar se é o mesmo objeto (singleton)
    if id(gestor1) == id(gestor2):
        print("✅ SINGLETON CONFIRMADO: Mesma instância do gestor")
    else:
        print("❌ ERRO: Instâncias diferentes detectadas!")

    print()

    func1_v2 = gestor2.funcionarios_disponiveis[0]
    func3_v2 = gestor2.funcionarios_disponiveis[2]

    print(f"👤 {func1_v2.nome} - Ocupações antes da segunda tentativa: {len(func1_v2.ocupacoes)}")
    print(f"👤 {func3_v2.nome} - Ocupações antes da segunda tentativa: {len(func3_v2.ocupacoes)}")
    print()

    # Tentar alocar novamente no MESMO horário (deve falhar)
    print(f"📝 Tentando alocar NOVAMENTE Ordem 1 | Pedido 1 - Atividade 20011")
    print(f"   Período: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}")
    print()

    func1_v2.registrar_ocupacao(1, 1, 20011, "mistura_de_massas_crocantes", inicio, fim)
    func3_v2.registrar_ocupacao(1, 1, 20011, "mistura_de_massas_crocantes", inicio, fim)

    print(f"📊 {func1_v2.nome} - Ocupações após segunda tentativa: {len(func1_v2.ocupacoes)}")
    print(f"📊 {func3_v2.nome} - Ocupações após segunda tentativa: {len(func3_v2.ocupacoes)}")
    print()

    # =========================================================================
    # VERIFICAÇÃO FINAL
    # =========================================================================
    print()
    print("=" * 70)
    print("📊 RESULTADO DO TESTE")
    print("=" * 70)

    resultado_gestor = "✅ PASSOU" if id(gestor1) == id(gestor2) else "❌ FALHOU"
    resultado_func1 = "✅ PASSOU" if len(func1_v2.ocupacoes) == 1 else "❌ FALHOU"
    resultado_func3 = "✅ PASSOU" if len(func3_v2.ocupacoes) == 1 else "❌ FALHOU"

    print(f"1. Singleton do GestorFuncionarios: {resultado_gestor}")
    print(f"2. {func1.nome} bloqueou segunda alocação: {resultado_func1}")
    print(f"3. {func3.nome} bloqueou segunda alocação: {resultado_func3}")
    print()

    if all(r == "✅ PASSOU" for r in [resultado_gestor, resultado_func1, resultado_func3]):
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ O sistema está protegido contra alocações duplicadas")
        print("✅ As ocupações persistem entre múltiplas chamadas do menu")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM!")
        print("❌ Verifique a implementação do singleton")

    print("=" * 70)


if __name__ == "__main__":
    teste_alocacao_multipla()
