import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho

import json
import os
import glob
from enums.producao.tipo_item import TipoItem
from typing import Dict, Any, Tuple, List
from utils.logs.logger_factory import setup_logger

logger = setup_logger("CarregadorAtividades")

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
        caminho = os.path.join(base_dir, "data/produtos/atividades")  # Corrigido: produtos (com 's')
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

    arquivos = glob.glob(pattern)

    if not arquivos:
        raise FileNotFoundError(f"❌ Nenhum arquivo encontrado para ID {id_item} em {pattern}")

    if len(arquivos) > 1:
        logger.warning(f"⚠️ Múltiplos arquivos encontrados para ID {id_item}: {arquivos}. Usando o primeiro.")

    return arquivos[0], tipo_item

# ==========================================================
# 📅 Busca por ID da Atividade (específica)
# ==========================================================
def buscar_dados_por_id_atividade(id_atividade: int, tipo_item: TipoItem = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Busca uma atividade específica pelo ID da atividade.
    O tipo_item é opcional - será determinado automaticamente pelo ID da atividade.
    
    Padrão de IDs de atividade:
    - 10000-19999: Atividades de produtos (ex: 10031 -> item 1003, atividade 1)
    - 20000-29999: Atividades de subprodutos (ex: 20011 -> item 2001, atividade 1)
    """
    # Determinar o ID do item baseado no ID da atividade
    if 10000 <= id_atividade <= 19999:  # Atividades de produtos
        id_item_base = id_atividade // 10  # Ex: 10031 -> 1003
    elif 20000 <= id_atividade <= 29999:  # Atividades de subprodutos
        id_item_base = id_atividade // 10  # Ex: 20011 -> 2001
    else:
        raise ValueError(f"❌ ID da atividade {id_atividade} fora do padrão esperado (10000-19999 para produtos, 20000-29999 para subprodutos)")

    try:
        caminho_arquivo, tipo_determinado = encontrar_arquivo_por_id(id_item_base)

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
            if not conteudo.strip():
                raise ValueError(f"❌ Arquivo {caminho_arquivo} está vazio.")
            dados = json.loads(conteudo)
        
        # Buscar a atividade específica
        atividades = dados.get("atividades", [])
        for i, atividade in enumerate(atividades):
            id_ativ_arquivo = atividade.get("id_atividade")
            logger.info(f"   🔹 Atividade {i+1}: ID={id_ativ_arquivo}, Nome='{atividade.get('nome', 'sem nome')}'")
            
            if id_ativ_arquivo == id_atividade:
                logger.info(f"✅ Atividade {id_atividade} encontrada em '{dados.get('nome')}'")
                
                # Preparar dados gerais do item
                dados_gerais = {
                    "nome_item": dados.get("nome", "item_desconhecido"),
                    "nome_atividade": atividade.get("nome", f"Atividade {id_atividade}"),
                    "id_item": dados.get("id_item"),
                    "tipo_item": tipo_determinado.name
                }
                
                return dados_gerais, atividade
        
        raise ValueError(f"❌ Atividade com id_atividade={id_atividade} não encontrada no arquivo {caminho_arquivo}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar atividade {id_atividade}: {e}")
        raise

# ==========================================================
# 📅 Busca dados completos por ID de Produto ou Subproduto
# ==========================================================
def buscar_dados_por_id_produto_ou_subproduto(id_produto_ou_subproduto: int, tipo_item: TipoItem = None) -> Dict[str, Any]:
    """
    Busca dados completos de um produto ou subproduto pelo ID.
    O tipo_item é opcional - será determinado automaticamente pelo ID.
    """
    try:
        caminho_arquivo, tipo_determinado = encontrar_arquivo_por_id(id_produto_ou_subproduto)

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
            if not conteudo.strip():
                raise ValueError(f"❌ Arquivo {caminho_arquivo} está vazio.")
            dados = json.loads(conteudo)

        # Verificar se o ID corresponde (flexível)
        id_no_arquivo = dados.get("id_item")
        
        nome_item = dados.get('nome', 'sem nome')
        logger.info(f"✅ Item {id_produto_ou_subproduto} encontrado: '{nome_item}' (Tipo: {tipo_determinado.name})")
        
        # Se o ID interno não bate, vamos logar mas não falhar
        if id_no_arquivo != id_produto_ou_subproduto:
            logger.warning(f"⚠️ ID interno ({id_no_arquivo}) difere do ID do arquivo ({id_produto_ou_subproduto}), mas prosseguindo...")
        
        return dados
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar item {id_produto_ou_subproduto}: {e}")
        raise

# ==========================================================
# 📅 Busca todas as atividades por ID de Item
# ==========================================================
def buscar_atividades_por_id_item(id_item: int, tipo_item: TipoItem = None) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    🔎 Retorna todas as atividades associadas ao id_item (subproduto ou produto).
    O tipo_item é opcional - será determinado automaticamente pelo ID.
    
    Returns:
        List[Tuple[Dict, Dict]]: Lista de tuplas (dados_do_item, dados_da_atividade)
    """
    try:
        caminho_arquivo, tipo_determinado = encontrar_arquivo_por_id(id_item)

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            dados = json.loads(f.read())

        # Verificar se o ID corresponde (flexível)
        id_no_arquivo = dados.get("id_item")
        nome_item = dados.get('nome', 'sem nome')
        
        atividades = dados.get("atividades", [])
        logger.info(f"✅ {len(atividades)} atividades encontradas para item '{nome_item}' (ID: {id_item}):")
        
        for i, a in enumerate(atividades):
            id_ativ = a.get('id_atividade', 'sem ID')
            nome_ativ = a.get('nome', 'sem nome')
            logger.info(f"   🔹 Atividade {i+1}: ID={id_ativ} | Nome='{nome_ativ}'")
        
        resultado = [(dados, atividade) for atividade in atividades]
        logger.info(f"📦 Total de atividades retornadas: {len(resultado)}")
        return resultado
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar atividades do item {id_item}: {e}")
        raise ValueError(f"❌ Nenhuma atividade encontrada para id_item={id_item}: {e}")

def listar_todas_atividades() -> Dict[str, list]:
    """
    Lista todas as atividades disponíveis no sistema
    Retorna um dicionário com produtos e subprodutos
    """
    base_dir = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip"
    
    resultado = {
        "produtos": [],
        "subprodutos": []
    }
    
    # Buscar atividades de produtos
    caminho_produtos = os.path.join(base_dir, "data/produtos/atividades/*.json")
    arquivos_produtos = glob.glob(caminho_produtos)
    
    
    for arquivo in arquivos_produtos:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.loads(f.read())
                atividades = dados.get("atividades", [])
                for atividade in atividades:
                    resultado["produtos"].append({
                        "id_item": dados.get("id_item"),
                        "nome_item": dados.get("nome"),
                        "id_atividade": atividade.get("id_atividade"),
                        "nome_atividade": atividade.get("nome"),
                        "arquivo": os.path.basename(arquivo)
                    })
        except Exception as e:
            logger.error(f"❌ Erro ao processar produto {arquivo}: {e}")
    
    # Buscar atividades de subprodutos
    caminho_subprodutos = os.path.join(base_dir, "data/subprodutos/atividades/*.json")
    arquivos_subprodutos = glob.glob(caminho_subprodutos)
    
    
    for arquivo in arquivos_subprodutos:
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.loads(f.read())
                atividades = dados.get("atividades", [])
                for atividade in atividades:
                    resultado["subprodutos"].append({
                        "id_item": dados.get("id_item"),
                        "nome_item": dados.get("nome"),
                        "id_atividade": atividade.get("id_atividade"),
                        "nome_atividade": atividade.get("nome"),
                        "arquivo": os.path.basename(arquivo)
                    })
        except Exception as e:
            logger.error(f"❌ Erro ao processar subproduto {arquivo}: {e}")
    
    return resultado
# ==========================================================
# 🆕 Função para obter faixa de quantidade de um item
# ==========================================================
def obter_faixa_quantidade(id_item: int) -> Tuple[int, int]:
    """
    Obtém a faixa de quantidade (min, max) de um item baseado nas faixas
    da primeira atividade do arquivo JSON.
    
    Args:
        id_item: ID do item (ex: 1001)
        
    Returns:
        Tuple[int, int]: (quantidade_min, quantidade_max)
        
    Raises:
        FileNotFoundError: Se o arquivo não for encontrado
        ValueError: Se as faixas não forem encontradas ou forem inválidas
    """
    try:
        # Encontra e carrega o arquivo
        caminho_arquivo, tipo_determinado = encontrar_arquivo_por_id(id_item)

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            dados = json.loads(f.read())

        # Obtém primeira atividade
        atividades = dados.get("atividades", [])
        if not atividades:
            raise ValueError(f"❌ Nenhuma atividade encontrada no item {id_item}")

        primeira_atividade = atividades[0]
        faixas = primeira_atividade.get("faixas", [])

        if not faixas:
            raise ValueError(f"❌ Nenhuma faixa encontrada na primeira atividade do item {id_item}")

        # Extrai quantidade mínima e máxima de todas as faixas
        quantidade_min = min(faixa.get("quantidade_min", 0) for faixa in faixas)
        quantidade_max = max(faixa.get("quantidade_max", 0) for faixa in faixas)

        if quantidade_min <= 0 or quantidade_max <= 0:
            raise ValueError(f"❌ Faixas inválidas encontradas no item {id_item}: min={quantidade_min}, max={quantidade_max}")

        return quantidade_min, quantidade_max
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter faixa de quantidade para item {id_item}: {e}")
        raise
    
# 🎯 Main de testes
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE: Carregador de Atividades")
    print("=" * 60)
    
    # Teste 1: Listar todas as atividades disponíveis
    print("\n=== 📋 Teste 1: Listagem de todas as atividades ===")
    try:
        todas_atividades = listar_todas_atividades()
        
        print(f"📦 Atividades de produtos encontradas: {len(todas_atividades['produtos'])}")
        for i, atividade in enumerate(todas_atividades['produtos'][:5]):  # Mostrar apenas as 5 primeiras
            print(f"   ✔️ Item {atividade['id_item']} ({atividade['nome_item']}): Atividade {atividade['id_atividade']} - {atividade['nome_atividade']}")
        if len(todas_atividades['produtos']) > 5:
            print(f"   ... e mais {len(todas_atividades['produtos']) - 5} atividades de produtos")
        
        print(f"\n🧩 Atividades de subprodutos encontradas: {len(todas_atividades['subprodutos'])}")
        for i, atividade in enumerate(todas_atividades['subprodutos'][:5]):  # Mostrar apenas as 5 primeiras
            print(f"   ✔️ Item {atividade['id_item']} ({atividade['nome_item']}): Atividade {atividade['id_atividade']} - {atividade['nome_atividade']}")
        if len(todas_atividades['subprodutos']) > 5:
            print(f"   ... e mais {len(todas_atividades['subprodutos']) - 5} atividades de subprodutos")
            
    except Exception as e:
        print(f"❌ Erro no teste de listagem: {e}")
    
    # Teste 2: Buscar dados completos de um produto
    print("\n=== 🔍 Teste 2: Busca de dados completos de produto ===")
    try:
        dados_produto = buscar_dados_por_id_produto_ou_subproduto(1001)
        print(f"✅ Produto encontrado:")
        print(f"   📋 Nome: {dados_produto.get('nome')}")
        print(f"   🆔 ID: {dados_produto.get('id_item')}")
        print(f"   📊 Atividades: {len(dados_produto.get('atividades', []))}")
        
        # Mostrar as primeiras atividades
        atividades = dados_produto.get('atividades', [])
        for i, ativ in enumerate(atividades[:3]):  # Mostrar apenas as 3 primeiras
            print(f"      {i+1}. ID {ativ.get('id_atividade')}: {ativ.get('nome')}")
        if len(atividades) > 3:
            print(f"      ... e mais {len(atividades) - 3} atividades")
        
    except Exception as e:
        print(f"❌ Erro no teste de busca de produto: {e}")
    
    # Teste 3: Buscar dados completos de um subproduto
    print("\n=== 🔍 Teste 3: Busca de dados completos de subproduto ===")
    try:
        dados_subproduto = buscar_dados_por_id_produto_ou_subproduto(2001)
        print(f"✅ Subproduto encontrado:")
        print(f"   📋 Nome: {dados_subproduto.get('nome')}")
        print(f"   🆔 ID: {dados_subproduto.get('id_item')}")
        print(f"   📊 Atividades: {len(dados_subproduto.get('atividades', []))}")
        
        # Mostrar as atividades
        atividades = dados_subproduto.get('atividades', [])
        for i, ativ in enumerate(atividades):
            print(f"      {i+1}. ID {ativ.get('id_atividade')}: {ativ.get('nome')}")
        
    except Exception as e:
        print(f"❌ Erro no teste de busca de subproduto: {e}")
    
    # Teste 4: Buscar todas as atividades de um item
    print("\n=== 🔍 Teste 4: Busca de atividades por ID do item ===")
    try:
        atividades_item = buscar_atividades_por_id_item(1001)  # Produto pão francês
        print(f"✅ Encontradas {len(atividades_item)} atividades para o item 1001:")
        
        for i, (dados_item, dados_atividade) in enumerate(atividades_item):
            print(f"   {i+1}. Atividade ID {dados_atividade.get('id_atividade')}: {dados_atividade.get('nome')}")
            print(f"      Item: {dados_item.get('nome')} (ID: {dados_item.get('id_item')})")
            if i >= 2:  # Mostrar apenas as 3 primeiras
                if len(atividades_item) > 3:
                    print(f"      ... e mais {len(atividades_item) - 3} atividades")
                break
        
    except Exception as e:
        print(f"❌ Erro no teste de busca de atividades por item: {e}")
    
    # Teste 5: Buscar uma atividade específica por ID
    print("\n=== 🔍 Teste 5: Busca de atividade específica por ID ===")
    try:
        # Vamos tentar buscar uma atividade com ID baseado no padrão
        # Se o item 1001 tem atividades, tentamos ID 10011 (item 1001, atividade 1)
        dados_gerais, dados_atividade = buscar_dados_por_id_atividade(10011)
        print(f"✅ Atividade específica encontrada:")
        print(f"   🎯 ID da Atividade: {dados_atividade.get('id_atividade')}")
        print(f"   📋 Nome da Atividade: {dados_atividade.get('nome')}")
        print(f"   🏭 Item Pai: {dados_gerais.get('nome_item')} (ID: {dados_gerais.get('id_item')})")
        print(f"   📄 Tipo: {dados_gerais.get('tipo_item')}")
        
        # Mostrar alguns detalhes da atividade
        tempo = dados_atividade.get('tempo_estimado_minutos', 'N/A')
        dificuldade = dados_atividade.get('dificuldade', 'N/A')
        print(f"   ⏱️ Tempo estimado: {tempo} minutos")
        print(f"   📊 Dificuldade: {dificuldade}")
        
    except Exception as e:
        print(f"❌ Erro no teste de busca de atividade específica: {e}")
        print("🔄 Tentando com outro ID de atividade...")
        
        # Tentar com um ID de subproduto
        try:
            dados_gerais, dados_atividade = buscar_dados_por_id_atividade(20011)
            print(f"✅ Atividade de subproduto encontrada:")
            print(f"   🎯 ID da Atividade: {dados_atividade.get('id_atividade')}")
            print(f"   📋 Nome da Atividade: {dados_atividade.get('nome')}")
            print(f"   🏭 Item Pai: {dados_gerais.get('nome_item')} (ID: {dados_gerais.get('id_item')})")
        except Exception as e2:
            print(f"❌ Erro com ID alternativo: {e2}")
    
    # Teste 6: Teste de erro (ID inválido)
    print("\n=== ⚠️ Teste 6: Teste de tratamento de erro (ID inválido) ===")
    try:
        dados_produto = buscar_dados_por_id_produto_ou_subproduto(9999)  # ID que não existe
        print("❌ ERRO: Deveria ter falhado!")
    except Exception as e:
        print(f"✅ Comportamento esperado - Erro capturado: {type(e).__name__}")
        print(f"   Mensagem: {str(e)[:100]}...")
    
    print("\n" + "=" * 60)
    print("🏁 TESTES CONCLUÍDOS")
    print("=" * 60)