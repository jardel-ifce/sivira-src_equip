#!/usr/bin/env python3
"""
Filtro de Logs para Diagnóstico do Otimizador
============================================

Script para capturar apenas as mensagens relevantes do erro do otimizador.
"""

import re
import sys
from datetime import datetime


class FiltroLogsOtimizador:
    """Filtra logs para mostrar apenas informações relevantes do otimizador"""
    
    def __init__(self, arquivo_saida="debug_otimizador.log"):
        self.arquivo_saida = arquivo_saida
        
        # Padrões de interesse para o diagnóstico
        self.padroes_interesse = [
            # Controle de fluxo
            r"🔄 Executando pedido \d+/\d+",
            r"Fase \d+:",
            r"Iniciando execução",
            r"executar_pedidos_otimizados",
            
            # Problemas específicos
            r"Tempo máximo de espera excedido",
            r"já possui \d+g do produto",
            r"já alocado no nível",
            r"Limite da jornada atingido",
            r"ALOCAÇÃO FALHOU",
            r"Nenhum forno conseguiu atender",
            
            # Resultados
            r"Pedidos atendidos:",
            r"Taxa de atendimento:",
            r"Status do solver:",
            r"Executados:",
            r"Falhas:",
            
            # Rollback e limpeza
            r"Rollback concluído:",
            r"equipamentos.*liberados",
            
            # Timestamps importantes
            r"Atividade atual:.*\d+",
            r"Atividade sucessora:.*\d+",
            r"Fim da atual:",
            r"Início da sucessora:",
            r"Atraso detectado:",
            r"Máximo permitido:",
            
            # Horários de alocação
            r"Intervalo tentado:",
            r"\d{2}:\d{2} \[\d{2}/\d{2}\] → \d{2}:\d{2} \[\d{2}/\d{2}\]",
        ]
        
        # Compilar padrões para melhor performance
        self.regex_compilados = [re.compile(p, re.IGNORECASE) for p in self.padroes_interesse]
        
        # Contadores para estatísticas
        self.linhas_processadas = 0
        self.linhas_relevantes = 0
        self.execucoes_pedido = 0
        self.falhas_alocacao = 0
        
    def filtrar_linha(self, linha):
        """Verifica se uma linha é relevante para o diagnóstico"""
        linha_limpa = linha.strip()
        
        if not linha_limpa:
            return False
            
        # Verificar se a linha corresponde a algum padrão de interesse
        for regex in self.regex_compilados:
            if regex.search(linha_limpa):
                return True
                
        return False
    
    def processar_entrada(self, fonte_entrada=None):
        """
        Processa entrada (stdin ou arquivo) e filtra linhas relevantes
        
        Args:
            fonte_entrada: Arquivo para ler (None = stdin)
        """
        print(f"🔍 Iniciando filtragem de logs...")
        print(f"📝 Salvando em: {self.arquivo_saida}")
        
        try:
            with open(self.arquivo_saida, 'w', encoding='utf-8') as arquivo_saida:
                # Cabeçalho do arquivo
                arquivo_saida.write(f"# Logs Filtrados do Otimizador - {datetime.now()}\n")
                arquivo_saida.write(f"# Apenas mensagens relevantes para diagnóstico\n")
                arquivo_saida.write("="*80 + "\n\n")
                
                # Escolher fonte de entrada
                if fonte_entrada:
                    with open(fonte_entrada, 'r', encoding='utf-8') as arquivo_entrada:
                        linhas = arquivo_entrada.readlines()
                else:
                    print("📋 Cole os logs aqui (Ctrl+D ou Ctrl+Z para finalizar):")
                    linhas = sys.stdin.readlines()
                
                # Processar cada linha
                for linha in linhas:
                    self.linhas_processadas += 1
                    
                    if self.filtrar_linha(linha):
                        self.linhas_relevantes += 1
                        
                        # Adicionar timestamp se não tiver
                        linha_formatada = self._formatar_linha(linha)
                        arquivo_saida.write(linha_formatada + "\n")
                        
                        # Contadores específicos
                        self._atualizar_contadores(linha)
                
                # Estatísticas no final
                self._escrever_estatisticas(arquivo_saida)
                
        except Exception as e:
            print(f"❌ Erro ao processar logs: {e}")
            return False
            
        self._imprimir_resumo()
        return True
    
    def _formatar_linha(self, linha):
        """Formata uma linha para melhor legibilidade"""
        linha_limpa = linha.strip()
        
        # Se já tem timestamp, manter
        if re.match(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]', linha_limpa):
            return linha_limpa
            
        # Se é uma linha de resultado importante, destacar
        if any(palavra in linha_limpa for palavra in ['❌', '✅', '🔄', '⚠️', '🚀']):
            return f">>> {linha_limpa}"
            
        return linha_limpa
    
    def _atualizar_contadores(self, linha):
        """Atualiza contadores específicos baseados no conteúdo da linha"""
        linha_lower = linha.lower()
        
        if "executando pedido" in linha_lower:
            self.execucoes_pedido += 1
            
        if any(termo in linha_lower for termo in ["alocação falhou", "falha", "erro"]):
            self.falhas_alocacao += 1
    
    def _escrever_estatisticas(self, arquivo):
        """Escreve estatísticas no final do arquivo"""
        arquivo.write("\n" + "="*80 + "\n")
        arquivo.write("📊 ESTATÍSTICAS DO DIAGNÓSTICO\n")
        arquivo.write("="*80 + "\n")
        arquivo.write(f"📋 Linhas processadas: {self.linhas_processadas}\n")
        arquivo.write(f"🔍 Linhas relevantes: {self.linhas_relevantes}\n")
        arquivo.write(f"🔄 Execuções de pedido detectadas: {self.execucoes_pedido}\n")
        arquivo.write(f"❌ Falhas de alocação detectadas: {self.falhas_alocacao}\n")
        arquivo.write(f"📈 Taxa de relevância: {(self.linhas_relevantes/self.linhas_processadas*100):.1f}%\n")
    
    def _imprimir_resumo(self):
        """Imprime resumo no console"""
        print(f"\n✅ Filtragem concluída!")
        print(f"📋 Processadas: {self.linhas_processadas} linhas")
        print(f"🔍 Relevantes: {self.linhas_relevantes} linhas")
        print(f"🔄 Execuções detectadas: {self.execucoes_pedido}")
        print(f"❌ Falhas detectadas: {self.falhas_alocacao}")
        print(f"📄 Arquivo salvo: {self.arquivo_saida}")
        
        if self.execucoes_pedido > 1:
            print(f"⚠️  ATENÇÃO: Detectadas {self.execucoes_pedido} execuções de pedido!")
            print(f"   Isso pode indicar loop ou múltiplas tentativas.")


def usar_filtro_interativo():
    """Modo interativo para usar o filtro"""
    print("🔍 FILTRO DE LOGS DO OTIMIZADOR")
    print("="*40)
    
    nome_arquivo = input("📄 Nome do arquivo de saída (Enter para 'debug_otimizador.log'): ").strip()
    if not nome_arquivo:
        nome_arquivo = "debug_otimizador.log"
    
    modo = input("📋 Modo: (1) Colar logs aqui (2) Ler de arquivo: ").strip()
    
    filtro = FiltroLogsOtimizador(nome_arquivo)
    
    if modo == "2":
        arquivo_entrada = input("📁 Caminho do arquivo de entrada: ").strip()
        filtro.processar_entrada(arquivo_entrada)
    else:
        print("\n📋 Cole os logs abaixo (Ctrl+D no Linux/Mac ou Ctrl+Z no Windows para finalizar):")
        filtro.processar_entrada()


def exemplo_uso():
    """Exemplo de como usar o script"""
    print("""
🔧 COMO USAR ESTE SCRIPT:

Método 1 - Interativo:
    python filtro_logs.py

Método 2 - Diretamente no código:
    filtro = FiltroLogsOtimizador("meu_debug.log")
    filtro.processar_entrada("logs_completos.txt")

Método 3 - Stdin/Stdout:
    # Cole os logs e pressione Ctrl+D (Linux/Mac) ou Ctrl+Z (Windows)
    python filtro_logs.py < logs.txt

O script vai capturar apenas:
✅ Execuções de pedidos
✅ Problemas de alocação  
✅ Mensagens de erro específicas
✅ Horários e conflitos
✅ Resultados finais

Ignorando logs verbosos e focando no problema!
""")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        exemplo_uso()
    else:
        usar_filtro_interativo()