import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho
import json
import os
import glob
from enums.producao.tipo_item import TipoItem
from typing import Dict, Any, Tuple
from utils.logs.logger_factory import setup_logger

logger = setup_logger("CarregadorFichaTecnica")

# ==========================================================
# 🎯 Determinação automática de tipo e caminho baseado no ID
# ==========================================================
def determinar_caminho_ficha_por_id(id_ficha_tecnica: int) -> Tuple[str, TipoItem]:
    """
    Determina o caminho e tipo baseado no ID da ficha técnica
    - IDs 1000-1999: PRODUTO -> data/produtos/fichas_tecnicas/
    - IDs 2000-2999: SUBPRODUTO -> data/subprodutos/fichas_tecnicas/
    """
    # Definir o diretório base absoluto
    base_dir = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip"
    
    if 1000 <= id_ficha_tecnica <= 1999:
        caminho = os.path.join(base_dir, "data/produtos/fichas_tecnicas")  # Corrigido: produtos (com 's')
        return caminho, TipoItem.PRODUTO
    elif 2000 <= id_ficha_tecnica <= 2999:
        caminho = os.path.join(base_dir, "data/subprodutos/fichas_tecnicas")  # Corrigido: subprodutos (com 's')
        return caminho, TipoItem.SUBPRODUTO
    else:
        raise ValueError(f"❌ ID {id_ficha_tecnica} fora do range válido (1000-1999 para PRODUTO, 2000-2999 para SUBPRODUTO)")

def encontrar_ficha_por_id(id_ficha_tecnica: int) -> Tuple[str, TipoItem]:
    """
    Encontra o arquivo de ficha técnica baseado no ID, ignorando o que vem depois do _
    CORREÇÃO: Os arquivos seguem o padrão ID_*.json, não ficha_ID_*.json
    """
    base_path, tipo_item = determinar_caminho_ficha_por_id(id_ficha_tecnica)
    pattern = os.path.join(base_path, f"{id_ficha_tecnica}_*.json")  # Corrigido: removido "ficha_"
    
    logger.info(f"🔍 DEBUG: Procurando arquivos com padrão: {pattern}")
    
    arquivos = glob.glob(pattern)
    
    if not arquivos:
        # Debug adicional para entender a estrutura
        if not os.path.exists(base_path):
            logger.error(f"❌ DEBUG: Diretório não existe: {base_path}")
            # Listar diretórios disponíveis para debug
            parent_dir = os.path.dirname(base_path)
            if os.path.exists(parent_dir):
                dirs_disponiveis = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
                logger.info(f"📁 DEBUG: Diretórios disponíveis em {parent_dir}: {dirs_disponiveis}")
        else:
            # Listar arquivos no diretório para debug
            arquivos_no_dir = os.listdir(base_path)
            logger.info(f"📄 DEBUG: Arquivos disponíveis em {base_path}: {arquivos_no_dir}")
        
        raise FileNotFoundError(f"❌ Nenhuma ficha técnica encontrada para ID {id_ficha_tecnica} em {pattern}")
    
    if len(arquivos) > 1:
        logger.warning(f"⚠️ Múltiplas fichas técnicas encontradas para ID {id_ficha_tecnica}: {arquivos}. Usando a primeira.")
    
    logger.info(f"✅ DEBUG: Arquivo encontrado: {arquivos[0]}")
    return arquivos[0], tipo_item

def encontrar_ficha_por_nome(nome_subproduto: str) -> str:
    """
    Encontra ficha técnica de subproduto pelo nome (busca em todos os arquivos de subprodutos)
    CORREÇÃO: Os arquivos seguem o padrão ID_*.json, não ficha_*.json
    """
    base_dir = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip"
    base_path = os.path.join(base_dir, "data/subprodutos/fichas_tecnicas")  # Corrigido: subprodutos (com 's')
    pattern = os.path.join(base_path, "*.json")  # Corrigido: removido "ficha_"
    
    logger.info(f"🔍 DEBUG: Procurando fichas com padrão: {pattern}")
    
    arquivos = glob.glob(pattern)
    
    if not arquivos:
        # Debug adicional
        if os.path.exists(base_path):
            arquivos_no_dir = os.listdir(base_path)
            logger.info(f"📄 DEBUG: Arquivos disponíveis em {base_path}: {arquivos_no_dir}")
        else:
            logger.error(f"❌ DEBUG: Diretório não existe: {base_path}")
        
        raise FileNotFoundError(f"❌ Nenhuma ficha técnica encontrada em {base_path}")
    
    logger.info(f"📁 DEBUG: Encontrados {len(arquivos)} arquivos de fichas técnicas")
    
    # Buscar em todos os arquivos de fichas técnicas de subprodutos
    for arquivo in arquivos:
        logger.info(f"   📄 Verificando arquivo: {arquivo}")
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
                if not conteudo.strip():
                    logger.warning(f"⚠️ Arquivo vazio: {arquivo}")
                    continue
                    
                dados = json.loads(conteudo)
                nome_arquivo = dados.get("nome", "")
                logger.info(f"      Nome no arquivo: '{nome_arquivo}'")
                
                if nome_arquivo == nome_subproduto:
                    logger.info(f"✅ Encontrada correspondência: {arquivo}")
                    return arquivo
                    
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro JSON no arquivo {arquivo}: {e}")
            continue
        except FileNotFoundError as e:
            logger.error(f"❌ Arquivo não encontrado: {arquivo}: {e}")
            continue
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao processar {arquivo}: {e}")
            continue
    
    raise ValueError(f"❌ Subproduto com nome '{nome_subproduto}' não encontrado")

# ===============================================
# 📦 Leitura e carregamento de fichas técnicas
# ===============================================
def buscar_ficha_tecnica_por_id(id_ficha_tecnica: int, tipo_item: TipoItem = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Carrega a ficha técnica correspondente a um ID específico.
    O tipo_item é opcional - será determinado automaticamente pelo ID.
    Retorna uma tupla: (item_completo, ficha_tecnica_do_item)
    """
    try:
        logger.info(f"🚀 DEBUG: Iniciando busca de ficha técnica para ID {id_ficha_tecnica}")
        
        caminho_arquivo, tipo_determinado = encontrar_ficha_por_id(id_ficha_tecnica)
        
        logger.info(f"🔍 DEBUG: Carregando arquivo: {caminho_arquivo}")
        
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
            if not conteudo.strip():
                raise ValueError(f"❌ Arquivo {caminho_arquivo} está vazio.")
            dados = json.loads(conteudo)
        
        # Verificar se o ID da ficha técnica corresponde
        id_no_arquivo = dados.get("id_ficha_tecnica")
        logger.info(f"📊 DEBUG: ID no arquivo: {id_no_arquivo}, ID solicitado: {id_ficha_tecnica}")
        
        # Permitir que o arquivo seja encontrado mesmo se o ID interno não bater exatamente
        # pois o importante é que encontramos o arquivo pelo padrão ID_*.json
        nome_item = dados.get('nome', 'sem nome')
        logger.info(f"✅ Ficha técnica {id_ficha_tecnica} encontrada: '{nome_item}'")
        logger.info(f"📋 DEBUG: Tipo determinado: {tipo_determinado.name}")
        
        # Se o ID interno não bate, vamos logar mas não falhar
        if id_no_arquivo != id_ficha_tecnica:
            logger.warning(f"⚠️ ID interno ({id_no_arquivo}) difere do ID do arquivo ({id_ficha_tecnica}), mas prosseguindo...")
        
        return dados, dados  # Retorna duas vezes o item (compatibilidade com código existente)
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar ficha técnica {id_ficha_tecnica}: {e}")
        raise ValueError(f"❌ Ficha técnica com id_ficha_tecnica={id_ficha_tecnica} não encontrada: {e}")

def buscar_ficha_tecnica_subproduto_por_nome(nome_subproduto: str) -> Dict[str, Any]:
    """
    Busca a ficha técnica de um subproduto pelo campo 'nome'.
    Agora busca em arquivos individuais ao invés de um arquivo único.
    """
    try:
        logger.info(f"🚀 DEBUG: Iniciando busca de subproduto por nome: '{nome_subproduto}'")
        
        caminho_arquivo = encontrar_ficha_por_nome(nome_subproduto)
        
        logger.info(f"🔍 DEBUG: Carregando arquivo encontrado: {caminho_arquivo}")
        
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
            if not conteudo.strip():
                raise ValueError(f"❌ Arquivo {caminho_arquivo} está vazio.")
            dados = json.loads(conteudo)
        
        # Verificar se o nome corresponde (dupla verificação)
        nome_no_arquivo = dados.get("nome")
        logger.info(f"📊 DEBUG: Nome no arquivo: '{nome_no_arquivo}', Nome solicitado: '{nome_subproduto}'")
        
        if nome_no_arquivo == nome_subproduto:
            id_ficha = dados.get('id_ficha_tecnica', 'sem ID')
            logger.info(f"✅ Ficha técnica do subproduto '{nome_subproduto}' encontrada (ID: {id_ficha})")
            return dados
        else:
            raise ValueError(f"❌ Nome no arquivo ('{nome_no_arquivo}') não corresponde ao nome solicitado ('{nome_subproduto}')")
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar ficha técnica do subproduto '{nome_subproduto}': {e}")
        raise ValueError(f"❌ Subproduto com nome '{nome_subproduto}' não encontrado: {e}")

def listar_todas_fichas_tecnicas() -> Dict[str, list]:
    """
    Lista todas as fichas técnicas disponíveis no sistema
    Retorna um dicionário com produtos e subprodutos
    """
    base_dir = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip"
    
    resultado = {
        "produtos": [],
        "subprodutos": []
    }
    
    # Buscar fichas de produtos
    caminho_produtos = os.path.join(base_dir, "data/produtos/fichas_tecnicas/*.json")
    arquivos_produtos = glob.glob(caminho_produtos)
    
    logger.info(f"📂 DEBUG: Encontradas {len(arquivos_produtos)} fichas de produtos")
    
    for arquivo in arquivos_produtos:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.loads(f.read())
                resultado["produtos"].append({
                    "id": dados.get("id_ficha_tecnica"),
                    "nome": dados.get("nome"),
                    "arquivo": os.path.basename(arquivo)
                })
        except Exception as e:
            logger.error(f"❌ Erro ao processar produto {arquivo}: {e}")
    
    # Buscar fichas de subprodutos
    caminho_subprodutos = os.path.join(base_dir, "data/subprodutos/fichas_tecnicas/*.json")
    arquivos_subprodutos = glob.glob(caminho_subprodutos)
    
    logger.info(f"📂 DEBUG: Encontradas {len(arquivos_subprodutos)} fichas de subprodutos")
    
    for arquivo in arquivos_subprodutos:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.loads(f.read())
                resultado["subprodutos"].append({
                    "id": dados.get("id_ficha_tecnica"),
                    "nome": dados.get("nome"),
                    "arquivo": os.path.basename(arquivo)
                })
        except Exception as e:
            logger.error(f"❌ Erro ao processar subproduto {arquivo}: {e}")
    
    return resultado

# 🎯 Main de testes
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE: Carregador de Fichas Técnicas")
    print("=" * 60)
    
    # Teste 1: Listar todas as fichas técnicas disponíveis
    print("\n=== 📋 Teste 1: Listagem de todas as fichas técnicas ===")
    try:
        todas_fichas = listar_todas_fichas_tecnicas()
        
        print(f"📦 Produtos encontrados: {len(todas_fichas['produtos'])}")
        for produto in todas_fichas['produtos']:
            print(f"   ✔️ ID {produto['id']}: {produto['nome']} ({produto['arquivo']})")
        
        print(f"\n🧩 Subprodutos encontrados: {len(todas_fichas['subprodutos'])}")
        for subproduto in todas_fichas['subprodutos']:
            print(f"   ✔️ ID {subproduto['id']}: {subproduto['nome']} ({subproduto['arquivo']})")
            
    except Exception as e:
        print(f"❌ Erro no teste de listagem: {e}")
    
    # Teste 2: Buscar ficha técnica por ID (produto)
    print("\n=== 🔍 Teste 2: Busca de ficha técnica por ID (Produto) ===")
    try:
        # Tentar buscar um produto (supondo que existe ID 1001)
        item_completo, ficha_tecnica = buscar_ficha_tecnica_por_id(1001)
        print(f"✅ Sucesso! Produto encontrado:")
        print(f"   📋 Nome: {ficha_tecnica.get('nome')}")
        print(f"   🆔 ID: {ficha_tecnica.get('id_ficha_tecnica')}")
        print(f"   📄 Tipo: {ficha_tecnica.get('tipo_item', 'N/A')}")
        
        # Mostrar alguns ingredientes se existirem
        ingredientes = ficha_tecnica.get('ingredientes', [])
        if ingredientes:
            print(f"   🥄 Ingredientes: {len(ingredientes)} itens")
            for i, ing in enumerate(ingredientes[:3]):  # Mostrar apenas os 3 primeiros
                nome = ing.get('nome', 'sem nome')
                quantidade = ing.get('quantidade', 0)
                unidade = ing.get('unidade', '')
                print(f"      {i+1}. {nome}: {quantidade} {unidade}")
            if len(ingredientes) > 3:
                print(f"      ... e mais {len(ingredientes) - 3} ingredientes")
        
    except Exception as e:
        print(f"❌ Erro no teste de busca por ID (produto): {e}")
    
    # Teste 3: Buscar ficha técnica por ID (subproduto)
    print("\n=== 🔍 Teste 3: Busca de ficha técnica por ID (Subproduto) ===")
    try:
        # Tentar buscar um subproduto (supondo que existe ID 2001)
        item_completo, ficha_tecnica = buscar_ficha_tecnica_por_id(2001)
        print(f"✅ Sucesso! Subproduto encontrado:")
        print(f"   📋 Nome: {ficha_tecnica.get('nome')}")
        print(f"   🆔 ID: {ficha_tecnica.get('id_ficha_tecnica')}")
        print(f"   📄 Tipo: {ficha_tecnica.get('tipo_item', 'N/A')}")
        
        # Mostrar alguns ingredientes se existirem
        ingredientes = ficha_tecnica.get('ingredientes', [])
        if ingredientes:
            print(f"   🥄 Ingredientes: {len(ingredientes)} itens")
            for i, ing in enumerate(ingredientes[:3]):  # Mostrar apenas os 3 primeiros
                nome = ing.get('nome', 'sem nome')
                quantidade = ing.get('quantidade', 0)
                unidade = ing.get('unidade', '')
                print(f"      {i+1}. {nome}: {quantidade} {unidade}")
            if len(ingredientes) > 3:
                print(f"      ... e mais {len(ingredientes) - 3} ingredientes")
        
    except Exception as e:
        print(f"❌ Erro no teste de busca por ID (subproduto): {e}")
    
    # Teste 4: Buscar subproduto por nome
    print("\n=== 🔍 Teste 4: Busca de subproduto por nome ===")
    try:
        # Usar um nome mais genérico que pode estar nos arquivos
        nome_teste = "massa_crocante"  # Primeiro tentativa
        
        ficha_tecnica = buscar_ficha_tecnica_subproduto_por_nome(nome_teste)
        print(f"✅ Sucesso! Subproduto '{nome_teste}' encontrado:")
        print(f"   📋 Nome: {ficha_tecnica.get('nome')}")
        print(f"   🆔 ID: {ficha_tecnica.get('id_ficha_tecnica')}")
        print(f"   📝 Descrição: {ficha_tecnica.get('descricao', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erro no teste de busca por nome: {e}")
        
        # Tentar com nomes alternativos baseados nos arquivos que vimos
        # Vamos usar os nomes que aparecem na listagem
        nomes_alternativos = ["massa_para_frituras", "massa_suave", "creme_de_queijo", "ganache_de_chocolate"]
        print("🔄 Tentando nomes alternativos...")
        
        for nome_alt in nomes_alternativos:
            try:
                ficha_tecnica = buscar_ficha_tecnica_subproduto_por_nome(nome_alt)
                print(f"✅ Sucesso com nome alternativo '{nome_alt}'!")
                print(f"   📋 Nome: {ficha_tecnica.get('nome')}")
                print(f"   🆔 ID: {ficha_tecnica.get('id_ficha_tecnica')}")
                break
            except:
                continue
        else:
            print("❌ Nenhum nome alternativo funcionou")
            print("🔍 Vamos tentar carregar um arquivo específico para ver sua estrutura...")
            
            # Debug: carregar um arquivo específico para ver sua estrutura
            try:
                arquivo_debug = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/subprodutos/fichas_tecnicas/2001_massa_crocante.json"
                with open(arquivo_debug, "r", encoding="utf-8") as f:
                    dados_debug = json.loads(f.read())
                    print(f"📋 Estrutura do arquivo 2001_massa_crocante.json:")
                    print(f"   Nome no arquivo: '{dados_debug.get('nome', 'N/A')}'")
                    print(f"   ID no arquivo: {dados_debug.get('id_ficha_tecnica', 'N/A')}")
                    print(f"   Chaves disponíveis: {list(dados_debug.keys())}")
            except Exception as debug_error:
                print(f"❌ Erro no debug: {debug_error}")
    
    # Teste 5: Teste de erro (ID inválido)
    print("\n=== ⚠️ Teste 5: Teste de tratamento de erro (ID inválido) ===")
    try:
        item_completo, ficha_tecnica = buscar_ficha_tecnica_por_id(9999)  # ID que não existe
        print("❌ ERRO: Deveria ter falhado!")
    except Exception as e:
        print(f"✅ Comportamento esperado - Erro capturado: {type(e).__name__}")
        print(f"   Mensagem: {str(e)[:100]}...")
    
    print("\n" + "=" * 60)
    print("🏁 TESTES CONCLUÍDOS")
    print("=" * 60)