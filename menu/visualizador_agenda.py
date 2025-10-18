"""
Visualizador de Agenda de Equipamentos
======================================

Módulo para visualização de agendas de equipamentos baseado nos logs reais
do sistema AtividadeModular. Integrado ao menu principal.

Estrutura de logs esperada:
/logs/equipamentos/ordem: X | pedido: Y.log
"""

import os
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, namedtuple

# Estrutura para dados de atividade do log
AtividadeLog = namedtuple('AtividadeLog', [
    'ordem', 'pedido', 'id_atividade', 'item', 'nome_atividade', 
    'equipamento', 'inicio', 'fim'
])

class VisualizadorAgenda:
    """Visualizador de agenda de equipamentos baseado em logs reais"""
    
    def __init__(self):
        # ✅ CORREÇÃO: Agora procura logs na pasta de sucesso
        self.logs_dir = "logs/equipamentos/sucesso"
        self.dados_cache = {}
        self.ultima_atualizacao = None
    
    def mostrar_menu_agenda(self):
        """Mostra o menu de opções da agenda"""
        print("📅 VISUALIZAÇÃO DE AGENDA DE EQUIPAMENTOS")
        print("=" * 60)
        
        # Status dos logs
        total_logs = self._contar_arquivos_log()
        print(f"📁 Logs disponíveis: {total_logs} arquivo(s)")
        
        if total_logs == 0:
            print("⚠️ Nenhum log de equipamento encontrado")
            print("💡 Execute algum pedido primeiro para gerar logs")
            print()
        else:
            # Mostra resumo rápido
            self._atualizar_cache()
            if self.dados_cache:
                equipamentos_ativos = len(self.dados_cache)
                print(f"🔧 Equipamentos com atividades: {equipamentos_ativos}")
                print()
        
        print("OPÇÕES DISPONÍVEIS:")
        print("1️⃣  Agenda Geral (todos os equipamentos)")
        print("2️⃣  Agenda por Tipo de Equipamento")
        print("3️⃣  Agenda de Equipamento Específico")
        print("4️⃣  Buscar Atividades por Item")
        print("5️⃣  Estatísticas de Utilização")
        print("6️⃣  Timeline por Ordem/Pedido")
        print("7️⃣  Verificar Conflitos de Horário")
        print("8️⃣  Exportar Agenda para Arquivo TXT")
        print("9️⃣  Gerar Relatório PDF de Escala e Pedidos")
        print("R️⃣  Recarregar Dados dos Logs")
        print("[V]  Voltar ao Menu Principal")
        print("─" * 60)
    
    def processar_opcao_agenda(self, opcao: str) -> bool:
        """
        Processa opção do menu de agenda.

        Returns:
            bool: True para continuar no menu, False para voltar ao principal
        """
        opcao = opcao.strip().lower()

        if opcao == "1":
            self.mostrar_agenda_geral()
        elif opcao == "2":
            self.mostrar_agenda_por_tipo()
        elif opcao == "3":
            self.mostrar_agenda_equipamento_especifico()
        elif opcao == "4":
            self.buscar_por_item()
        elif opcao == "5":
            self.mostrar_estatisticas()
        elif opcao == "6":
            self.mostrar_timeline_ordem()
        elif opcao == "7":
            self.verificar_conflitos()
        elif opcao == "8":
            self.exportar_agenda()
        elif opcao == "9":
            self.gerar_relatorio_escala_e_pedidos_pdf()
        elif opcao == "r":
            self.recarregar_dados()
        elif opcao == "v":
            return False  # Volta ao menu principal
        else:
            print(f"\n❌ Opção '{opcao}' inválida!")

        return True
    
    def _contar_arquivos_log(self) -> int:
        """Conta arquivos de log disponíveis"""
        try:
            pattern = os.path.join(self.logs_dir, "*.log")
            arquivos = glob.glob(pattern)
            return len(arquivos)
        except Exception:
            return 0
    
    def _atualizar_cache(self):
        """Atualiza cache com dados dos logs"""
        try:
            # Verifica se precisa atualizar
            if self._cache_ainda_valido():
                return
            
            self.dados_cache.clear()
            
            # Lê todos os arquivos de log
            pattern = os.path.join(self.logs_dir, "*.log")
            arquivos_log = glob.glob(pattern)
            
            for arquivo in arquivos_log:
                self._processar_arquivo_log(arquivo)
            
            self.ultima_atualizacao = datetime.now()
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar cache: {e}")
    
    def _cache_ainda_valido(self) -> bool:
        """Verifica se o cache ainda está válido (30 segundos)"""
        if self.ultima_atualizacao is None:
            return False
        
        agora = datetime.now()
        diferenca = agora - self.ultima_atualizacao
        return diferenca.total_seconds() < 30
    
    def _processar_arquivo_log(self, caminho_arquivo: str):
        """Processa um arquivo de log específico"""
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if linha:
                        atividade = self._parsear_linha_log(linha)
                        if atividade:
                            equipamento = atividade.equipamento
                            if equipamento not in self.dados_cache:
                                self.dados_cache[equipamento] = []
                            self.dados_cache[equipamento].append(atividade)
        
        except Exception as e:
            print(f"⚠️ Erro ao processar {caminho_arquivo}: {e}")
    
    def _parsear_linha_log(self, linha: str) -> Optional[AtividadeLog]:
        """
        Parseia uma linha do log no formato:
        ordem | pedido | id_atividade | item | nome_atividade | equipamento | inicio | fim
        """
        try:
            partes = [p.strip() for p in linha.split('|')]
            
            if len(partes) >= 8:
                return AtividadeLog(
                    ordem=partes[0],
                    pedido=partes[1], 
                    id_atividade=partes[2],
                    item=partes[3],
                    nome_atividade=partes[4],
                    equipamento=partes[5],
                    inicio=partes[6],
                    fim=partes[7]
                )
        except Exception:
            pass
        
        return None
    
    def mostrar_agenda_geral(self):
        """Mostra agenda geral de todos os equipamentos"""
        print("\n📋 AGENDA GERAL DE EQUIPAMENTOS")
        print("=" * 50)

        self._atualizar_cache()

        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return

        # Ordena equipamentos alfabeticamente
        for equipamento in sorted(self.dados_cache.keys()):
            atividades = self.dados_cache[equipamento]
            print(f"\n🔧 {equipamento}")
            print("─" * 30)

            if atividades:
                # Ordena atividades por horário de início
                atividades_ordenadas = sorted(atividades, key=lambda x: x.inicio)

                for atividade in atividades_ordenadas:
                    print(f"  ⏰ {atividade.inicio} - {atividade.fim}")

                    # Calcula e mostra duração
                    duracao = self._calcular_duracao(atividade.inicio, atividade.fim)
                    if duracao:
                        print(f"     ⏱️  Duração: {duracao}")

                    print(f"     📦 Ordem {atividade.ordem} | Pedido {atividade.pedido}")
                    print(f"     🎯 {atividade.nome_atividade}")
                    print(f"     📋 Item: {atividade.item}")
                    print()
            else:
                print("  📊 Nenhuma atividade registrada")
    
    def mostrar_agenda_por_tipo(self):
        """Mostra agenda agrupada por tipo de equipamento"""
        print("\n🏷️ AGENDA POR TIPO DE EQUIPAMENTO")
        print("=" * 50)
        
        self._atualizar_cache()
        
        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return
        
        # Agrupa por tipo (baseado no nome do equipamento)
        tipos = self._agrupar_por_tipo()
        
        for tipo, equipamentos in tipos.items():
            print(f"\n🏭 {tipo}")
            print("=" * 40)
            
            for equipamento, atividades in equipamentos.items():
                print(f"\n  🔧 {equipamento}")
                print("  " + "─" * 25)
                
                if atividades:
                    atividades_ordenadas = sorted(atividades, key=lambda x: x.inicio)
                    for atividade in atividades_ordenadas:
                        print(f"    ⏰ {atividade.inicio} - {atividade.fim}")
                        print(f"       🎯 {atividade.nome_atividade}")
                else:
                    print("    📊 Sem atividades")
    
    def _agrupar_por_tipo(self) -> Dict[str, Dict[str, List[AtividadeLog]]]:
        """Agrupa equipamentos por tipo baseado no nome"""
        tipos = defaultdict(lambda: defaultdict(list))
        
        for equipamento, atividades in self.dados_cache.items():
            # Deduz tipo do nome do equipamento
            tipo = self._deduzir_tipo_equipamento(equipamento)
            tipos[tipo][equipamento] = atividades
        
        return dict(tipos)
    
    def _deduzir_tipo_equipamento(self, nome_equipamento: str) -> str:
        """Deduz o tipo do equipamento baseado no nome"""
        nome = nome_equipamento.lower()
        
        if 'forno' in nome:
            return "FORNOS"
        elif 'armário' in nome or 'fermentador' in nome:
            return "ARMÁRIOS DE FERMENTAÇÃO"
        elif 'bancada' in nome:
            return "BANCADAS"
        elif 'masseira' in nome:
            return "MISTURADORAS"
        elif 'modeladora' in nome:
            return "MODELADORAS"
        elif 'divisora' in nome:
            return "DIVISORAS/BOLEADORAS"
        elif 'balança' in nome:
            return "BALANÇAS"
        elif 'batedeira' in nome:
            return "BATEDEIRAS"
        else:
            return "OUTROS"
    
    def mostrar_agenda_equipamento_especifico(self):
        """Mostra agenda de um equipamento específico"""
        print("\n🔍 AGENDA DE EQUIPAMENTO ESPECÍFICO")
        print("=" * 40)
        
        self._atualizar_cache()
        
        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return
        
        # Lista equipamentos disponíveis
        equipamentos = sorted(self.dados_cache.keys())
        
        print("Equipamentos disponíveis:")
        for i, equipamento in enumerate(equipamentos, 1):
            atividades_count = len(self.dados_cache[equipamento])
            print(f"  {i}. {equipamento} ({atividades_count} atividades)")
        
        try:
            escolha = input(f"\nEscolha um equipamento (1-{len(equipamentos)}): ").strip()
            indice = int(escolha) - 1
            
            if 0 <= indice < len(equipamentos):
                equipamento_escolhido = equipamentos[indice]
                self._mostrar_detalhes_equipamento(equipamento_escolhido)
            else:
                print("❌ Opção inválida!")
                
        except ValueError:
            print("❌ Digite um número válido!")
    
    def _calcular_duracao(self, inicio_str: str, fim_str: str) -> Optional[str]:
        """
        Calcula a duração entre dois horários no formato do log.
        Suporta durações maiores que 24 horas.

        Formato esperado: "HH:MM [DD/MM]" ou "HH:MM:SS [DD/MM]"
        Exemplo: "03:36 [30/12]" ou "06:50 [31/12]"

        Args:
            inicio_str: String do horário de início
            fim_str: String do horário de fim

        Returns:
            String formatada com a duração (ex: "1d 3h 14min" ou "2h 30min")
        """
        try:
            # Parse do formato "HH:MM [DD/MM]" ou "HH:MM:SS [DD/MM]"
            import re

            # Extrai hora, minuto, dia e mês
            pattern = r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*\[(\d{1,2})/(\d{1,2})\]'

            match_inicio = re.search(pattern, inicio_str)
            match_fim = re.search(pattern, fim_str)

            if not match_inicio or not match_fim:
                return None

            # Parse início
            h_ini = int(match_inicio.group(1))
            m_ini = int(match_inicio.group(2))
            s_ini = int(match_inicio.group(3)) if match_inicio.group(3) else 0
            dia_ini = int(match_inicio.group(4))
            mes_ini = int(match_inicio.group(5))

            # Parse fim
            h_fim = int(match_fim.group(1))
            m_fim = int(match_fim.group(2))
            s_fim = int(match_fim.group(3)) if match_fim.group(3) else 0
            dia_fim = int(match_fim.group(4))
            mes_fim = int(match_fim.group(5))

            # Usa ano atual (ou 2024 como padrão)
            ano = 2024

            # Cria objetos datetime
            dt_inicio = datetime(ano, mes_ini, dia_ini, h_ini, m_ini, s_ini)
            dt_fim = datetime(ano, mes_fim, dia_fim, h_fim, m_fim, s_fim)

            # Calcula diferença
            duracao = dt_fim - dt_inicio

            # Formata resultado
            total_segundos = int(duracao.total_seconds())

            if total_segundos < 0:
                return "⚠️ Duração negativa"

            dias = total_segundos // 86400
            horas = (total_segundos % 86400) // 3600
            minutos = (total_segundos % 3600) // 60

            # Formata string de saída
            partes = []
            if dias > 0:
                partes.append(f"{dias}d")
            if horas > 0:
                partes.append(f"{horas}h")
            if minutos > 0 or len(partes) == 0:
                partes.append(f"{minutos}min")

            return " ".join(partes)

        except Exception as e:
            return None

    def _mostrar_detalhes_equipamento(self, equipamento: str):
        """Mostra detalhes completos de um equipamento"""
        print(f"\n🔧 AGENDA DETALHADA: {equipamento}")
        print("=" * 50)

        atividades = self.dados_cache.get(equipamento, [])

        if not atividades:
            print("📊 Nenhuma atividade registrada para este equipamento")
            return

        # Ordena por horário
        atividades_ordenadas = sorted(atividades, key=lambda x: x.inicio)

        print(f"📊 Total de atividades: {len(atividades)}")

        # Calcula estatísticas
        tempos_inicio = [a.inicio for a in atividades]
        tempos_fim = [a.fim for a in atividades]

        print(f"⏰ Período de uso: {min(tempos_inicio)} até {max(tempos_fim)}")
        print()

        # Lista atividades
        for i, atividade in enumerate(atividades_ordenadas, 1):
            print(f"📋 ATIVIDADE {i}")
            print(f"   🆔 ID: {atividade.id_atividade}")
            print(f"   📦 Ordem {atividade.ordem} | Pedido {atividade.pedido}")
            print(f"   🏷️ Item: {atividade.item}")
            print(f"   🎯 Atividade: {atividade.nome_atividade}")
            print(f"   ⏰ Horário: {atividade.inicio} - {atividade.fim}")
            print()
    
    def buscar_por_item(self):
        """Busca atividades por item específico"""
        print("\n🔍 BUSCAR ATIVIDADES POR ITEM")
        print("=" * 30)
        
        self._atualizar_cache()
        
        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return
        
        # Lista itens únicos
        itens_unicos = set()
        for atividades in self.dados_cache.values():
            for atividade in atividades:
                itens_unicos.add(atividade.item)
        
        if not itens_unicos:
            print("📊 Nenhum item encontrado")
            return
        
        print("Itens disponíveis:")
        itens_ordenados = sorted(itens_unicos)
        for item in itens_ordenados:
            print(f"  • {item}")
        
        item_busca = input("\nDigite o nome do item (ou parte dele): ").strip().lower()
        
        if not item_busca:
            print("❌ Digite um termo de busca!")
            return
        
        # Busca atividades
        resultados = []
        for equipamento, atividades in self.dados_cache.items():
            for atividade in atividades:
                if item_busca in atividade.item.lower():
                    resultados.append((equipamento, atividade))
        
        if not resultados:
            print(f"📭 Nenhuma atividade encontrada para '{item_busca}'")
            return
        
        print(f"\n📋 RESULTADOS PARA '{item_busca}' ({len(resultados)} encontrados)")
        print("=" * 50)
        
        # Ordena por horário
        resultados_ordenados = sorted(resultados, key=lambda x: x[1].inicio)
        
        for equipamento, atividade in resultados_ordenados:
            print(f"🔧 {equipamento}")
            print(f"   ⏰ {atividade.inicio} - {atividade.fim}")
            print(f"   📦 Ordem {atividade.ordem} | Pedido {atividade.pedido}")
            print(f"   🎯 {atividade.nome_atividade}")
            print()
    
    def mostrar_estatisticas(self):
        """Mostra estatísticas de utilização dos equipamentos"""
        print("\n📊 ESTATÍSTICAS DE UTILIZAÇÃO")
        print("=" * 40)
        
        self._atualizar_cache()
        
        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return
        
        # Estatísticas gerais
        total_equipamentos = len(self.dados_cache)
        total_atividades = sum(len(atividades) for atividades in self.dados_cache.values())
        
        print(f"🔧 Total de equipamentos: {total_equipamentos}")
        print(f"📋 Total de atividades: {total_atividades}")
        print(f"📊 Média de atividades por equipamento: {total_atividades/total_equipamentos:.1f}")
        print()
        
        # Top equipamentos mais utilizados
        print("🏆 TOP 5 EQUIPAMENTOS MAIS UTILIZADOS:")
        equipamentos_ordenados = sorted(
            self.dados_cache.items(), 
            key=lambda x: len(x[1]), 
            reverse=True
        )
        
        for i, (equipamento, atividades) in enumerate(equipamentos_ordenados[:5], 1):
            print(f"  {i}. {equipamento}: {len(atividades)} atividades")
        
        print()
        
        # Estatísticas por tipo
        tipos = self._agrupar_por_tipo()
        print("📈 UTILIZAÇÃO POR TIPO:")
        
        for tipo, equipamentos in tipos.items():
            total_atividades_tipo = sum(len(atividades) for atividades in equipamentos.values())
            print(f"  {tipo}: {total_atividades_tipo} atividades ({len(equipamentos)} equipamentos)")
    
    def mostrar_timeline_ordem(self):
        """Mostra timeline de uma ordem/pedido específico"""
        print("\n📅 TIMELINE POR ORDEM/PEDIDO")
        print("=" * 30)
        
        self._atualizar_cache()
        
        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return
        
        # Coleta todas as ordens/pedidos disponíveis
        ordens_pedidos = set()
        for atividades in self.dados_cache.values():
            for atividade in atividades:
                ordens_pedidos.add(f"{atividade.ordem}|{atividade.pedido}")
        
        if not ordens_pedidos:
            print("📊 Nenhuma ordem/pedido encontrada")
            return
        
        print("Ordens/Pedidos disponíveis:")
        ordens_ordenadas = sorted(ordens_pedidos)
        for ordem_pedido in ordens_ordenadas:
            ordem, pedido = ordem_pedido.split('|')
            print(f"  • Ordem {ordem} | Pedido {pedido}")
        
        try:
            ordem_busca = input("\nDigite a ordem: ").strip()
            pedido_busca = input("Digite o pedido: ").strip()
            
            # Busca atividades da ordem/pedido
            atividades_encontradas = []
            for equipamento, atividades in self.dados_cache.items():
                for atividade in atividades:
                    if atividade.ordem == ordem_busca and atividade.pedido == pedido_busca:
                        atividades_encontradas.append((equipamento, atividade))
            
            if not atividades_encontradas:
                print(f"📭 Nenhuma atividade encontrada para Ordem {ordem_busca} | Pedido {pedido_busca}")
                return
            
            self._mostrar_timeline(ordem_busca, pedido_busca, atividades_encontradas)
            
        except KeyboardInterrupt:
            print("\n❌ Busca cancelada")
    
    def _mostrar_timeline(self, ordem: str, pedido: str, atividades: List[Tuple[str, AtividadeLog]]):
        """Mostra timeline organizada de atividades"""
        print(f"\n📅 TIMELINE - Ordem {ordem} | Pedido {pedido}")
        print("=" * 50)

        # Ordena por horário de início
        atividades_ordenadas = sorted(atividades, key=lambda x: x[1].inicio)

        print(f"📊 Total de atividades: {len(atividades)}")

        # Calcula duração total com parsing correto
        if atividades:
            inicio_primeiro = min(a[1].inicio for a in atividades)
            fim_ultimo = max(a[1].fim for a in atividades)
            print(f"⏰ Período total: {inicio_primeiro} até {fim_ultimo}")

            # Calcula a duração em formato legível
            duracao_str = self._calcular_duracao(inicio_primeiro, fim_ultimo)
            if duracao_str:
                print(f"⏱️  Duração total: {duracao_str}")

        print()

        # Mostra timeline
        for i, (equipamento, atividade) in enumerate(atividades_ordenadas, 1):
            print(f"📋 ETAPA {i}")
            print(f"   🔧 Equipamento: {equipamento}")
            print(f"   🎯 Atividade: {atividade.nome_atividade}")
            print(f"   ⏰ Horário: {atividade.inicio} - {atividade.fim}")

            # Calcula e mostra duração da atividade
            duracao_atividade = self._calcular_duracao(atividade.inicio, atividade.fim)
            if duracao_atividade:
                print(f"   ⏱️  Duração: {duracao_atividade}")

            print(f"   🆔 ID: {atividade.id_atividade}")
            print()
    
    def verificar_conflitos(self):
        """Verifica conflitos de horário entre equipamentos"""
        print("\n⚠️ VERIFICAÇÃO DE CONFLITOS")
        print("=" * 30)
        
        self._atualizar_cache()
        
        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return
        
        conflitos_encontrados = []
        
        # Verifica cada equipamento
        for equipamento, atividades in self.dados_cache.items():
            if len(atividades) < 2:
                continue
            
            # Ordena por horário
            atividades_ordenadas = sorted(atividades, key=lambda x: x.inicio)
            
            # Verifica sobreposições
            for i in range(len(atividades_ordenadas) - 1):
                ativ_atual = atividades_ordenadas[i]
                ativ_proxima = atividades_ordenadas[i + 1]
                
                # Verifica se há sobreposição (fim atual > início próximo)
                if ativ_atual.fim > ativ_proxima.inicio:
                    conflitos_encontrados.append((equipamento, ativ_atual, ativ_proxima))
        
        if not conflitos_encontrados:
            print("✅ Nenhum conflito de horário encontrado!")
            print("💡 Todos os equipamentos estão com agendas organizadas")
            return
        
        print(f"⚠️ {len(conflitos_encontrados)} conflito(s) encontrado(s):")
        print()
        
        for equipamento, ativ1, ativ2 in conflitos_encontrados:
            print(f"🔧 {equipamento}")
            print(f"   ❌ CONFLITO:")
            print(f"      1️⃣ {ativ1.nome_atividade} ({ativ1.inicio} - {ativ1.fim})")
            print(f"      2️⃣ {ativ2.nome_atividade} ({ativ2.inicio} - {ativ2.fim})")
            print(f"      ⏰ Sobreposição detectada!")
            print()
    
    def exportar_agenda(self):
        """Exporta agenda para arquivo texto"""
        print("\n💾 EXPORTAR AGENDA")
        print("=" * 20)

        self._atualizar_cache()

        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"agenda_equipamentos_{timestamp}.txt"

        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                f.write("AGENDA DE EQUIPAMENTOS\n")
                f.write("=" * 50 + "\n")
                f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

                # Escreve dados por equipamento
                for equipamento in sorted(self.dados_cache.keys()):
                    f.write(f"EQUIPAMENTO: {equipamento}\n")
                    f.write("-" * 30 + "\n")

                    atividades = self.dados_cache[equipamento]
                    if atividades:
                        atividades_ordenadas = sorted(atividades, key=lambda x: x.inicio)
                        for atividade in atividades_ordenadas:
                            f.write(f"  {atividade.inicio} - {atividade.fim}\n")

                            # Adiciona duração
                            duracao = self._calcular_duracao(atividade.inicio, atividade.fim)
                            if duracao:
                                f.write(f"  Duração: {duracao}\n")

                            f.write(f"  Ordem {atividade.ordem} | Pedido {atividade.pedido}\n")
                            f.write(f"  {atividade.nome_atividade}\n")
                            f.write(f"  Item: {atividade.item}\n\n")
                    else:
                        f.write("  Sem atividades registradas\n\n")

                    f.write("\n")

            print(f"✅ Agenda exportada para: {nome_arquivo}")

        except Exception as e:
            print(f"❌ Erro ao exportar agenda: {e}")

    def gerar_relatorio_escala_e_pedidos_pdf(self, nome_arquivo: str = "escala_e_pedidos.pdf"):
        """
        Gera relatório PDF com escala de equipamentos e pedidos com durações corretas.
        """
        print("\n📄 GERANDO RELATÓRIO PDF")
        print("=" * 30)

        self._atualizar_cache()

        if not self.dados_cache:
            print("📭 Nenhuma atividade encontrada nos logs")
            return

        try:
            from matplotlib.backends.backend_pdf import PdfPages
            import matplotlib.pyplot as plt
            from matplotlib.patches import Rectangle

            with PdfPages(nome_arquivo) as pdf:
                # Página 1: Resumo geral
                self._gerar_pagina_resumo(pdf)

                # Página 2+: Detalhamento por equipamento
                for equipamento in sorted(self.dados_cache.keys()):
                    self._gerar_pagina_equipamento(pdf, equipamento)

            print(f"✅ Relatório PDF gerado: {nome_arquivo}")

        except ImportError:
            print("❌ Biblioteca matplotlib não encontrada.")
            print("💡 Instalando matplotlib...")
            try:
                import subprocess
                subprocess.check_call(["pip", "install", "matplotlib"])
                print("✅ Matplotlib instalado. Execute novamente.")
            except:
                print("❌ Erro ao instalar matplotlib. Instale manualmente: pip install matplotlib")
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")

    def _gerar_pagina_resumo(self, pdf):
        """Gera página de resumo do relatório"""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')

        # Título
        ax.text(0.5, 0.95, 'RELATÓRIO DE ESCALA E PEDIDOS',
                ha='center', va='top', fontsize=16, fontweight='bold')

        # Data de geração
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        ax.text(0.5, 0.90, f'Gerado em: {data_atual}',
                ha='center', va='top', fontsize=10)

        # Estatísticas gerais
        total_equipamentos = len(self.dados_cache)
        total_atividades = sum(len(atividades) for atividades in self.dados_cache.values())

        y_pos = 0.80
        ax.text(0.1, y_pos, 'RESUMO GERAL', fontsize=12, fontweight='bold')
        y_pos -= 0.05
        ax.text(0.1, y_pos, f'• Total de equipamentos: {total_equipamentos}', fontsize=10)
        y_pos -= 0.04
        ax.text(0.1, y_pos, f'• Total de atividades: {total_atividades}', fontsize=10)
        y_pos -= 0.04
        ax.text(0.1, y_pos, f'• Média de atividades por equipamento: {total_atividades/total_equipamentos:.1f}', fontsize=10)

        # Lista de equipamentos
        y_pos -= 0.08
        ax.text(0.1, y_pos, 'EQUIPAMENTOS:', fontsize=12, fontweight='bold')
        y_pos -= 0.05

        for equipamento in sorted(self.dados_cache.keys()):
            num_atividades = len(self.dados_cache[equipamento])
            ax.text(0.15, y_pos, f'• {equipamento}: {num_atividades} atividades', fontsize=9)
            y_pos -= 0.03
            if y_pos < 0.1:
                break

        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    def _gerar_pagina_equipamento(self, pdf, equipamento: str):
        """Gera página detalhada para um equipamento específico"""
        import matplotlib.pyplot as plt

        atividades = self.dados_cache[equipamento]
        if not atividades:
            return

        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis('off')

        # Título
        ax.text(0.5, 0.95, f'EQUIPAMENTO: {equipamento}',
                ha='center', va='top', fontsize=14, fontweight='bold')

        # Atividades
        atividades_ordenadas = sorted(atividades, key=lambda x: x.inicio)

        y_pos = 0.88
        ax.text(0.05, y_pos, 'ATIVIDADES:', fontsize=11, fontweight='bold')
        y_pos -= 0.04

        for i, atividade in enumerate(atividades_ordenadas, 1):
            if y_pos < 0.05:
                break

            # Linha de atividade
            ax.text(0.05, y_pos, f'{i}. Ordem {atividade.ordem} | Pedido {atividade.pedido}',
                    fontsize=9, fontweight='bold')
            y_pos -= 0.03

            ax.text(0.10, y_pos, f'Item: {atividade.item}', fontsize=8)
            y_pos -= 0.025

            ax.text(0.10, y_pos, f'Atividade: {atividade.nome_atividade}', fontsize=8)
            y_pos -= 0.025

            ax.text(0.10, y_pos, f'Horário: {atividade.inicio} - {atividade.fim}', fontsize=8)
            y_pos -= 0.025

            # Calcula e mostra duração
            duracao = self._calcular_duracao(atividade.inicio, atividade.fim)
            if duracao:
                ax.text(0.10, y_pos, f'Duração: {duracao}', fontsize=8, color='blue')
                y_pos -= 0.025

            ax.text(0.10, y_pos, f'ID: {atividade.id_atividade}', fontsize=7, color='gray')
            y_pos -= 0.04

        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    def recarregar_dados(self):
        """Força recarregamento dos dados dos logs"""
        print("\n🔄 RECARREGANDO DADOS DOS LOGS")
        print("=" * 30)
        
        self.dados_cache.clear()
        self.ultima_atualizacao = None
        
        print("🗑️ Cache limpo")
        
        self._atualizar_cache()
        
        total_equipamentos = len(self.dados_cache)
        total_atividades = sum(len(atividades) for atividades in self.dados_cache.values())
        
        print(f"✅ Dados recarregados:")
        print(f"   🔧 {total_equipamentos} equipamentos")
        print(f"   📋 {total_atividades} atividades")
        print(f"   🕒 Última atualização: {self.ultima_atualizacao.strftime('%H:%M:%S')}")
