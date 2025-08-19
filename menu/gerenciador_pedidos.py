"""
Gerenciador de Pedidos
=====================

Módulo responsável por registrar, validar e gerenciar pedidos de produção.
Adaptado para trabalhar com TesteSistemaProducao diretamente.

🆕 NOVIDADES:
- Sistema de Ordens/Sessões
- Agrupamento de pedidos por ordem
- Incremento automático após execução
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
    id_ordem: int  # 🆕 Adicionado controle de ordem
    id_item: int
    tipo_item: str  # "PRODUTO" ou "SUBPRODUTO"
    quantidade: int
    fim_jornada: datetime
    inicio_jornada: datetime
    arquivo_atividades: str
    nome_item: str
    registrado_em: datetime


class GerenciadorPedidos:
    """Gerencia registros de pedidos para produção com sistema de ordens"""
    
    def __init__(self):
        self.pedidos: List[DadosPedidoMenu] = []
        self.contador_pedido = 1  # Contador de pedidos dentro da ordem atual
        self.ordem_atual = 1      # 🆕 Ordem/sessão atual
        
        # Diretórios dos arquivos de atividades
        self.dir_produtos = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/produtos/atividades"
        self.dir_subprodutos = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/subprodutos/atividades"
        
        # Arquivo para persistência
        self.arquivo_pedidos = "data/pedidos/pedidos_salvos.json"  # 🆕 Movido para data/pedidos
        
        # Carrega pedidos salvos se existirem
        self.carregar_pedidos()
    
    def registrar_pedido(self, id_item: int, tipo_item: str, quantidade: int, 
                        fim_jornada: datetime) -> Tuple[bool, str]:
        """
        Registra um novo pedido na ordem atual.
        
        Args:
            id_item: ID do item (ex: 1001)
            tipo_item: "PRODUTO" ou "SUBPRODUTO"
            quantidade: Quantidade a produzir
            fim_jornada: Data/hora fim da jornada
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            # 🆕 Debug: Mostra estado atual
            print(f"🔍 DEBUG: Ordem atual = {self.ordem_atual}, Contador pedido = {self.contador_pedido}")
            
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
            
            # 🆕 Cria o pedido com ordem atual
            pedido = DadosPedidoMenu(
                id_pedido=self.contador_pedido,
                id_ordem=self.ordem_atual,  # Usa ordem atual
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
            
            # 🆕 Debug: Confirma criação
            print(f"🔍 DEBUG: Pedido criado - Ordem {pedido.id_ordem} | Pedido {pedido.id_pedido}")
            
            # Incrementa contador APÓS criar o pedido
            self.contador_pedido += 1
            
            return True, f"Ordem {pedido.id_ordem} | Pedido {pedido.id_pedido}: {nome_item} ({quantidade} uni)"
            
        except Exception as e:
            return False, f"Erro ao registrar pedido: {e}"
    
    def incrementar_ordem(self) -> int:
        """
        🆕 Incrementa a ordem atual e reseta contador de pedidos.
        Chamado após QUALQUER tentativa de execução (sucesso OU falha).
        
        Isso evita conflitos de IDs entre ordens que falharam e novas ordens.
        
        Returns:
            int: Nova ordem atual
        """
        print(f"🔍 DEBUG: Incrementando ordem de {self.ordem_atual} para {self.ordem_atual + 1}")
        print(f"💡 MOTIVO: Evitar conflitos de IDs (ordem incrementa sempre após execução)")
        
        self.ordem_atual += 1
        self.contador_pedido = 1  # Reseta contador de pedidos para nova ordem
        
        print(f"📈 Ordem incrementada para: {self.ordem_atual}")
        print(f"🔄 Contador de pedidos resetado para: {self.contador_pedido}")
        return self.ordem_atual
    
    def obter_ordem_atual(self) -> int:
        """🆕 Retorna a ordem atual"""
        return self.ordem_atual
    
    def obter_pedidos_ordem_atual(self) -> List[DadosPedidoMenu]:
        """🆕 Retorna apenas pedidos da ordem atual"""
        return [p for p in self.pedidos if p.id_ordem == self.ordem_atual]
    
    def obter_pedidos_por_ordem(self, ordem: int) -> List[DadosPedidoMenu]:
        """🆕 Retorna pedidos de uma ordem específica"""
        return [p for p in self.pedidos if p.id_ordem == ordem]
    
    def verificar_estrutura_diretorios(self) -> Dict:
        """🆕 Verifica se a estrutura de diretórios está correta"""
        diretorios = {
            "produtos": self.dir_produtos,
            "subprodutos": self.dir_subprodutos,
            "pedidos_salvos": os.path.dirname(self.arquivo_pedidos)
        }
        
        resultado = {}
        
        for nome, caminho in diretorios.items():
            resultado[nome] = {
                "caminho": caminho,
                "existe": os.path.exists(caminho),
                "eh_diretorio": os.path.isdir(caminho) if os.path.exists(caminho) else False
            }
            
            # Informações adicionais para diretório de pedidos
            if nome == "pedidos_salvos":
                arquivo_pedidos_existe = os.path.exists(self.arquivo_pedidos)
                resultado[nome]["arquivo_pedidos_existe"] = arquivo_pedidos_existe
                if arquivo_pedidos_existe:
                    try:
                        stat = os.stat(self.arquivo_pedidos)
                        resultado[nome]["tamanho_arquivo"] = stat.st_size
                        resultado[nome]["modificado_em"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    except Exception as e:
                        resultado[nome]["erro_stat"] = str(e)
        
        return resultado
    
    def limpar_arquivo_pedidos_salvos(self):
        """🆕 Remove arquivo de pedidos salvos se existir"""
        try:
            if os.path.exists(self.arquivo_pedidos):
                os.remove(self.arquivo_pedidos)
                print(f"🗑️ Arquivo de pedidos salvos removido: {self.arquivo_pedidos}")
                return True
            else:
                print(f"📄 Arquivo de pedidos salvos não existe: {self.arquivo_pedidos}")
                return False
        except Exception as e:
            print(f"⚠️ Erro ao remover arquivo de pedidos salvos: {e}")
            return False
    
    def debug_sistema_ordens(self):
        """🆕 Método de debug para verificar estado do sistema de ordens"""
        print("🔍 DEBUG - ESTADO DO SISTEMA DE ORDENS")
        print("=" * 50)
        print(f"Ordem atual: {self.ordem_atual}")
        print(f"Contador pedido: {self.contador_pedido}")
        print(f"Total de pedidos: {len(self.pedidos)}")
        
        if self.pedidos:
            print(f"Ordens existentes: {self.listar_ordens_existentes()}")
            print(f"Pedidos na ordem atual: {len(self.obter_pedidos_ordem_atual())}")
            
            print("\nTodos os pedidos:")
            for p in self.pedidos:
                print(f"  Ordem {p.id_ordem} | Pedido {p.id_pedido}: {p.nome_item}")
        else:
            print("Nenhum pedido registrado")
        print("=" * 50)
    
    def listar_ordens_existentes(self) -> List[int]:
        """🆕 Lista todas as ordens que possuem pedidos"""
        ordens = set(p.id_ordem for p in self.pedidos)
        return sorted(ordens)
    
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
        """Lista todos os pedidos registrados, agrupados por ordem"""
        if not self.pedidos:
            print("📭 Nenhum pedido registrado.")
            return
        
        # 🆕 Agrupa pedidos por ordem
        ordens = self.listar_ordens_existentes()
        
        print(f"📋 {len(self.pedidos)} pedido(s) registrado(s) em {len(ordens)} ordem(ns):")
        
        # Debug: verifica duplicatas
        ids_completos = [(p.id_ordem, p.id_pedido) for p in self.pedidos]
        if len(set(ids_completos)) != len(ids_completos):
            print(f"⚠️ ATENÇÃO: Detectadas duplicatas nos IDs: {ids_completos}")
        
        print()
        
        # 🆕 Lista por ordem
        for ordem in ordens:
            pedidos_ordem = self.obter_pedidos_por_ordem(ordem)
            status_ordem = "🎯 ATUAL" if ordem == self.ordem_atual else "✅ EXECUTADA"
            
            print(f"📦 ORDEM {ordem} ({len(pedidos_ordem)} pedidos) - {status_ordem}")
            print("─" * 50)
            
            for pedido in pedidos_ordem:
                print(f"   🎯 Ordem {pedido.id_ordem} | Pedido {pedido.id_pedido}")
                print(f"      📦 Item: {pedido.nome_item} (ID: {pedido.id_item})")
                print(f"      🏷️ Tipo: {pedido.tipo_item}")
                print(f"      📊 Quantidade: {pedido.quantidade}")
                print(f"      ⏰ Jornada: {pedido.inicio_jornada.strftime('%d/%m/%Y %H:%M')} → {pedido.fim_jornada.strftime('%d/%m/%Y %H:%M')}")
                print(f"      📅 Registrado: {pedido.registrado_em.strftime('%d/%m/%Y %H:%M:%S')}")
                print()
            
            print()
    
    def remover_pedido(self, id_ordem: int, id_pedido: int) -> Tuple[bool, str]:
        """🆕 Remove um pedido específico usando Ordem e Pedido"""
        for i, pedido in enumerate(self.pedidos):
            if pedido.id_ordem == id_ordem and pedido.id_pedido == id_pedido:
                nome_item = pedido.nome_item
                del self.pedidos[i]
                return True, f"Ordem {id_ordem} | Pedido {id_pedido} ({nome_item}) removido com sucesso"
        
        return False, f"Ordem {id_ordem} | Pedido {id_pedido} não encontrado"
    
    def remover_pedido_legado(self, id_pedido: int) -> Tuple[bool, str]:
        """Remove pedido usando apenas ID (para compatibilidade)"""
        # Tenta encontrar na ordem atual primeiro
        pedidos_atuais = self.obter_pedidos_ordem_atual()
        for pedido in pedidos_atuais:
            if pedido.id_pedido == id_pedido:
                return self.remover_pedido(pedido.id_ordem, pedido.id_pedido)
        
        # Se não encontrou, procura em todas as ordens
        for pedido in self.pedidos:
            if pedido.id_pedido == id_pedido:
                return self.remover_pedido(pedido.id_ordem, pedido.id_pedido)
        
        return False, f"Pedido {id_pedido} não encontrado"
    
    def limpar_pedidos(self):
        """Remove todos os pedidos"""
        total = len(self.pedidos)
        self.pedidos.clear()
        self.contador_pedido = 1
        # 🆕 NÃO reseta ordem_atual - mantém continuidade
        print(f"✅ {total} pedido(s) removido(s)")
        print(f"📋 Ordem atual mantida: {self.ordem_atual}")
    
    def limpar_ordem_atual(self):
        """🆕 Remove apenas pedidos da ordem atual"""
        pedidos_atuais = self.obter_pedidos_ordem_atual()
        total = len(pedidos_atuais)
        
        # Remove pedidos da ordem atual
        self.pedidos = [p for p in self.pedidos if p.id_ordem != self.ordem_atual]
        
        # Reseta contador de pedidos
        self.contador_pedido = 1
        
        print(f"✅ {total} pedido(s) da Ordem {self.ordem_atual} removido(s)")
    
    def obter_pedido(self, id_ordem: int, id_pedido: int) -> Optional[DadosPedidoMenu]:
        """🆕 Obtém um pedido específico usando Ordem e Pedido"""
        for pedido in self.pedidos:
            if pedido.id_ordem == id_ordem and pedido.id_pedido == id_pedido:
                return pedido
        return None
    
    def obter_pedido_legado(self, id_pedido: int) -> Optional[DadosPedidoMenu]:
        """Obtém pedido usando apenas ID (busca na ordem atual primeiro)"""
        # Procura na ordem atual primeiro
        for pedido in self.obter_pedidos_ordem_atual():
            if pedido.id_pedido == id_pedido:
                return pedido
        
        # Se não encontrou, procura em todas
        for pedido in self.pedidos:
            if pedido.id_pedido == id_pedido:
                return pedido
        
        return None
    
    def salvar_pedidos(self):
        """Salva pedidos em arquivo JSON com informações de ordem"""
        try:
            # Cria diretório se não existir
            diretorio = os.path.dirname(self.arquivo_pedidos)
            os.makedirs(diretorio, exist_ok=True)
            print(f"📁 Diretório de pedidos: {diretorio}")
            
            # Converte pedidos para dicionários
            dados_para_salvar = []
            for pedido in self.pedidos:
                dados = asdict(pedido)
                # Converte datetime para string
                dados['fim_jornada'] = pedido.fim_jornada.isoformat()
                dados['inicio_jornada'] = pedido.inicio_jornada.isoformat()
                dados['registrado_em'] = pedido.registrado_em.isoformat()
                dados_para_salvar.append(dados)
            
            # 🆕 Salva com informações de ordem
            dados_completos = {
                'pedidos': dados_para_salvar,
                'contador_pedido': self.contador_pedido,
                'ordem_atual': self.ordem_atual,  # Salva ordem atual
                'total_ordens': len(self.listar_ordens_existentes()),
                'salvo_em': datetime.now().isoformat(),
                'versao': '2.0_com_ordens'  # Marca versão
            }
            
            # Salva arquivo
            with open(self.arquivo_pedidos, 'w', encoding='utf-8') as f:
                json.dump(dados_completos, f, indent=2, ensure_ascii=False)
            
            print(f"💾 {len(self.pedidos)} pedido(s) salvo(s) em {self.arquivo_pedidos}")
            print(f"📦 Ordem atual: {self.ordem_atual}")
            
        except Exception as e:
            print(f"⌨ Erro ao salvar pedidos: {e}")
    
    def carregar_pedidos(self):
        """Carrega pedidos salvos do arquivo JSON com suporte a ordens"""
        try:
            if not os.path.exists(self.arquivo_pedidos):
                return
            
            with open(self.arquivo_pedidos, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # 🆕 Verifica se tem informações de ordem
            if 'ordem_atual' in dados:
                # Formato novo com ordens
                self.ordem_atual = dados.get('ordem_atual', 1)
                print(f"📦 Carregando com sistema de ordens - Ordem atual: {self.ordem_atual}")
            else:
                # Formato antigo - migra para sistema de ordens
                print("🔄 Migrando pedidos antigos para sistema de ordens...")
                self.ordem_atual = 1
            
            # Restaura pedidos
            self.pedidos.clear()
            for dados_pedido in dados.get('pedidos', []):
                # Converte strings de volta para datetime
                dados_pedido['fim_jornada'] = datetime.fromisoformat(dados_pedido['fim_jornada'])
                dados_pedido['inicio_jornada'] = datetime.fromisoformat(dados_pedido['inicio_jornada'])
                dados_pedido['registrado_em'] = datetime.fromisoformat(dados_pedido['registrado_em'])
                
                # 🆕 Garante que tenha id_ordem
                if 'id_ordem' not in dados_pedido:
                    dados_pedido['id_ordem'] = 1  # Migração: coloca todos na ordem 1
                
                pedido = DadosPedidoMenu(**dados_pedido)
                self.pedidos.append(pedido)
            
            # 🆕 Ajusta contador baseado na ordem atual
            pedidos_ordem_atual = self.obter_pedidos_ordem_atual()
            if pedidos_ordem_atual:
                # Se tem pedidos na ordem atual, próximo pedido é max + 1
                max_pedido_atual = max(p.id_pedido for p in pedidos_ordem_atual)
                self.contador_pedido = max_pedido_atual + 1
            else:
                # Se não tem pedidos na ordem atual, começa do 1
                self.contador_pedido = 1
            
            if self.pedidos:
                ordens_existentes = self.listar_ordens_existentes()
                print(f"📂 {len(self.pedidos)} pedido(s) carregado(s) de {self.arquivo_pedidos}")
                print(f"📦 Ordens existentes: {ordens_existentes}")
                print(f"🎯 Ordem atual: {self.ordem_atual}")
            
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
            print(f"⌨ Erro ao listar itens de {tipo_item}: {e}")
        
        return itens
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas dos pedidos registrados com informações de ordem"""
        if not self.pedidos:
            return {"total": 0, "ordem_atual": self.ordem_atual}
        
        # Estatísticas gerais
        produtos = sum(1 for p in self.pedidos if p.tipo_item == "PRODUTO")
        subprodutos = sum(1 for p in self.pedidos if p.tipo_item == "SUBPRODUTO")
        quantidade_total = sum(p.quantidade for p in self.pedidos)
        
        # Estatísticas temporais
        inicio_mais_cedo = min(p.inicio_jornada for p in self.pedidos)
        fim_mais_tarde = max(p.fim_jornada for p in self.pedidos)
        duracao_total = fim_mais_tarde - inicio_mais_cedo
        
        # 🆕 Estatísticas por ordem
        ordens_existentes = self.listar_ordens_existentes()
        pedidos_ordem_atual = self.obter_pedidos_ordem_atual()
        
        return {
            "total": len(self.pedidos),
            "produtos": produtos,
            "subprodutos": subprodutos,
            "quantidade_total": quantidade_total,
            "inicio_mais_cedo": inicio_mais_cedo,
            "fim_mais_tarde": fim_mais_tarde,
            "duracao_total": duracao_total,
            # 🆕 Informações de ordem
            "ordem_atual": self.ordem_atual,
            "total_ordens": len(ordens_existentes),
            "ordens_existentes": ordens_existentes,
            "pedidos_ordem_atual": len(pedidos_ordem_atual)
        }