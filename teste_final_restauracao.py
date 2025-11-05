"""
Teste Final de Restauração
===========================

Executa UMA restauração limpa e verifica o resultado.
"""

from utils.recuperacao.recuperador_estado import RecuperadorEstado
from factory.fabrica_equipamentos import equipamentos_disponiveis

print("=" * 80)
print("TESTE FINAL DE RESTAURAÇÃO")
print("=" * 80)
print()

# Executar restauração
print("⏳ Executando restauração...")
recuperador = RecuperadorEstado()
relatorio = recuperador.recuperar_de_log(
    "logs/equipamentos_detalhados/ocupacoes_detalhadas_ordem_1_pedidos_1_2_20251027_195345.log",
    aplicar_restauracao=True
)

print()
print("=" * 80)
print("RESULTADO DA RESTAURAÇÃO")
print("=" * 80)
print()
print(f"✅ Ocupações recuperadas: {relatorio.total_ocupacoes_recuperadas}")
print(f"✅ Equipamentos restaurados: {relatorio.equipamentos_restaurados}/{relatorio.total_equipamentos}")
print()

# Verificar estado na memória
total_ocupacoes_memoria = 0
equipamentos_com_ocupacoes = 0

print("=" * 80)
print("VERIFICAÇÃO NA MEMÓRIA")
print("=" * 80)
print()

for equipamento in equipamentos_disponiveis:
    nome = equipamento.nome if hasattr(equipamento, 'nome') else "Sem nome"
    tipo = type(equipamento).__name__

    # Contar ocupações
    ocupacoes = 0
    if hasattr(equipamento, 'fracoes_ocupacoes'):
        for fracao in equipamento.fracoes_ocupacoes:
            ocupacoes += len(fracao)
    elif hasattr(equipamento, 'ocupacoes'):
        ocupacoes = len(equipamento.ocupacoes)
    elif hasattr(equipamento, 'niveis_ocupacoes'):
        for nivel in equipamento.niveis_ocupacoes:
            ocupacoes += len(nivel)
        # Câmara pode ter caixas também
        if hasattr(equipamento, 'caixas_ocupacoes'):
            for caixa in equipamento.caixas_ocupacoes:
                ocupacoes += len(caixa)
    elif hasattr(equipamento, 'caixas_ocupacoes'):
        for caixa in equipamento.caixas_ocupacoes:
            ocupacoes += len(caixa)

    if ocupacoes > 0:
        equipamentos_com_ocupacoes += 1
        total_ocupacoes_memoria += ocupacoes
        print(f"✅ {nome} ({tipo}): {ocupacoes} ocupações")

print()
print("=" * 80)
print("RESUMO FINAL")
print("=" * 80)
print()
print(f"📊 Total de ocupações na memória: {total_ocupacoes_memoria}")
print(f"📊 Equipamentos com ocupações: {equipamentos_com_ocupacoes}")
print()

# Comparação
if total_ocupacoes_memoria == relatorio.total_ocupacoes_recuperadas:
    print(f"🎉 SUCESSO COMPLETO!")
    print(f"   Todas as {total_ocupacoes_memoria} ocupações foram restauradas corretamente!")
elif total_ocupacoes_memoria >= relatorio.total_ocupacoes_recuperadas * 0.9:
    percentual = (total_ocupacoes_memoria / relatorio.total_ocupacoes_recuperadas) * 100
    print(f"✅ SUCESSO PARCIAL ({percentual:.1f}%)")
    print(f"   {total_ocupacoes_memoria}/{relatorio.total_ocupacoes_recuperadas} ocupações restauradas")
else:
    print(f"⚠️  PROBLEMA DETECTADO")
    print(f"   Esperado: {relatorio.total_ocupacoes_recuperadas}")
    print(f"   Obtido: {total_ocupacoes_memoria}")

print()
print("=" * 80)
