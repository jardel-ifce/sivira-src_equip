"""
Gerenciador de Pedidos
=====================

Módulo responsável por registrar, validar e gerenciar pedidos de produção.
Adaptado para trabalhar com TesteSistemaProducao diretamente.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from enums.producao.tipo_item import TipoItem


@dataclass
class DadosPedidoMenu:
    """Dados de um pedido registrado pelo menu"""
    id_pedido: int
    id_item: int
    tipo_item: str  # "PRODUTO" ou "SUBPRODUTO"
    quantidade: int
    fim_jornada: datetime
    inicio_jornada: datetime
    arquivo_atividades: str
    nome_item: str
    registrado_em: datetime


class GerenciadorPedidos:
    """Gerencia registros de pedidos para produção"""
    
    def __init__(self):
        self.pedidos: List[DadosPedidoMenu] = []
        self.contador_id = 1
        
        # Diretórios dos arquivos de atividades
        self.dir_produtos = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/produtos/atividades"
        self.dir_subprodutos = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/subprodutos/atividades"
        
        # Arquivo para persistência
        self.arquivo_pedidos = "menu/pedidos_salvos.json"
        
        # Carrega pedidos salvos se existirem
        self.carregar_pedidos()
    
    def registrar_pedido(self, id_item: int, tipo_item: str, quantidade: int, 
                        fim_jornada: datetime) -> Tuple[bool, str]:
        """
        Registra um novo pedido.
        
        Args:
            id_item: ID do item (ex: 1001)
            tipo_item: "PRODUTO" ou "SUBPRODUTO"
            quantidade: Quantidade a produzir
            fim_jornada: Data/hora fim da jornada
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            # Valida parâmetros
            if quantidade <= 0:
                return False, "Quantidade deve ser maior que zero"
            
            if tipo_item not in ["PRODUTO", "SUBPRODUTO"]:
                return False, "Tipo deve ser PRODUTO ou SUBPRODUTO"
            
            # Calcula início da jornada (3 dias antes - como nos scripts)
            inicio_jornada = fim_jornada - timedelta(days=3)
            
            # Verifica se arquivo de atividades existe
            arquivo_atividades = self._encontrar_arquivo_atividades(id_item, tipo_item)
            if not arquivo_atividades:
                return False, f"Arquivo de atividades não encontrado para ID {id_item} tipo {tipo_item}"
            
            # Extrai nome do item do arquivo
            nome_item = self._extrair_nome_do_arquivo(arquivo_atividades)
            
            # Cria o pedido
            pedido = DadosPedidoMenu(
                id_pedido=self.contador_id,
                id_item=id_item,
                tipo_item=tipo_item,
                quantidade=quantidade,
                fim_jornada=fim_jornada,
                inicio_jornada=inicio_jornada,
                arquivo_atividades=arquivo_atividades,
                nome_item=nome_item,
                registrado_em=datetime.now()
            )
            
            # Adiciona à lista
            self.pedidos.append(pedido)
            self.contador_id += 1
            
            return True, f"Pedido {pedido.id_pedido} registrado: {nome_item} ({quantidade} uni)"
            
        except Exception as e:
            return False, f"Erro ao registrar pedido: {e}"
    
    def _encontrar_arquivo_atividades(self, id_item: int, tipo_item: str) -> Optional[str]:
        """Encontra arquivo de atividades para o item"""
        
        # Define diretório baseado no tipo
        if tipo_item == "PRODUTO":
            diretorio = self.dir_produtos
        else:
            diretorio = self.dir_subprodutos
        
        # Verifica se diretório existe
        if not os.path.exists(diretorio):
            return None
        
        # Procura arquivo com padrão ID_*.json
        padrao = f"{id_item}_"
        
        for arquivo in os.listdir(diretorio):
            if arquivo.startswith(padrao) and arquivo.endswith(".json"):
                caminho_completo = os.path.join(diretorio, arquivo)
                return caminho_completo
        
        return None
    
    def _extrair_nome_do_arquivo(self, caminho_arquivo: str) -> str:
        """Extrai nome do item do nome do arquivo"""
        nome_arquivo = os.path.basename(caminho_arquivo)
        # Remove extensão
        nome_sem_ext = nome_arquivo.replace(".json", "")
        # Remove ID_ do início
        if "_" in nome_sem_ext:
            partes = nome_sem_ext.split("_", 1)
            if len(partes) > 1:
                return partes[1].replace("_", " ").title()
        
        return nome_sem_ext
    
    def listar_pedidos(self):
        """Lista todos os pedidos registrados"""
        if not self.pedidos:
            print("📭 Nenhum pedido registrado.")
            return
        
        print(f"📋 {len(self.pedidos)} pedido(s) registrado(s):")
        
        # Debug: verifica duplicatas
        ids_pedidos = [p.id_pedido for p in self.pedidos]
        if len(set(ids_pedidos)) != len(ids_pedidos):
            print(f"⚠️ ATENÇÃO: Detectadas duplicatas nos IDs: {ids_pedidos}")
        
        print()
        
        for pedido in self.pedidos:
            print(f"🎯 Pedido {pedido.id_pedido}")
            print(f"   📦 Item: {pedido.nome_item} (ID: {pedido.id_item})")
            print(f"   📝 Tipo: {pedido.tipo_item}")
            print(f"   📊 Quantidade: {pedido.quantidade}")
            print(f"   ⏰ Jornada: {pedido.inicio_jornada.strftime('%d/%m/%Y %H:%M')} → {pedido.fim_jornada.strftime('%d/%m/%Y %H:%M')}")
            print(f"   📅 Registrado: {pedido.registrado_em.strftime('%d/%m/%Y %H:%M:%S')}")
            print()
    
    def remover_pedido(self, id_pedido: int) -> Tuple[bool, str]:
        """Remove um pedido específico"""
        for i, pedido in enumerate(self.pedidos):
            if pedido.id_pedido == id_pedido:
                nome_item = pedido.nome_item
                del self.pedidos[i]
                return True, f"Pedido {id_pedido} ({nome_item}) removido com sucesso"
        
        return False, f"Pedido {id_pedido} não encontrado"
    
    def limpar_pedidos(self):
        """Remove todos os pedidos"""
        total = len(self.pedidos)
        self.pedidos.clear()
        self.contador_id = 1
        print(f"✅ {total} pedido(s) removido(s)")
    
    def obter_pedido(self, id_pedido: int) -> Optional[DadosPedidoMenu]:
        """Obtém um pedido específico"""
        for pedido in self.pedidos:
            if pedido.id_pedido == id_pedido:
                return pedido
        return None
    
    def salvar_pedidos(self):
        """Salva pedidos em arquivo JSON"""
        try:
            # Cria diretório se não existir
            os.makedirs(os.path.dirname(self.arquivo_pedidos), exist_ok=True)
            
            # Converte pedidos para dicionários
            dados_para_salvar = []
            for pedido in self.pedidos:
                dados = asdict(pedido)
                # Converte datetime para string
                dados['fim_jornada'] = pedido.fim_jornada.isoformat()
                dados['inicio_jornada'] = pedido.inicio_jornada.isoformat()
                dados['registrado_em'] = pedido.registrado_em.isoformat()
                dados_para_salvar.append(dados)
            
            # Salva arquivo
            with open(self.arquivo_pedidos, 'w', encoding='utf-8') as f:
                json.dump({
                    'pedidos': dados_para_salvar,
                    'contador_id': self.contador_id,
                    'salvo_em': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 {len(self.pedidos)} pedido(s) salvo(s) em {self.arquivo_pedidos}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar pedidos: {e}")
    
    def carregar_pedidos(self):
        """Carrega pedidos salvos do arquivo JSON"""
        try:
            if not os.path.exists(self.arquivo_pedidos):
                return
            
            with open(self.arquivo_pedidos, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Restaura pedidos
            self.pedidos.clear()
            for dados_pedido in dados.get('pedidos', []):
                # Converte strings de volta para datetime
                dados_pedido['fim_jornada'] = datetime.fromisoformat(dados_pedido['fim_jornada'])
                dados_pedido['inicio_jornada'] = datetime.fromisoformat(dados_pedido['inicio_jornada'])
                dados_pedido['registrado_em'] = datetime.fromisoformat(dados_pedido['registrado_em'])
                
                pedido = DadosPedidoMenu(**dados_pedido)
                self.pedidos.append(pedido)
            
            # Restaura contador
            self.contador_id = dados.get('contador_id', 1)
            
            if self.pedidos:
                print(f"📂 {len(self.pedidos)} pedido(s) carregado(s) de {self.arquivo_pedidos}")
            
        except Exception as e:
            print(f"⚠️ Não foi possível carregar pedidos salvos: {e}")
    
    def validar_item_existe(self, id_item: int, tipo_item: str) -> Tuple[bool, str]:
        """
        Valida se um item existe nos arquivos de atividades.
        
        Args:
            id_item: ID do item
            tipo_item: "PRODUTO" ou "SUBPRODUTO"
            
        Returns:
            Tuple[bool, str]: (existe, nome_do_arquivo_ou_erro)
        """
        arquivo = self._encontrar_arquivo_atividades(id_item, tipo_item)
        
        if arquivo:
            nome = self._extrair_nome_do_arquivo(arquivo)
            return True, nome
        else:
            return False, f"Item {id_item} não encontrado em {tipo_item}S"
    
    def listar_itens_disponiveis(self, tipo_item: str) -> List[Tuple[int, str]]:
        """
        Lista itens disponíveis de um tipo.
        
        Args:
            tipo_item: "PRODUTO" ou "SUBPRODUTO"
            
        Returns:
            List[Tuple[int, str]]: Lista de (id, nome)
        """
        if tipo_item == "PRODUTO":
            diretorio = self.dir_produtos
        else:
            diretorio = self.dir_subprodutos
        
        itens = []
        
        try:
            if os.path.exists(diretorio):
                for arquivo in os.listdir(diretorio):
                    if arquivo.endswith(".json"):
                        # Extrai ID do nome do arquivo
                        try:
                            id_item = int(arquivo.split("_")[0])
                            nome = self._extrair_nome_do_arquivo(os.path.join(diretorio, arquivo))
                            itens.append((id_item, nome))
                        except (ValueError, IndexError):
                            continue
                
                # Ordena por ID
                itens.sort(key=lambda x: x[0])
        
        except Exception as e:
            print(f"❌ Erro ao listar itens de {tipo_item}: {e}")
        
        return itens
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas dos pedidos registrados"""
        if not self.pedidos:
            return {"total": 0}
        
        # Contadores por tipo
        produtos = sum(1 for p in self.pedidos if p.tipo_item == "PRODUTO")
        subprodutos = sum(1 for p in self.pedidos if p.tipo_item == "SUBPRODUTO")
        
        # Quantidade total
        quantidade_total = sum(p.quantidade for p in self.pedidos)
        
        # Estatísticas temporais
        inicio_mais_cedo = min(p.inicio_jornada for p in self.pedidos)
        fim_mais_tarde = max(p.fim_jornada for p in self.pedidos)
        duracao_total = fim_mais_tarde - inicio_mais_cedo
        
        return {
            "total": len(self.pedidos),
            "produtos": produtos,
            "subprodutos": subprodutos,
            "quantidade_total": quantidade_total,
            "inicio_mais_cedo": inicio_mais_cedo,
            "fim_mais_tarde": fim_mais_tarde,
            "duracao_total": duracao_total
        }