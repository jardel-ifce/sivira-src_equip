"""
Capturador de Ocupações de Equipamentos
=====================================

Sistema que captura ocupações detalhadas dos equipamentos EXISTENTES no sistema,
sem modificar as classes dos equipamentos. Funciona via:

1. Descoberta automática de equipamentos no sistema
2. Invocação do método mostrar_agenda() de cada equipamento
3. Captura e análise das saídas de log
4. Geração de relatórios detalhados com bocas, níveis, frações, etc.

Estratégia: Iterar sobre objetos existentes em vez de modificar classes.
"""

import os
import gc
import io
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from contextlib import redirect_stdout


class CapturadorOcupacoes:
    """
    🔍 Capturador de ocupações que encontra equipamentos ativos no sistema
    e extrai informações detalhadas via mostrar_agenda()
    """

    def __init__(self, pasta_logs: str = "logs/equipamentos_detalhados"):
        self.pasta_logs = pasta_logs
        self.equipamentos_encontrados: Dict[str, Any] = {}
        self.logs_capturados: Dict[str, str] = {}
        self._garantir_pasta_existe()

    def _garantir_pasta_existe(self):
        """Garante que a pasta de logs existe"""
        os.makedirs(self.pasta_logs, exist_ok=True)

    def descobrir_equipamentos_no_sistema(self) -> Dict[str, Any]:
        """
        🔍 Descobre todos os equipamentos disponíveis via fábrica de equipamentos
        Usa a lista equipamentos_disponiveis para garantir que todos estão incluídos
        """
        equipamentos_encontrados = {}

        try:
            # Importar da fábrica de equipamentos
            from factory.fabrica_equipamentos import equipamentos_disponiveis

            print(f"🔍 Carregando {len(equipamentos_disponiveis)} equipamentos da fábrica...")

            for equipamento in equipamentos_disponiveis:
                try:
                    if hasattr(equipamento, 'nome') and hasattr(equipamento, 'mostrar_agenda'):
                        nome = getattr(equipamento, 'nome', f'Equipamento_{id(equipamento)}')
                        tipo = type(equipamento).__name__
                        equipamentos_encontrados[f"{nome} ({tipo})"] = equipamento
                        print(f"   ✅ {nome} ({tipo}) registrado")
                    else:
                        print(f"   ⚠️ Equipamento inválido (sem nome/mostrar_agenda): {type(equipamento).__name__}")

                except Exception as e:
                    print(f"   ❌ Erro ao processar equipamento {type(equipamento).__name__}: {e}")
                    continue

        except ImportError as e:
            print(f"❌ Erro ao importar fábrica de equipamentos: {e}")
            # Fallback para garbage collector se a fábrica não estiver disponível
            print("🔄 Usando fallback via garbage collector...")
            return self._descobrir_via_garbage_collector()

        self.equipamentos_encontrados = equipamentos_encontrados
        return equipamentos_encontrados

    def _descobrir_via_garbage_collector(self) -> Dict[str, Any]:
        """
        🔍 Método fallback: descobre equipamentos via garbage collector
        """
        equipamentos_encontrados = {}

        # Percorre todos os objetos ativos no sistema
        for obj in gc.get_objects():
            try:
                # Verifica se é um equipamento válido
                if self._eh_equipamento_valido(obj):
                    nome = getattr(obj, 'nome', f'Equipamento_{id(obj)}')
                    tipo = type(obj).__name__
                    equipamentos_encontrados[f"{nome} ({tipo})"] = obj

            except Exception:
                # Ignora objetos que não podem ser acessados
                continue

        return equipamentos_encontrados

    def _eh_equipamento_valido(self, obj) -> bool:
        """
        🔍 Verifica se um objeto é um equipamento válido
        """
        try:
            # Verifica se tem atributos típicos de equipamento
            if not (hasattr(obj, 'nome') and hasattr(obj, 'mostrar_agenda')):
                return False

            # Verifica se tem ocupações (diferentes tipos de equipamento)
            tem_ocupacoes = (
                hasattr(obj, 'ocupacoes') or
                hasattr(obj, 'ocupacoes_por_boca') or
                hasattr(obj, 'configuracoes_temperatura') or
                hasattr(obj, 'fracoes_ocupadas')
            )

            if not tem_ocupacoes:
                return False

            # Verifica se é realmente um equipamento de produção
            nome = getattr(obj, 'nome', '')
            return any(tipo in nome.lower() for tipo in [
                'fogão', 'bancada', 'fritadeira', 'hotmix', 'balança',
                'freezer', 'câmara', 'forno', 'masseira'
            ])

        except Exception:
            return False

    def capturar_ocupacoes_todos_equipamentos(self, id_ordem: int, pedidos_inclusos: List[int] = None) -> Dict[str, str]:
        """
        📋 Captura ocupações detalhadas de todos os equipamentos descobertos
        """
        if not self.equipamentos_encontrados:
            self.descobrir_equipamentos_no_sistema()

        logs_capturados = {}

        print(f"🔍 Capturando ocupações de {len(self.equipamentos_encontrados)} equipamentos...")

        for nome_completo, equipamento in self.equipamentos_encontrados.items():
            try:
                log_capturado = self._capturar_mostrar_agenda(equipamento)
                if log_capturado and log_capturado.strip():
                    logs_capturados[nome_completo] = log_capturado
                    print(f"   ✅ {nome_completo}: {len(log_capturado)} chars capturados")
                else:
                    print(f"   📭 {nome_completo}: sem ocupações")

            except Exception as e:
                print(f"   ❌ {nome_completo}: erro ao capturar - {e}")

        self.logs_capturados = logs_capturados
        return logs_capturados

    def _capturar_mostrar_agenda(self, equipamento) -> Optional[str]:
        """
        📋 Captura a saída do método mostrar_agenda() de um equipamento
        """
        try:
            # Preparar captura de logs
            log_capture = io.StringIO()
            handler = logging.StreamHandler(log_capture)
            handler.setLevel(logging.INFO)

            # Obter logger do equipamento
            logger_name = type(equipamento).__name__
            equip_logger = logging.getLogger(logger_name)

            # Salvar nível original e configurar para capturar
            nivel_original = equip_logger.level
            equip_logger.setLevel(logging.INFO)
            equip_logger.addHandler(handler)

            try:
                # Executar mostrar_agenda()
                equipamento.mostrar_agenda()

                # Capturar o output
                log_output = log_capture.getvalue()
                return log_output

            finally:
                # Restaurar configuração original
                equip_logger.removeHandler(handler)
                equip_logger.setLevel(nivel_original)
                handler.close()

        except Exception as e:
            print(f"   ⚠️ Erro ao capturar agenda de {getattr(equipamento, 'nome', 'equipamento')}: {e}")
            return None

    def gerar_relatorio_ocupacoes_detalhadas(
        self,
        id_ordem: int,
        pedidos_inclusos: List[int] = None,
        salvar_arquivo: bool = True
    ) -> Optional[str]:
        """
        📄 Gera relatório completo com ocupações detalhadas capturadas para múltiplos pedidos
        """
        if not self.logs_capturados:
            self.capturar_ocupacoes_todos_equipamentos(id_ordem, pedidos_inclusos)

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Gerar nome mais descritivo incluindo todos os pedidos
            if pedidos_inclusos and len(pedidos_inclusos) > 1:
                pedidos_str = "_".join(map(str, sorted(pedidos_inclusos)))
                nome_arquivo = f"ocupacoes_detalhadas_ordem_{id_ordem}_pedidos_{pedidos_str}_{timestamp}.log"
            else:
                pedido_unico = pedidos_inclusos[0] if pedidos_inclusos else 1
                nome_arquivo = f"ocupacoes_detalhadas_ordem_{id_ordem}_pedido_{pedido_unico}_{timestamp}.log"

            if salvar_arquivo:
                caminho_completo = os.path.join(self.pasta_logs, nome_arquivo)
            else:
                caminho_completo = None

            conteudo = self._gerar_conteudo_relatorio(id_ordem, pedidos_inclusos)

            if salvar_arquivo and caminho_completo:
                with open(caminho_completo, 'w', encoding='utf-8') as f:
                    f.write(conteudo)

                print(f"✅ Relatório detalhado salvo: {caminho_completo}")
                return caminho_completo
            else:
                return conteudo

        except Exception as e:
            print(f"❌ Erro ao gerar relatório detalhado: {e}")
            return None

    def _gerar_conteudo_relatorio(self, id_ordem: int, pedidos_inclusos: List[int] = None) -> str:
        """
        📝 Gera o conteúdo formatado do relatório
        """
        linhas = []

        # Cabeçalho
        linhas.append("=" * 80)
        linhas.append(f"📋 RELATÓRIO DETALHADO DE OCUPAÇÕES DE EQUIPAMENTOS")

        # Gerar título com múltiplos pedidos se aplicável
        if pedidos_inclusos and len(pedidos_inclusos) > 1:
            pedidos_str = ", ".join(map(str, sorted(pedidos_inclusos)))
            linhas.append(f"    Ordem {id_ordem} | Pedidos {pedidos_str}")
        else:
            pedido_unico = pedidos_inclusos[0] if pedidos_inclusos else 1
            linhas.append(f"    Ordem {id_ordem} | Pedido {pedido_unico}")

        linhas.append("=" * 80)
        linhas.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        linhas.append(f"Equipamentos analisados: {len(self.equipamentos_encontrados)}")
        linhas.append(f"Equipamentos com ocupações: {len(self.logs_capturados)}")
        linhas.append("=" * 80)
        linhas.append("")

        # Para cada equipamento com ocupações
        for nome_completo, log_conteudo in self.logs_capturados.items():
            linhas.append(f"🔧 {nome_completo}")
            linhas.append("=" * 60)
            linhas.append("")

            # Adicionar log capturado com análise
            linhas.append("📋 OCUPAÇÕES REGISTRADAS:")
            linhas.append("-" * 40)
            linhas.append(log_conteudo)
            linhas.append("-" * 40)

            # Análise do conteúdo
            analise = self._analisar_log_equipamento(nome_completo, log_conteudo)
            if analise:
                linhas.append("🔍 ANÁLISE:")
                for linha_analise in analise:
                    linhas.append(f"   {linha_analise}")

            linhas.append("")
            linhas.append("=" * 60)
            linhas.append("")

        # Equipamentos sem ocupações
        equipamentos_vazios = []
        for nome_completo in self.equipamentos_encontrados:
            if nome_completo not in self.logs_capturados:
                equipamentos_vazios.append(nome_completo)

        if equipamentos_vazios:
            linhas.append("📭 EQUIPAMENTOS SEM OCUPAÇÕES:")
            linhas.append("-" * 40)
            for nome in equipamentos_vazios:
                linhas.append(f"   • {nome}")
            linhas.append("")

        # Estatísticas finais
        linhas.append("=" * 80)
        linhas.append("📊 ESTATÍSTICAS RESUMIDAS")
        linhas.append("=" * 80)
        linhas.append(f"📈 Total de equipamentos descobertos: {len(self.equipamentos_encontrados)}")
        linhas.append(f"🔧 Equipamentos com ocupações: {len(self.logs_capturados)}")
        linhas.append(f"📭 Equipamentos vazios: {len(equipamentos_vazios)}")

        # Contagem por tipo
        tipos_equipamentos = self._contar_tipos_equipamentos()
        if tipos_equipamentos:
            linhas.append("")
            linhas.append("🏷️ TIPOS DE EQUIPAMENTOS:")
            for tipo, count in tipos_equipamentos.items():
                linhas.append(f"   • {tipo}: {count} equipamento(s)")

        linhas.append("")
        linhas.append("=" * 80)
        linhas.append("📄 Fim do relatório detalhado")
        linhas.append("=" * 80)

        return "\n".join(linhas)

    def _analisar_log_equipamento(self, nome_completo: str, log_conteudo: str) -> List[str]:
        """
        🔍 Analisa o log capturado e extrai informações específicas
        """
        analise = []

        try:
            nome_lower = nome_completo.lower()

            # Análise para Fogão
            if 'fogão' in nome_lower:
                bocas_utilizadas = self._extrair_bocas_fogao(log_conteudo)
                if bocas_utilizadas:
                    analise.append(f"🔥 Bocas utilizadas: {', '.join(bocas_utilizadas)}")

                # Procurar por informações de chama e pressão
                if 'chama:' in log_conteudo.lower():
                    chamas = self._extrair_configuracoes_chama(log_conteudo)
                    if chamas:
                        analise.append(f"🔥 Configurações de chama: {chamas}")

            # Análise para Bancada
            elif 'bancada' in nome_lower:
                if 'fração' in log_conteudo.lower():
                    fracoes = self._extrair_fracoes_bancada(log_conteudo)
                    if fracoes:
                        analise.append(f"📐 Frações utilizadas: {fracoes}")

            # Análise para Refrigeração
            elif any(termo in nome_lower for termo in ['freezer', 'câmara', 'refrigerad']):
                if 'nível' in log_conteudo.lower() or 'caixa' in log_conteudo.lower():
                    niveis_caixas = self._extrair_niveis_caixas(log_conteudo)
                    if niveis_caixas:
                        analise.append(f"❄️ Níveis/Caixas utilizados: {niveis_caixas}")

                if '°c' in log_conteudo.lower():
                    temperaturas = self._extrair_temperaturas(log_conteudo)
                    if temperaturas:
                        analise.append(f"🌡️ Temperaturas: {temperaturas}")

            # Análise geral para quantidades
            quantidades = self._extrair_quantidades_gramas(log_conteudo)
            if quantidades:
                total_gramas = sum(quantidades)
                analise.append(f"⚖️ Total processado: {total_gramas:.1f}g em {len(quantidades)} operação(ões)")

            # Análise de horários
            horarios = self._extrair_horarios(log_conteudo)
            if horarios and len(horarios) >= 2:
                inicio_min = min(horarios)
                fim_max = max(horarios)
                analise.append(f"⏰ Período de uso: {inicio_min} - {fim_max}")

        except Exception as e:
            analise.append(f"⚠️ Erro na análise: {e}")

        return analise

    def _extrair_bocas_fogao(self, log_conteudo: str) -> List[str]:
        """Extrai números de bocas utilizadas"""
        import re
        bocas = re.findall(r'boca (\d+)', log_conteudo.lower())
        return list(set(bocas))

    def _extrair_configuracoes_chama(self, log_conteudo: str) -> str:
        """Extrai configurações de chama e pressão"""
        import re
        chamas = re.findall(r'chama: (\w+)', log_conteudo.lower())
        pressoes = re.findall(r'pressão: ([\w, ]+)', log_conteudo.lower())

        config = []
        if chamas:
            config.append(f"Chama: {', '.join(set(chamas))}")
        if pressoes:
            config.append(f"Pressão: {', '.join(set(pressoes))}")

        return " | ".join(config)

    def _extrair_fracoes_bancada(self, log_conteudo: str) -> str:
        """Extrai informações sobre frações utilizadas"""
        import re
        fracoes = re.findall(r'fração (\d+)', log_conteudo.lower())
        return ', '.join(set(fracoes)) if fracoes else ""

    def _extrair_niveis_caixas(self, log_conteudo: str) -> str:
        """Extrai informações sobre níveis e caixas"""
        import re
        niveis = re.findall(r'nível (\d+)', log_conteudo.lower())
        caixas = re.findall(r'caixa (\d+)', log_conteudo.lower())

        info = []
        if niveis:
            info.append(f"Níveis: {', '.join(set(niveis))}")
        if caixas:
            info.append(f"Caixas: {', '.join(set(caixas))}")

        return " | ".join(info)

    def _extrair_temperaturas(self, log_conteudo: str) -> str:
        """Extrai temperaturas mencionadas"""
        import re
        temps = re.findall(r'(-?\d+)°c', log_conteudo.lower())
        return f"{', '.join(set(temps))}°C" if temps else ""

    def _extrair_quantidades_gramas(self, log_conteudo: str) -> List[float]:
        """Extrai quantidades em gramas APENAS de ocupações, ignorando capacidades"""
        import re

        quantidades_encontradas = set()  # Usar set para evitar duplicatas

        # Procurar especificamente por linhas de ocupação com padrão completo
        # Exemplo: "🔸 Ordem 1 | Pedido 1 | Atividade 20031 | Item 0 | 60.0g |"
        linhas = log_conteudo.split('\n')

        for linha in linhas:
            linha_lower = linha.lower()

            # Evitar linhas de capacidade ou configuração
            if any(palavra in linha_lower for palavra in ['capacidade:', 'capacidade', '-']):
                continue

            # Procurar apenas linhas que são ocupações reais
            if all(termo in linha_lower for termo in ['ordem', 'pedido', 'atividade', 'item']):
                # Extrair quantidades dessa linha específica
                matches = re.findall(r'(\d+(?:\.\d+)?)g', linha_lower)
                for match in matches:
                    quantidades_encontradas.add(float(match))

        return list(quantidades_encontradas)

    def _extrair_horarios(self, log_conteudo: str) -> List[str]:
        """Extrai horários mencionados"""
        import re
        horarios = re.findall(r'(\d{2}:\d{2})', log_conteudo)
        return list(set(horarios))

    def _contar_tipos_equipamentos(self) -> Dict[str, int]:
        """Conta equipamentos por tipo"""
        contadores = {}

        for nome_completo in self.equipamentos_encontrados:
            # Extrair tipo do nome
            if '(' in nome_completo and ')' in nome_completo:
                tipo = nome_completo.split('(')[-1].split(')')[0]
                contadores[tipo] = contadores.get(tipo, 0) + 1

        return contadores

    def limpar_dados(self):
        """Limpa dados capturados"""
        self.equipamentos_encontrados.clear()
        self.logs_capturados.clear()


# Instância global para uso em todo o sistema
capturador_ocupacoes = CapturadorOcupacoes()