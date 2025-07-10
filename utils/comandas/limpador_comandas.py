import os

PASTA_COMANDAS = "data/comandas"

def apagar_todas_as_comandas():
    """
    🗑️ Remove todos os arquivos de comanda (.json) da pasta 'comandas'.
    """
    if not os.path.exists(PASTA_COMANDAS):
        print(f"📁 Pasta '{PASTA_COMANDAS}' não encontrada.")
        return

    arquivos_removidos = 0
    for arquivo in os.listdir(PASTA_COMANDAS):
        if arquivo.endswith(".json"):
            caminho = os.path.join(PASTA_COMANDAS, arquivo)
            try:
                os.remove(caminho)
                print(f"🗑️ Comanda removida: {caminho}")
                arquivos_removidos += 1
            except Exception as e:
                print(f"❌ Erro ao remover '{caminho}': {e}")

    if arquivos_removidos == 0:
        print("📂 Nenhuma comanda encontrada para remoção.")
    else:
        print(f"✅ Total de comandas removidas: {arquivos_removidos}")

