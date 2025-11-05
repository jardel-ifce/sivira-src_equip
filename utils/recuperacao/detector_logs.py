"""
Detector de Logs
================

Detecta e valida logs disponíveis para recuperação.
"""

import os
import glob
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class DetectorLogs:
    """
    🔍 Detector de logs de equipamentos detalhados

    Funcionalidades:
    - Detecta logs disponíveis no diretório
    - Extrai metadados dos logs (data, ordem, pedidos)
    - Valida estrutura dos logs
    - Ordena logs por data
    """

    def __init__(self, pasta_logs: str = "logs/equipamentos_detalhados"):
        """
        Inicializa detector

        Args:
            pasta_logs: Pasta onde os logs estão armazenados
        """
        self.pasta_logs = pasta_logs
        self.logs_encontrados: List[Dict] = []

    def detectar_logs(self) -> List[Dict]:
        """
        Detecta todos os logs disponíveis

        Returns:
            Lista de dicionários com informações dos logs:
            {
                'caminho': caminho completo do arquivo,
                'nome': nome do arquivo,
                'tamanho': tamanho em bytes,
                'data_modificacao': datetime da última modificação,
                'ordem': ID da ordem (extraído do nome),
                'pedidos': lista de IDs de pedidos (extraídos do nome)
            }
        """
        self.logs_encontrados.clear()

        # Verificar se pasta existe
        if not os.path.exists(self.pasta_logs):
            return []

        # Buscar todos os arquivos .log
        pattern = os.path.join(self.pasta_logs, "*.log")
        arquivos = glob.glob(pattern)

        for arquivo in arquivos:
            info_log = self._extrair_info_log(arquivo)
            if info_log:
                self.logs_encontrados.append(info_log)

        # Ordenar por data de modificação (mais recente primeiro)
        self.logs_encontrados.sort(key=lambda x: x['data_modificacao'], reverse=True)

        return self.logs_encontrados

    def _extrair_info_log(self, caminho: str) -> Optional[Dict]:
        """
        Extrai informações de um arquivo de log

        Args:
            caminho: Caminho do arquivo

        Returns:
            Dicionário com informações ou None se inválido
        """
        try:
            # Informações básicas do arquivo
            stat = os.stat(caminho)
            nome = os.path.basename(caminho)

            # Extrair metadados do nome do arquivo
            ordem, pedidos = self._extrair_metadados_nome(nome)

            return {
                'caminho': caminho,
                'nome': nome,
                'tamanho': stat.st_size,
                'data_modificacao': datetime.fromtimestamp(stat.st_mtime),
                'ordem': ordem,
                'pedidos': pedidos
            }

        except Exception as e:
            print(f"⚠️ Erro ao extrair info do log {caminho}: {e}")
            return None

    def _extrair_metadados_nome(self, nome: str) -> Tuple[Optional[int], List[int]]:
        """
        Extrai ordem e pedidos do nome do arquivo

        Formatos esperados:
        - ocupacoes_detalhadas_ordem_1_pedido_1_20251027_195345.log
        - ocupacoes_detalhadas_ordem_1_pedidos_1_2_20251027_195345.log

        Args:
            nome: Nome do arquivo

        Returns:
            Tupla (ordem, lista_pedidos)
        """
        ordem = None
        pedidos = []

        # Extrair ordem
        match_ordem = re.search(r'ordem_(\d+)', nome)
        if match_ordem:
            ordem = int(match_ordem.group(1))

        # Extrair pedidos (pode ser singular ou plural)
        # Formato: pedido_X ou pedidos_X_Y_Z
        match_pedido_singular = re.search(r'pedido_(\d+)', nome)
        match_pedidos_plural = re.search(r'pedidos_([\d_]+)', nome)

        if match_pedidos_plural:
            # Múltiplos pedidos: pedidos_1_2_3
            pedidos_str = match_pedidos_plural.group(1)
            # Extrair todos os números
            pedidos = [int(p) for p in pedidos_str.split('_') if p.isdigit()]
        elif match_pedido_singular:
            # Um único pedido: pedido_1
            pedidos = [int(match_pedido_singular.group(1))]

        return ordem, pedidos

    def obter_log_mais_recente(self) -> Optional[Dict]:
        """
        Retorna o log mais recente

        Returns:
            Dicionário com informações do log ou None se não houver
        """
        if not self.logs_encontrados:
            self.detectar_logs()

        return self.logs_encontrados[0] if self.logs_encontrados else None

    def obter_logs_por_ordem(self, id_ordem: int) -> List[Dict]:
        """
        Retorna todos os logs de uma ordem específica

        Args:
            id_ordem: ID da ordem

        Returns:
            Lista de logs da ordem
        """
        if not self.logs_encontrados:
            self.detectar_logs()

        return [log for log in self.logs_encontrados if log['ordem'] == id_ordem]

    def validar_estrutura_log(self, caminho: str) -> Tuple[bool, List[str]]:
        """
        Valida se o log tem a estrutura esperada

        Args:
            caminho: Caminho do arquivo de log

        Returns:
            Tupla (valido, lista_erros)
        """
        erros = []

        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()

            # Verificações básicas
            if not conteudo or not conteudo.strip():
                erros.append("Arquivo vazio")
                return False, erros

            # Verificar cabeçalho
            if "RELATÓRIO DETALHADO DE OCUPAÇÕES DE EQUIPAMENTOS" not in conteudo:
                erros.append("Cabeçalho do relatório não encontrado")

            # Verificar se tem pelo menos um equipamento
            if "🔧" not in conteudo:
                erros.append("Nenhum equipamento encontrado no log")

            # Verificar estatísticas finais
            if "ESTATÍSTICAS RESUMIDAS" not in conteudo:
                erros.append("Estatísticas finais não encontradas")

            return len(erros) == 0, erros

        except Exception as e:
            erros.append(f"Erro ao ler arquivo: {e}")
            return False, erros

    def extrair_equipamentos_do_log(self, caminho: str) -> List[Tuple[str, str]]:
        """
        Extrai lista de equipamentos presentes no log

        Args:
            caminho: Caminho do arquivo de log

        Returns:
            Lista de tuplas (nome_equipamento, tipo_equipamento)
        """
        equipamentos = []

        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()

            # Padrão: 🔧 Nome do Equipamento (TipoEquipamento)
            # Usar MULTILINE para capturar apenas a linha com 🔧
            pattern = r'🔧\s+(.+?)\s+\(([^)]+)\)'
            matches = re.findall(pattern, conteudo, re.MULTILINE)

            for nome, tipo in matches:
                # Limpar quebras de linha e espaços extras
                nome_limpo = ' '.join(nome.split())
                tipo_limpo = ' '.join(tipo.split())
                equipamentos.append((nome_limpo, tipo_limpo))

        except Exception as e:
            print(f"⚠️ Erro ao extrair equipamentos: {e}")

        return equipamentos

    def gerar_resumo_logs(self) -> str:
        """
        Gera resumo dos logs disponíveis

        Returns:
            String formatada com resumo
        """
        if not self.logs_encontrados:
            self.detectar_logs()

        if not self.logs_encontrados:
            return "📭 Nenhum log encontrado"

        linhas = []
        linhas.append("=" * 70)
        linhas.append(f"📋 LOGS DISPONÍVEIS PARA RECUPERAÇÃO ({len(self.logs_encontrados)})")
        linhas.append("=" * 70)

        for i, log in enumerate(self.logs_encontrados, 1):
            linhas.append(f"\n{i}. {log['nome']}")
            linhas.append(f"   📅 Data: {log['data_modificacao'].strftime('%d/%m/%Y %H:%M:%S')}")
            linhas.append(f"   📏 Tamanho: {log['tamanho']:,} bytes")
            linhas.append(f"   🆔 Ordem: {log['ordem']}")

            if log['pedidos']:
                pedidos_str = ', '.join(map(str, log['pedidos']))
                linhas.append(f"   📦 Pedidos: {pedidos_str}")

            # Validar estrutura
            valido, erros = self.validar_estrutura_log(log['caminho'])
            if valido:
                linhas.append(f"   ✅ Estrutura válida")
            else:
                linhas.append(f"   ❌ Estrutura inválida:")
                for erro in erros:
                    linhas.append(f"      - {erro}")

        linhas.append("\n" + "=" * 70)
        return "\n".join(linhas)

    def limpar(self):
        """Limpa lista de logs encontrados"""
        self.logs_encontrados.clear()
