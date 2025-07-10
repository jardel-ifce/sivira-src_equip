from models.atividades.atividade_modular_produto import AtividadeModularProduto

# Criação da atividade principal do produto
atividade1 = AtividadeModularProduto(id_produto=1, quantidade=240)

# Mostrar atividades criadas
for atividade in atividade1.get_todas_atividades():
    print("=" * 60)
    print(f"📝 Atividade ID: {atividade.id_atividade}")
    print(f"📦 Tipo Item: {atividade.tipo_item.name}")
    print(f"🔢 Quantidade: {atividade.quantidade_produto}")
    print(f"⏱️ Duração estimada: {atividade.duracao}")

print("\n📚 Estrutura de ficha técnica e subprodutos\n")

# Chamada da impressão a partir da ficha principal
atividade1.ficha_tecnica.imprimir_ficha_recursiva()
