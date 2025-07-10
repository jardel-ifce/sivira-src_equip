import unicodedata
def normalizar_nome(nome: str) -> str:
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")

