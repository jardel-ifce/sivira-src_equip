"""
Script de teste para verificar se as ocupações de funcionários impedem alocações duplicadas
"""
from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios
from datetime import datetime

def testar_ocupacoes():
    print("=" * 80)
    print("🧪 TESTE: Verificação de ocupações e prevenção de duplicatas")
    print("=" * 80)
    print()

    # Criar gestor (singleton)
    gestor = GestorFuncionarios()

    # Limpar todas as alocações para começar do zero
    print("🧹 Limpando todas as alocações anteriores...")
    gestor.limpar_todas_alocacoes()
    print()

    # Verificar estado inicial dos funcionários
    print("📊 ESTADO INICIAL DOS FUNCIONÁRIOS:")
    print("-" * 80)
    for func in gestor.funcionarios_disponiveis:
        print(f"   👤 {func.nome}: {len(func.ocupacoes)} ocupações")
    print()

    # Alocar funcionários para ordem 1, pedido 1
    print("🎯 ALOCANDO FUNCIONÁRIOS PARA ORDEM 1 | PEDIDO 1...")
    print("-" * 80)
    sucesso = gestor.alocar_funcionarios_para_ordem_pedido(1, 1)
    print(f"   Resultado: {'✅ Sucesso' if sucesso else '❌ Falha'}")
    print()

    # Verificar ocupações após primeira alocação
    print("📊 ESTADO APÓS PRIMEIRA ALOCAÇÃO:")
    print("-" * 80)
    total_ocupacoes = 0
    for func in gestor.funcionarios_disponiveis:
        if func.ocupacoes:
            print(f"   👤 {func.nome}: {len(func.ocupacoes)} ocupações")
            for ocup in func.ocupacoes[:2]:  # Mostrar apenas 2 primeiras
                id_ordem, id_pedido, id_ativ, nome_ativ, inicio, fim = ocup
                print(f"      └ Ordem {id_ordem} | Pedido {id_pedido} | {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')}")
            if len(func.ocupacoes) > 2:
                print(f"      └ ... e mais {len(func.ocupacoes) - 2} ocupações")
            total_ocupacoes += len(func.ocupacoes)
    print(f"\n   📝 Total de ocupações registradas: {total_ocupacoes}")
    print()

    # Tentar realocar o mesmo pedido (deve falhar)
    print("⚠️ TENTANDO REALOCAR O MESMO PEDIDO (DEVE FALHAR)...")
    print("-" * 80)
    sucesso = gestor.alocar_funcionarios_para_ordem_pedido(1, 1)
    print(f"   Resultado: {'✅ Sucesso' if sucesso else '❌ Falha (esperado)'}")
    print()

    # Verificar se as ocupações permaneceram inalteradas
    print("📊 ESTADO APÓS TENTATIVA DE REALOCAÇÃO:")
    print("-" * 80)
    total_ocupacoes_apos = 0
    for func in gestor.funcionarios_disponiveis:
        if func.ocupacoes:
            total_ocupacoes_apos += len(func.ocupacoes)
    print(f"   📝 Total de ocupações: {total_ocupacoes_apos}")
    print(f"   {'✅' if total_ocupacoes == total_ocupacoes_apos else '❌'} Ocupações {'não foram duplicadas' if total_ocupacoes == total_ocupacoes_apos else 'FORAM DUPLICADAS!'}")
    print()

    # Testar verificação de disponibilidade com horários conflitantes
    print("🧪 TESTANDO VERIFICAÇÃO DE DISPONIBILIDADE:")
    print("-" * 80)
    funcionario_1 = gestor.funcionarios_disponiveis[0]

    if funcionario_1.ocupacoes:
        # Pegar primeira ocupação
        _, _, _, _, inicio_ocup, fim_ocup = funcionario_1.ocupacoes[0]

        # Tentar criar conflito no mesmo horário
        disponivel, motivo = funcionario_1.verificar_disponibilidade_no_intervalo(inicio_ocup, fim_ocup)
        print(f"   {funcionario_1.nome}:")
        print(f"   └ Ocupação existente: {inicio_ocup.strftime('%H:%M')} - {fim_ocup.strftime('%H:%M')}")
        print(f"   └ Disponível no mesmo horário? {disponivel}")
        print(f"   └ Motivo: {motivo}")
        print()

        # Tentar horário após a ocupação (deve estar disponível)
        novo_inicio = fim_ocup
        novo_fim = fim_ocup.replace(hour=fim_ocup.hour + 1) if fim_ocup.hour < 23 else fim_ocup
        disponivel2, motivo2 = funcionario_1.verificar_disponibilidade_no_intervalo(novo_inicio, novo_fim)
        print(f"   └ Disponível após ocupação ({novo_inicio.strftime('%H:%M')} - {novo_fim.strftime('%H:%M')})? {disponivel2}")
        print(f"   └ Motivo: {motivo2}")
    print()

    # Resumo final
    print("=" * 80)
    print("📋 RESUMO DO TESTE:")
    print("=" * 80)
    print(f"✅ Ocupações preenchidas corretamente: {total_ocupacoes > 0}")
    print(f"✅ Pedidos duplicados bloqueados: {total_ocupacoes == total_ocupacoes_apos}")
    print(f"✅ Verificação de conflitos funcionando: {not disponivel if funcionario_1.ocupacoes else 'N/A'}")
    print("=" * 80)

if __name__ == "__main__":
    testar_ocupacoes()
