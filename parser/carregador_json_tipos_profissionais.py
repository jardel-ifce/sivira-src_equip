import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

import json
import os
import glob
from enums.funcionarios.tipo_profissional import TipoProfissional
from enums.producao.tipo_item import TipoItem
from typing import Set, Tuple

# ==========================================================
# 🎯 Determinação automática de tipo e caminho baseado no ID
# ==========================================================
def determinar_caminho_por_id(id_item: int) -> Tuple[str, TipoItem]:
    """
    Determina o caminho e tipo baseado no ID do item
    - IDs 1000-1999: PRODUTO -> data/produtos/atividades/
    - IDs 2000-2999: SUBPRODUTO -> data/subprodutos/atividades/
    """
    # Definir o diretório base absoluto
    base_dir = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip"
    
    if 1000 <= id_item <= 1999:
        caminho = os.path.join(base_dir, "data/produtos/atividades")
        return caminho, TipoItem.PRODUTO
    elif 2000 <= id_item <= 2999:
        caminho = os.path.join(base_dir, "data/subprodutos/atividades")  # Corrigido: subprodutos (com 's')
        return caminho, TipoItem.SUBPRODUTO
    else:
        raise ValueError(f"❌ ID {id_item} fora do range válido (1000-1999 para PRODUTO, 2000-2999 para SUBPRODUTO)")

def encontrar_arquivo_por_id(id_item: int) -> Tuple[str, TipoItem]:
    """
    Encontra o arquivo JSON baseado no ID, ignorando o que vem depois do _
    """
    base_path, tipo_item = determinar_caminho_por_id(id_item)
    pattern = os.path.join(base_path, f"{id_item}_*.json")
    
    print(f"🔍 DEBUG: Procurando arquivos com padrão: {pattern}")
    
    arquivos = glob.glob(pattern)
    
    if not arquivos:
        # Vamos também tentar verificar se o diretório existe
        if not os.path.exists(base_path):
            print(f"❌ DEBUG: Diretório não existe: {base_path}")
            # Listar diretórios disponíveis para debug
            parent_dir = os.path.dirname(base_path)
            if os.path.exists(parent_dir):
                dirs_disponiveis = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
                print(f"📁 DEBUG: Diretórios disponíveis em {parent_dir}: {dirs_disponiveis}")
        else:
            # Listar arquivos no diretório para debug
            arquivos_no_dir = os.listdir(base_path)
            print(f"📄 DEBUG: Arquivos disponíveis em {base_path}: {arquivos_no_dir}")
        
        raise FileNotFoundError(f"❌ Nenhum arquivo encontrado para ID {id_item} em {pattern}")
    
    if len(arquivos) > 1:
        print(f"⚠️ DEBUG: Múltiplos arquivos encontrados: {arquivos}. Usando o primeiro.")
    
    print(f"✅ DEBUG: Arquivo encontrado: {arquivos[0]}")
    return arquivos[0], tipo_item

def carregar_item_por_id(id_item: int) -> dict:
    """
    Carrega o conteúdo de um arquivo de item baseado no ID
    """
    try:
        caminho_arquivo, _ = encontrar_arquivo_por_id(id_item)
        print(f"🔍 DEBUG: Tentando carregar arquivo: {caminho_arquivo}")
        
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            dados = json.loads(f.read())
        
        print(f"✅ DEBUG: Arquivo carregado com sucesso. ID do item: {dados.get('id_item')}")
        print(f"📊 DEBUG: Número de atividades: {len(dados.get('atividades', []))}")
        
        return dados
    except Exception as e:
        print(f"❌ DEBUG: Erro ao carregar item {id_item}: {e}")
        return None

def buscar_tipos_profissionais_por_id_item(id_item: int) -> Set[TipoProfissional]:
    """
    📦 Coleta os tipos únicos de profissionais exigidos nas atividades de um produto
    e de seus subprodutos (se houver), com base no ID do item (produto ou subproduto).
    
    Agora funciona com a nova estrutura de arquivos individuais.

    Args:
        id_item (int): ID do item (produto ou subproduto)

    Returns:
        Set[TipoProfissional]: Conjunto com tipos únicos de profissionais envolvidos
    """
    tipos: Set[TipoProfissional] = set()

    # 🔁 Função auxiliar para adicionar tipos de uma lista de atividades
    def adicionar_tipos(atividades: list):
        print(f"🔍 DEBUG: Processando {len(atividades)} atividades")
        for i, atividade in enumerate(atividades):
            tipos_atividade = atividade.get("tipos_profissionais_permitidos", [])
            print(f"   Atividade {i+1}: {len(tipos_atividade)} tipos profissionais - {tipos_atividade}")
            
            for nome_tipo in tipos_atividade:
                if nome_tipo:
                    try:
                        tipos.add(TipoProfissional[nome_tipo])
                        print(f"   ✅ Adicionado: {nome_tipo}")
                    except KeyError:
                        print(f"   ⚠️ Tipo profissional '{nome_tipo}' não reconhecido, ignorando...")
                    except Exception as e:
                        print(f"   ❌ Erro ao processar tipo '{nome_tipo}': {e}")

    # 🔁 Função recursiva para explorar subprodutos (caso existam)
    def explorar(id_alvo: int):
        print(f"🧭 DEBUG: Explorando ID {id_alvo}")
        
        # Carregar item baseado no ID
        item = carregar_item_por_id(id_alvo)
        
        if not item:
            print(f"❌ DEBUG: Item {id_alvo} não encontrado")
            return  # Item não encontrado, pular

        print(f"✅ DEBUG: Item {id_alvo} carregado: {item.get('nome', 'sem nome')}")

        # Adicionar tipos profissionais das atividades deste item
        atividades = item.get("atividades", [])
        if atividades:
            adicionar_tipos(atividades)
        else:
            print(f"⚠️ DEBUG: Nenhuma atividade encontrada para o item {id_alvo}")

        # Busca por subatividades com base no campo "id_macroatividade_produto"
        for atividade in item.get("atividades", []):
            id_sub = atividade.get("id_macroatividade_produto")
            if id_sub and isinstance(id_sub, int):
                print(f"🔗 DEBUG: Encontrada subatividade com ID {id_sub}")
                explorar(id_sub)

    # 🧭 Início da exploração
    print(f"🚀 DEBUG: Iniciando busca de tipos profissionais para ID {id_item}")
    try:
        explorar(id_item)
        print(f"✅ DEBUG: Exploração concluída. Total de tipos encontrados: {len(tipos)}")
        for tipo in tipos:
            print(f"   📋 {tipo.name}")
    except Exception as e:
        print(f"❌ Erro ao buscar tipos profissionais para ID {id_item}: {e}")
        import traceback
        traceback.print_exc()
        return set()

    return tipos

def buscar_todos_tipos_profissionais_sistema() -> Set[TipoProfissional]:
    """
    🌐 Busca todos os tipos profissionais utilizados em todo o sistema
    percorrendo todos os arquivos de atividades (produtos e subprodutos)
    """
    tipos: Set[TipoProfissional] = set()
    
    # Definir o diretório base absoluto
    base_dir = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip"
    
    # Caminhos para buscar todos os arquivos (corrigidos)
    caminhos = [
        os.path.join(base_dir, "data/produtos/atividades/*.json"),
        os.path.join(base_dir, "data/subprodutos/atividades/*.json")  # Corrigido: subprodutos (com 's')
    ]
    
    print("🔍 DEBUG: Buscando tipos profissionais em todo o sistema...")
    
    for caminho_pattern in caminhos:
        print(f"📂 DEBUG: Verificando padrão: {caminho_pattern}")
        arquivos = glob.glob(caminho_pattern)
        print(f"📁 DEBUG: Encontrados {len(arquivos)} arquivos")
        
        # Debug adicional se não encontrar arquivos
        if len(arquivos) == 0:
            dir_path = os.path.dirname(caminho_pattern)
            if os.path.exists(dir_path):
                arquivos_disponiveis = os.listdir(dir_path)
                print(f"📄 DEBUG: Arquivos disponíveis em {dir_path}: {arquivos_disponiveis}")
            else:
                print(f"❌ DEBUG: Diretório não existe: {dir_path}")
        
        for arquivo in arquivos:
            print(f"   📄 Processando: {arquivo}")
            try:
                with open(arquivo, "r", encoding="utf-8") as f:
                    dados = json.loads(f.read())
                
                # Processar atividades do arquivo
                atividades = dados.get("atividades", [])
                print(f"      🔹 {len(atividades)} atividades encontradas")
                
                for atividade in atividades:
                    tipos_atividade = atividade.get("tipos_profissionais_permitidos", [])
                    for nome_tipo in tipos_atividade:
                        if nome_tipo:
                            try:
                                tipos.add(TipoProfissional[nome_tipo])
                                print(f"      ✅ Tipo adicionado: {nome_tipo}")
                            except KeyError:
                                print(f"      ⚠️ Tipo profissional '{nome_tipo}' não reconhecido em {arquivo}")
                            except Exception as e:
                                print(f"      ❌ Erro ao processar tipo '{nome_tipo}': {e}")
                                
            except Exception as e:
                print(f"❌ Erro ao processar arquivo {arquivo}: {e}")
    
    print(f"✅ DEBUG: Busca no sistema concluída. Total de tipos únicos: {len(tipos)}")
    return tipos

# 🎯 Teste rápido
if __name__ == "__main__":
    print("=== Teste: Tipos Profissionais por ID ===")
    
    # Teste com um ID específico
    try:
        tipos = buscar_tipos_profissionais_por_id_item(2001)  # ID do subproduto massa_crocante
        print(f"Tipos profissionais para ID 2001:")
        for tipo in sorted(tipos, key=lambda t: t.name):
            print(f"✔️ {tipo.name}")
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
    
    print("\n=== Teste: Todos os Tipos Profissionais do Sistema ===")
    try:
        todos_tipos = buscar_todos_tipos_profissionais_sistema()
        print(f"Total de tipos profissionais únicos no sistema: {len(todos_tipos)}")
        for tipo in sorted(todos_tipos, key=lambda t: t.name):
            print(f"✔️ {tipo.name}")
    except Exception as e:
        print(f"❌ Erro no teste de sistema: {e}")