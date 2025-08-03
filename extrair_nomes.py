import os
import re

def extrair_nomes_arquivos_json():
    # Diretório especificado
    diretorio = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/produtos/atividades"
    
    try:
        # Verifica se o diretório existe
        if not os.path.exists(diretorio):
            print(f"Erro: O diretório '{diretorio}' não existe.")
            return
        
        # Lista todos os arquivos no diretório
        arquivos = os.listdir(diretorio)
        
        # Filtra apenas arquivos .json
        arquivos_json = [arquivo for arquivo in arquivos if arquivo.endswith('.json')]
        
        if not arquivos_json:
            print("Nenhum arquivo .json encontrado no diretório.")
            return
        
        print(f"Encontrados {len(arquivos_json)} arquivo(s) .json:")
        print("-" * 50)
        
        # Processa cada arquivo JSON
        for arquivo in sorted(arquivos_json):
            # Remove a extensão .json
            nome_sem_extensao = arquivo[:-5]
            
            # Usa regex para separar o número do resto do nome
            match = re.match(r'^(\d+)_(.+)$', nome_sem_extensao)
            
            if match:
                numero = match.group(1)
                nome = match.group(2).replace('_', ' ')
                print(f"{numero} - {nome}")
            else:
                # Se não seguir o padrão esperado, exibe o nome original
                print(f"Formato não reconhecido: {arquivo}")
    
    except PermissionError:
        print(f"Erro: Sem permissão para acessar o diretório '{diretorio}'.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

# Executa a função
if __name__ == "__main__":
    extrair_nomes_arquivos_json()