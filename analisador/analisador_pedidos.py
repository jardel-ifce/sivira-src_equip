import os
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")  # ajuste para o seu caminho
from datetime import datetime
from collections import defaultdict
import re

class AnalisadorPedidos:
    def __init__(self, diretorio_logs):
        self.diretorio_logs = diretorio_logs
        self.pedidos = {}  # {(ordem, pedido): [atividades]}
        self.atividades_por_id = defaultdict(list)  # {id_atividade: [(ordem, pedido, dados_atividade)]}
    
    def extrair_info_arquivo(self, nome_arquivo):
        """Extrai ordem e pedido do nome do arquivo"""
        # Padrão: ordem: X | pedido: Y.log
        match = re.match(r'ordem:\s*(\d+)\s*\|\s*pedido:\s*(\d+)\.log', nome_arquivo)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None
    
    def parse_linha_log(self, linha):
        """Parse de uma linha do log"""
        partes = [p.strip() for p in linha.split('|')]
        if len(partes) != 8:
            return None
        
        return {
            'ordem': int(partes[0]),
            'pedido': int(partes[1]),
            'id_atividade': int(partes[2]),
            'produto': partes[3],
            'atividade': partes[4],
            'equipamento': partes[5],
            'inicio': partes[6],
            'fim': partes[7]
        }
    
    def carregar_logs(self):
        """Carrega todos os logs do diretório"""
        if not os.path.exists(self.diretorio_logs):
            print(f"Diretório não encontrado: {self.diretorio_logs}")
            return
        
        arquivos_log = [f for f in os.listdir(self.diretorio_logs) if f.endswith('.log')]
        
        for arquivo in arquivos_log:
            ordem, pedido = self.extrair_info_arquivo(arquivo)
            if ordem is None or pedido is None:
                print(f"Arquivo com formato inválido: {arquivo}")
                continue
            
            caminho_completo = os.path.join(self.diretorio_logs, arquivo)
            
            try:
                with open(caminho_completo, 'r', encoding='utf-8') as f:
                    atividades = []
                    for linha in f:
                        linha = linha.strip()
                        if linha:
                            dados_atividade = self.parse_linha_log(linha)
                            if dados_atividade:
                                atividades.append(dados_atividade)
                                
                                # Indexar por ID de atividade para detectar duplicatas
                                self.atividades_por_id[dados_atividade['id_atividade']].append(
                                    (ordem, pedido, dados_atividade)
                                )
                    
                    self.pedidos[(ordem, pedido)] = atividades
                    print(f"Carregado: Ordem {ordem}, Pedido {pedido} - {len(atividades)} atividades")
            
            except Exception as e:
                print(f"Erro ao ler arquivo {arquivo}: {e}")
    
    def detectar_atividades_duplicadas(self):
        """Detecta IDs de atividades que aparecem em múltiplos pedidos"""
        duplicatas = {}
        
        for id_atividade, ocorrencias in self.atividades_por_id.items():
            if len(ocorrencias) > 1:
                # Verificar se são de pedidos diferentes
                pedidos_diferentes = set()
                for ordem, pedido, dados in ocorrencias:
                    pedidos_diferentes.add((ordem, pedido))
                
                if len(pedidos_diferentes) > 1:
                    duplicatas[id_atividade] = ocorrencias
        
        return duplicatas
    
    def exibir_relatorio_duplicatas(self):
        """Exibe relatório das atividades duplicadas"""
        duplicatas = self.detectar_atividades_duplicadas()
        
        if not duplicatas:
            print("\n=== RELATÓRIO DE ANÁLISE ===")
            print("Nenhuma atividade duplicada encontrada entre diferentes pedidos.")
            return
        
        print("\n=== RELATÓRIO DE ATIVIDADES DUPLICADAS ===")
        print(f"Encontradas {len(duplicatas)} atividade(s) compartilhada(s):\n")
        
        for id_atividade, ocorrencias in duplicatas.items():
            print(f"🔄 ID ATIVIDADE: {id_atividade}")
            
            # Pegar informações da primeira ocorrência para mostrar detalhes da atividade
            primeira_ocorrencia = ocorrencias[0][2]
            print(f"   Produto: {primeira_ocorrencia['produto']}")
            print(f"   Atividade: {primeira_ocorrencia['atividade']}")
            print(f"   Equipamento: {primeira_ocorrencia['equipamento']}")
            print()
            
            print("   📋 PEDIDOS QUE COMPARTILHAM ESTA ATIVIDADE:")
            for ordem, pedido, dados in ocorrencias:
                print(f"   • Ordem {ordem}, Pedido {pedido}")
                print(f"     Horário: {dados['inicio']} → {dados['fim']}")
            print("-" * 60)
        
        return duplicatas

def main():
    # Testar com os logs fornecidos
    diretorio = "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/logs/equipamentos"
    
    analisador = AnalisadorPedidos(diretorio)
    analisador.carregar_logs()
    duplicatas = analisador.exibir_relatorio_duplicatas()
    
    return analisador, duplicatas

if __name__ == "__main__":
    analisador, duplicatas = main()
