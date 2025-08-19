"""
Conversor de Pedidos - IMPLEMENTADO  
===================================

Converte pedidos do menu para sistema de produção real.
"""

from typing import List, Optional
from menu.gerenciador_pedidos import DadosPedidoMenu


class ConversorPedidos:
    """
    Conversor de pedidos do menu para sistema de produção.
    
    Responsabilidades:
    - Conversão DadosPedidoMenu → PedidoDeProducao
    - Validações de dados
    - Mapeamento de IDs
    """
    
    def __init__(self, gestor_almoxarifado=None):
        """
        Inicializa conversor.
        
        Args:
            gestor_almoxarifado: Gestor do almoxarifado
        """
        self.gestor_almoxarifado = gestor_almoxarifado
        print("🔄 ConversorPedidos criado")
    
    def converter_pedidos(self, pedidos_menu: List[DadosPedidoMenu]) -> Optional[List]:
        """
        Converte pedidos do menu para formato do sistema REAL.
        
        Args:
            pedidos_menu: Lista de pedidos do menu
            
        Returns:
            List: Pedidos convertidos ou None se erro
        """
        try:
            print(f"🔄 Convertendo {len(pedidos_menu)} pedidos para sistema real...")
            
            # ✅ IMPORTA SISTEMA REAL
            print("   📦 Importando módulos do sistema...")
            from models.atividades.pedido_de_producao import PedidoDeProducao
            from enums.producao.tipo_item import TipoItem
            from factory.fabrica_funcionarios import funcionarios_disponiveis
            
            pedidos_convertidos = []
            
            for dados_pedido in pedidos_menu:
                print(f"   📦 Convertendo: {dados_pedido.nome_item} ({dados_pedido.quantidade} uni)")
                
                try:
                    # ✅ CONVERSÃO DE TIPO
                    if dados_pedido.tipo_item == "PRODUTO":
                        tipo_item = TipoItem.PRODUTO
                    elif dados_pedido.tipo_item == "SUBPRODUTO":
                        tipo_item = TipoItem.SUBPRODUTO
                    else:
                        print(f"     ❌ Tipo inválido: {dados_pedido.tipo_item}")
                        continue
                    
                    print(f"     🔹 ID: {dados_pedido.id_item}")
                    print(f"     🔹 Tipo: {tipo_item.name}")
                    print(f"     🔹 Quantidade: {dados_pedido.quantidade}")
                    print(f"     🔹 Jornada: {dados_pedido.inicio_jornada.strftime('%d/%m %H:%M')} → {dados_pedido.fim_jornada.strftime('%d/%m %H:%M')}")
                    
                    # ✅ CRIA PEDIDO REAL
                    pedido = PedidoDeProducao(
                        id_ordem=dados_pedido.id_ordem, 
                        id_pedido=dados_pedido.id_pedido,
                        id_produto=dados_pedido.id_item,
                        tipo_item=tipo_item,
                        quantidade=dados_pedido.quantidade,
                        inicio_jornada=dados_pedido.inicio_jornada,
                        fim_jornada=dados_pedido.fim_jornada,
                        todos_funcionarios=funcionarios_disponiveis,
                        gestor_almoxarifado=self.gestor_almoxarifado
                    )
                    
                    # ✅ MONTA ESTRUTURA (CRÍTICO!)
                    print(f"     🏗️ Montando estrutura técnica...")
                    pedido.montar_estrutura()
                    print(f"     ✅ Estrutura montada: {len(pedido.funcionarios_elegiveis)} funcionários elegíveis")
                    
                    pedidos_convertidos.append(pedido)
                    print(f"     ✅ Pedido {dados_pedido.id_pedido} convertido com sucesso!")
                    
                except Exception as e:
                    print(f"     ❌ Erro ao converter pedido {dados_pedido.id_pedido}: {e}")
                    # Continue com próximos pedidos
                    continue
            
            print(f"✅ {len(pedidos_convertidos)}/{len(pedidos_menu)} pedido(s) convertido(s) com sucesso")
            
            if len(pedidos_convertidos) == 0:
                print("❌ Nenhum pedido foi convertido com sucesso!")
                return None
            
            return pedidos_convertidos
            
        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
            print("💡 Verifique se está executando do diretório correto")
            return None
            
        except Exception as e:
            print(f"❌ Erro geral na conversão: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def validar_pedido(self, pedido: DadosPedidoMenu) -> bool:
        """
        Valida um pedido individual.
        
        Args:
            pedido: Pedido a validar
            
        Returns:
            bool: True se válido
        """
        try:
            print(f"🔍 Validando pedido: {pedido.nome_item}")
            
            # Validações básicas
            if pedido.quantidade <= 0:
                print(f"     ❌ Quantidade inválida: {pedido.quantidade}")
                return False
            
            if pedido.tipo_item not in ["PRODUTO", "SUBPRODUTO"]:
                print(f"     ❌ Tipo inválido: {pedido.tipo_item}")
                return False
            
            if pedido.fim_jornada <= pedido.inicio_jornada:
                print(f"     ❌ Datas inválidas: fim antes do início")
                return False
            
            # Verifica se arquivo de atividades existe
            import os
            if not os.path.exists(pedido.arquivo_atividades):
                print(f"     ❌ Arquivo de atividades não encontrado: {pedido.arquivo_atividades}")
                return False
            
            print(f"     ✅ Pedido válido")
            return True
            
        except Exception as e:
            print(f"     ❌ Erro na validação: {e}")
            return False
    
    def validar_todos_pedidos(self, pedidos_menu: List[DadosPedidoMenu]) -> tuple[bool, List[str]]:
        """
        Valida todos os pedidos.
        
        Args:
            pedidos_menu: Lista de pedidos
            
        Returns:
            tuple[bool, List[str]]: (todos_válidos, lista_de_erros)
        """
        print(f"🔍 Validando {len(pedidos_menu)} pedidos...")
        
        erros = []
        pedidos_validos = 0
        
        for pedido in pedidos_menu:
            if self.validar_pedido(pedido):
                pedidos_validos += 1
            else:
                erros.append(f"Pedido {pedido.id_pedido} ({pedido.nome_item}) inválido")
        
        todos_validos = len(erros) == 0
        
        print(f"📊 Resultado: {pedidos_validos}/{len(pedidos_menu)} pedidos válidos")
        
        if erros:
            print("❌ Erros encontrados:")
            for erro in erros:
                print(f"   • {erro}")
        
        return todos_validos, erros
    
    def obter_estatisticas_conversao(self, pedidos_menu: List[DadosPedidoMenu], 
                                   pedidos_convertidos: Optional[List]) -> dict:
        """
        Retorna estatísticas da conversão.
        
        Args:
            pedidos_menu: Pedidos originais
            pedidos_convertidos: Pedidos convertidos
            
        Returns:
            dict: Estatísticas
        """
        total_original = len(pedidos_menu)
        total_convertido = len(pedidos_convertidos) if pedidos_convertidos else 0
        taxa_sucesso = (total_convertido / total_original * 100) if total_original > 0 else 0
        
        # Análise por tipo
        tipos_original = {}
        for pedido in pedidos_menu:
            tipos_original[pedido.tipo_item] = tipos_original.get(pedido.tipo_item, 0) + 1
        
        return {
            "total_original": total_original,
            "total_convertido": total_convertido,
            "taxa_sucesso": taxa_sucesso,
            "tipos_original": tipos_original,
            "tem_gestor_almoxarifado": self.gestor_almoxarifado is not None
        }