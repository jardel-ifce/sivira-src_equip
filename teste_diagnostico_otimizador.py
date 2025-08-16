import json
from datetime import datetime
from typing import List, Dict, Any
import os

class DebugCriacaoAtividades:
    """
    🔍 Sistema de debug detalhado para rastrear criação de atividades.
    Salva logs em arquivo para análise posterior.
    """
    
    def __init__(self, salvar_em_arquivo: bool = True):
        self.logs_debug = []
        self.salvar_arquivo = salvar_em_arquivo
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.arquivo_debug = f"debug_criacao_atividades_{self.timestamp}.json"
        
    def log(self, categoria: str, item_id: int, item_nome: str, dados: Dict[str, Any]):
        """Registra um evento de debug"""
        evento = {
            "timestamp": datetime.now().isoformat(),
            "categoria": categoria,
            "item_id": item_id,
            "item_nome": item_nome,
            "dados": dados
        }
        
        self.logs_debug.append(evento)
        
        # Print para console também
        print(f"🔍 [{categoria}] Item {item_id} ({item_nome}): {dados}")
        
    def salvar_logs(self):
        """Salva todos os logs em arquivo JSON"""
        if not self.salvar_arquivo:
            return
            
        try:
            with open(self.arquivo_debug, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp_debug": self.timestamp,
                    "total_eventos": len(self.logs_debug),
                    "eventos": self.logs_debug
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Debug salvo em: {self.arquivo_debug}")
            print(f"📊 Total de eventos: {len(self.logs_debug)}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar debug: {e}")
    
    def gerar_relatorio_creme(self):
        """Gera relatório específico para eventos do creme de queijo"""
        eventos_creme = [
            evento for evento in self.logs_debug 
            if evento['item_id'] == 2010 or 'creme' in evento['item_nome'].lower()
        ]
        
        print(f"\n📋 RELATÓRIO ESPECÍFICO - CREME DE QUEIJO:")
        print("=" * 60)
        print(f"🔢 Total de eventos relacionados ao creme: {len(eventos_creme)}")
        
        for evento in eventos_creme:
            print(f"\n⏰ {evento['timestamp']}")
            print(f"📂 Categoria: {evento['categoria']}")
            print(f"📝 Dados: {evento['dados']}")
        
        return eventos_creme


# Instância global para usar em todo o sistema
debug_atividades = DebugCriacaoAtividades()


def adicionar_debug_ao_pedido_producao():
    """
    🔧 Adiciona pontos de debug no método _verificar_estoque_suficiente
    e _criar_atividades_recursivas do PedidoDeProducao.
    
    Cole este código no início dos métodos para debug.
    """
    
    codigo_debug_verificar_estoque = '''
    # 🔍 DEBUG - Início verificação de estoque
    debug_atividades.log(
        categoria="VERIFICACAO_ESTOQUE_INICIO",
        item_id=id_item,
        item_nome=f"item_{id_item}",
        dados={
            "quantidade_necessaria": quantidade_necessaria,
            "gestor_disponivel": self.gestor_almoxarifado is not None
        }
    )
    '''
    
    codigo_debug_item_encontrado = '''
    # 🔍 DEBUG - Item encontrado
    debug_atividades.log(
        categoria="ITEM_ENCONTRADO",
        item_id=id_item,
        item_nome=item.descricao,
        dados={
            "politica_enum": str(politica_enum),
            "politica_value": politica_enum.value,
            "estoque_atual": self.gestor_almoxarifado.obter_estoque_atual(id_item)
        }
    )
    '''
    
    codigo_debug_decisao_estoque = '''
    # 🔍 DEBUG - Decisão de estoque
    debug_atividades.log(
        categoria="DECISAO_ESTOQUE",
        item_id=id_item,
        item_nome=item.descricao,
        dados={
            "politica": politica_enum.value,
            "quantidade_necessaria": quantidade_necessaria,
            "estoque_atual": estoque_atual,
            "tem_estoque_suficiente": tem_estoque_suficiente,
            "decisao": "NAO_PRODUZIR" if tem_estoque_suficiente else "PRODUZIR"
        }
    )
    '''
    
    codigo_debug_criar_atividades = '''
    # 🔍 DEBUG - Início criação atividades recursivas
    debug_atividades.log(
        categoria="CRIAR_ATIVIDADES_INICIO",
        item_id=ficha_modular.id_item,
        item_nome=getattr(ficha_modular, 'nome', f'item_{ficha_modular.id_item}'),
        dados={
            "tipo_item": ficha_modular.tipo_item.value,
            "quantidade_requerida": ficha_modular.quantidade_requerida
        }
    )
    '''
    
    codigo_debug_decisao_producao = '''
    # 🔍 DEBUG - Decisão de produção
    debug_atividades.log(
        categoria="DECISAO_PRODUCAO",
        item_id=ficha_modular.id_item,
        item_nome=getattr(ficha_modular, 'nome', f'item_{ficha_modular.id_item}'),
        dados={
            "tipo_item": ficha_modular.tipo_item.value,
            "deve_produzir": deve_produzir,
            "motivo": "PRODUTO_SEMPRE_PRODUZ" if ficha_modular.tipo_item == TipoItem.PRODUTO else "VERIFICACAO_ESTOQUE"
        }
    )
    '''
    
    print("🔧 CÓDIGOS DE DEBUG PARA ADICIONAR:")
    print("=" * 50)
    print("\n📝 1. No início de _verificar_estoque_suficiente:")
    print(codigo_debug_verificar_estoque)
    print("\n📝 2. Após encontrar o item no almoxarifado:")
    print(codigo_debug_item_encontrado)
    print("\n📝 3. Após a decisão de estoque (ESTOCADO/AMBOS):")
    print(codigo_debug_decisao_estoque)
    print("\n📝 4. No início de _criar_atividades_recursivas:")
    print(codigo_debug_criar_atividades)
    print("\n📝 5. Após a decisão deve_produzir:")
    print(codigo_debug_decisao_producao)
    
    return {
        "verificar_estoque_inicio": codigo_debug_verificar_estoque,
        "item_encontrado": codigo_debug_item_encontrado,
        "decisao_estoque": codigo_debug_decisao_estoque,
        "criar_atividades_inicio": codigo_debug_criar_atividades,
        "decisao_producao": codigo_debug_decisao_producao
    }


def criar_versao_debug_pedido_producao():
    """
    🔧 Cria uma versão com debug do método _verificar_estoque_suficiente
    """
    codigo_metodo_debug = '''
def _verificar_estoque_suficiente(self, id_item: int, quantidade_necessaria: float) -> bool:
    """
    ✅ VERSÃO COM DEBUG: Verifica se há estoque suficiente para um item específico.
    """
    # 🔍 DEBUG - Início verificação de estoque
    debug_atividades.log(
        categoria="VERIFICACAO_ESTOQUE_INICIO",
        item_id=id_item,
        item_nome=f"item_{id_item}",
        dados={
            "quantidade_necessaria": quantidade_necessaria,
            "gestor_disponivel": self.gestor_almoxarifado is not None
        }
    )
    
    if not self.gestor_almoxarifado:
        debug_atividades.log(
            categoria="ERRO_GESTOR_INDISPONIVEL",
            item_id=id_item,
            item_nome=f"item_{id_item}",
            dados={"erro": "Gestor almoxarifado não disponível"}
        )
        logger.warning("⚠️ Gestor de almoxarifado não disponível. Assumindo necessidade de produção.")
        return False
    
    try:
        # Buscar item usando método otimizado do gestor
        item = self.gestor_almoxarifado.obter_item_por_id(id_item)
        if not item:
            debug_atividades.log(
                categoria="ERRO_ITEM_NAO_ENCONTRADO",
                item_id=id_item,
                item_nome=f"item_{id_item}",
                dados={"erro": "Item não encontrado no almoxarifado"}
            )
            logger.warning(f"⚠️ Item {id_item} não encontrado no almoxarifado")
            return False
        
        # ✅ CORREÇÃO: Usar ENUM diretamente, não string
        politica_enum = item.politica_producao
        
        # 🔍 DEBUG - Item encontrado
        debug_atividades.log(
            categoria="ITEM_ENCONTRADO",
            item_id=id_item,
            item_nome=item.descricao,
            dados={
                "politica_enum": str(politica_enum),
                "politica_value": politica_enum.value,
                "estoque_atual": self.gestor_almoxarifado.obter_estoque_atual(id_item),
                "tipo_politica": type(politica_enum).__name__
            }
        )
        
        # Para SOB_DEMANDA: sempre produzir (não verificar estoque)
        if politica_enum == PoliticaProducao.SOB_DEMANDA:
            debug_atividades.log(
                categoria="DECISAO_SOB_DEMANDA",
                item_id=id_item,
                item_nome=item.descricao,
                dados={
                    "decisao": "SEMPRE_PRODUZIR",
                    "motivo": "Política SOB_DEMANDA"
                }
            )
            logger.debug(
                f"🔄 Item '{item.descricao}' (ID {id_item}) é SOB_DEMANDA. "
                f"Produção será realizada independente do estoque."
            )
            return False  # Retorna False para forçar produção
        
        # Para ESTOCADO e AMBOS: verificar estoque atual
        if politica_enum in [PoliticaProducao.ESTOCADO, PoliticaProducao.AMBOS]:
            tem_estoque_suficiente = self.gestor_almoxarifado.verificar_estoque_atual_suficiente(
                id_item, quantidade_necessaria
            )
            
            estoque_atual = self.gestor_almoxarifado.obter_estoque_atual(id_item)
            
            # 🔍 DEBUG - Decisão de estoque
            debug_atividades.log(
                categoria="DECISAO_ESTOQUE",
                item_id=id_item,
                item_nome=item.descricao,
                dados={
                    "politica": politica_enum.value,
                    "quantidade_necessaria": quantidade_necessaria,
                    "estoque_atual": estoque_atual,
                    "tem_estoque_suficiente": tem_estoque_suficiente,
                    "decisao": "NAO_PRODUZIR" if tem_estoque_suficiente else "PRODUZIR"
                }
            )
            
            logger.info(
                f"📦 Item '{item.descricao}' (ID {id_item}): "
                f"Estoque atual: {estoque_atual} | "
                f"Necessário: {quantidade_necessaria} | "
                f"Política: {politica_enum.value} | "
                f"Suficiente: {'✅' if tem_estoque_suficiente else '❌'}"
            )
            
            return tem_estoque_suficiente
        
        # Política desconhecida - assumir necessidade de produção
        debug_atividades.log(
            categoria="POLITICA_DESCONHECIDA",
            item_id=id_item,
            item_nome=item.descricao,
            dados={
                "politica_desconhecida": str(politica_enum),
                "decisao": "PRODUZIR_POR_SEGURANCA"
            }
        )
        logger.warning(f"⚠️ Política de produção desconhecida '{politica_enum}' para item {id_item}")
        return False
        
    except Exception as e:
        debug_atividades.log(
            categoria="ERRO_EXCECAO",
            item_id=id_item,
            item_nome=f"item_{id_item}",
            dados={
                "erro": str(e),
                "tipo_erro": type(e).__name__
            }
        )
        logger.warning(f"⚠️ Erro ao verificar estoque do item {id_item}: {e}")
        return False
'''
    
    print("📝 MÉTODO _verificar_estoque_suficiente COM DEBUG COMPLETO:")
    print("=" * 60)
    print(codigo_metodo_debug)
    
    return codigo_metodo_debug


if __name__ == "__main__":
    print("🔍 SISTEMA DE DEBUG PARA CRIAÇÃO DE ATIVIDADES")
    print("=" * 50)
    
    # Gerar códigos de debug
    adicionar_debug_ao_pedido_producao()
    
    print("\n" + "="*50)
    print("💡 INSTRUÇÕES:")
    print("1. Adicione os códigos de debug nos métodos indicados")
    print("2. Execute o pedido 777")
    print("3. Execute: debug_atividades.salvar_logs()")
    print("4. Execute: debug_atividades.gerar_relatorio_creme()")
    print("5. Analise o arquivo JSON gerado para identificar o problema")
    print("="*50)