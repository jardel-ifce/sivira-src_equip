"""
Gerador de CSV de Reabastecimento.

Gera arquivos CSV com pedidos de reabastecimento para subprodutos críticos.
"""

import os
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from utils.producao.calculadora_duracao import consultar_duracao_por_faixas


class GeradorCSVReabastecimento:
    """
    Gera arquivos CSV com pedidos de reabastecimento.

    Formato do CSV:
    id,tipo_produto,quantidade,fim_jornada
    2012,SUBPRODUTO,19500,2025-10-24 18:00:00
    """

    # Configurações
    DIR_CSV = "data/csv/reabastecimento"
    HORA_PADRAO_ENTREGA = 18  # 18:00
    TIPO_PRODUTO = "SUBPRODUTO"

    def __init__(self):
        """Inicializa o gerador de CSV."""
        # Criar diretório se não existir
        os.makedirs(self.DIR_CSV, exist_ok=True)

    def gerar_csv_reabastecimento(
        self,
        itens_criticos: List[Dict],
        data_entrega: datetime = None
    ) -> Tuple[bool, str, str]:
        """
        Gera arquivo CSV com pedidos de reabastecimento.

        Args:
            itens_criticos: Lista de itens críticos (do DetectorItensCriticos)
            data_entrega: Data/hora de entrega desejada (padrão: próximo dia às 18:00)

        Returns:
            Tupla (sucesso, caminho_arquivo, mensagem)
        """
        try:
            # Se não forneceu data, usar próximo dia às 18:00
            if data_entrega is None:
                data_entrega = self._obter_data_entrega_padrao()

            # Gerar nome do arquivo
            nome_arquivo = self._gerar_nome_arquivo(data_entrega)
            caminho_completo = os.path.join(self.DIR_CSV, nome_arquivo)

            # Gerar CSV
            linhas_escritas = self._escrever_csv(caminho_completo, itens_criticos, data_entrega)

            if linhas_escritas > 0:
                mensagem = f"✅ CSV gerado com sucesso: {linhas_escritas} item(ns)"
                return True, caminho_completo, mensagem
            else:
                mensagem = "⚠️ Nenhum item crítico para incluir no CSV"
                return False, "", mensagem

        except Exception as e:
            mensagem = f"❌ Erro ao gerar CSV: {e}"
            return False, "", mensagem

    def _obter_data_entrega_padrao(self) -> datetime:
        """
        Obtém data/hora padrão de entrega (próximo dia às 18:00).

        Returns:
            datetime: Próximo dia às 18:00
        """
        agora = datetime.now()
        proximo_dia = agora + timedelta(days=1)
        data_entrega = proximo_dia.replace(
            hour=self.HORA_PADRAO_ENTREGA,
            minute=0,
            second=0,
            microsecond=0
        )
        return data_entrega

    def _gerar_nome_arquivo(self, data_entrega: datetime) -> str:
        """
        Gera nome do arquivo CSV no formato pedidos_YYYY_MM_DD.csv.

        Args:
            data_entrega: Data de entrega dos pedidos

        Returns:
            str: Nome do arquivo
        """
        return f"pedidos_{data_entrega.strftime('%Y_%m_%d')}.csv"

    def _escrever_csv(
        self,
        caminho_arquivo: str,
        itens_criticos: List[Dict],
        data_entrega: datetime
    ) -> int:
        """
        Escreve o arquivo CSV.

        Args:
            caminho_arquivo: Caminho completo do arquivo
            itens_criticos: Lista de itens críticos
            data_entrega: Data/hora de entrega

        Returns:
            int: Número de linhas escritas (excluindo cabeçalho)
        """
        # Formatar data/hora para o CSV
        fim_jornada_str = data_entrega.strftime('%Y-%m-%d %H:%M:%S')

        with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Cabeçalho
            writer.writerow(['id', 'tipo_produto', 'quantidade', 'fim_jornada'])

            # Dados
            linhas_escritas = 0
            for item in itens_criticos:
                writer.writerow([
                    item['id'],
                    self.TIPO_PRODUTO,
                    int(item['quantidade_reabastecer']),  # Converter para inteiro
                    fim_jornada_str
                ])
                linhas_escritas += 1

        return linhas_escritas

    def obter_data_sugerida(self) -> datetime:
        """
        Obtém a data/hora sugerida para entrega.

        Returns:
            datetime: Data sugerida (próximo dia às 18:00)
        """
        return self._obter_data_entrega_padrao()

    def formatar_data_para_exibicao(self, data: datetime) -> str:
        """
        Formata data para exibição amigável.

        Args:
            data: Data a ser formatada

        Returns:
            str: Data formatada (ex: "24/10/2025 18:00")
        """
        return data.strftime('%d/%m/%Y %H:%M')

    def listar_csvs_gerados(self) -> List[Dict]:
        """
        Lista todos os CSVs de reabastecimento gerados.

        Returns:
            Lista de dicionários com informações dos arquivos
        """
        arquivos = []

        if not os.path.exists(self.DIR_CSV):
            return arquivos

        for arquivo in os.listdir(self.DIR_CSV):
            if arquivo.endswith('.csv'):
                caminho_completo = os.path.join(self.DIR_CSV, arquivo)
                stat = os.stat(caminho_completo)

                # Contar linhas
                with open(caminho_completo, 'r', encoding='utf-8') as f:
                    total_linhas = sum(1 for _ in f) - 1  # -1 para excluir cabeçalho

                arquivos.append({
                    'nome': arquivo,
                    'caminho': caminho_completo,
                    'tamanho_bytes': stat.st_size,
                    'data_criacao': datetime.fromtimestamp(stat.st_ctime),
                    'total_itens': total_linhas
                })

        # Ordenar por data de criação (mais recente primeiro)
        arquivos.sort(key=lambda x: x['data_criacao'], reverse=True)

        return arquivos

    def calcular_duracao_pedido(self, id_item: int, quantidade: int) -> Optional[timedelta]:
        """
        Calcula a duração de produção de um pedido.

        Args:
            id_item: ID do item (subproduto)
            quantidade: Quantidade a ser produzida

        Returns:
            timedelta com a duração total ou None se não conseguir calcular
        """
        try:
            # Caminho para o arquivo de atividades
            caminho_atividades = f"data/subprodutos/atividades/{id_item}_*.json"

            # Buscar o arquivo
            import glob
            arquivos = glob.glob(caminho_atividades)

            if not arquivos:
                return None

            # Carregar dados do item
            with open(arquivos[0], 'r', encoding='utf-8') as f:
                dados_item = json.load(f)

            # Calcular duração total somando todas as atividades
            duracao_total = timedelta()

            for atividade in dados_item.get('atividades', []):
                duracao_atividade = consultar_duracao_por_faixas(atividade, quantidade)
                duracao_total += duracao_atividade

            return duracao_total

        except Exception as e:
            print(f"⚠️ Erro ao calcular duração do item {id_item}: {e}")
            return None

    def calcular_datas_individuais(
        self,
        itens_criticos: List[Dict],
        buffer_horas: float = 2.0
    ) -> Dict[int, datetime]:
        """
        Calcula data/hora individual para cada pedido baseado na duração.

        Fórmula: hora_atual + buffer + duração_do_pedido

        Args:
            itens_criticos: Lista de itens críticos
            buffer_horas: Buffer de tempo em horas (padrão: 2.0)

        Returns:
            Dicionário {id_item: datetime de conclusão}
        """
        datas_calculadas = {}
        hora_atual = datetime.now()

        print(f"\n🕐 Hora atual: {self.formatar_data_para_exibicao(hora_atual)}")
        print(f"⏱️  Buffer configurado: {buffer_horas:.1f}h")
        print("\n" + "=" * 80)
        print("CÁLCULO DE DATAS INDIVIDUAIS")
        print("=" * 80)

        for item in itens_criticos:
            id_item = item['id']
            quantidade = item['quantidade_reabastecer']
            nome = item['nome']

            # Calcular duração
            duracao = self.calcular_duracao_pedido(id_item, quantidade)

            if duracao:
                # Calcular data de conclusão: hora_atual + buffer + duração
                hora_inicio = hora_atual + timedelta(hours=buffer_horas)
                hora_conclusao = hora_inicio + duracao

                datas_calculadas[id_item] = hora_conclusao

                # Exibir informações
                duracao_str = self._formatar_timedelta(duracao)
                print(f"\n📦 [{id_item}] {nome[:40]}")
                print(f"   Quantidade: {quantidade:.0f}")
                print(f"   Duração calculada: {duracao_str}")
                print(f"   Início estimado: {self.formatar_data_para_exibicao(hora_inicio)}")
                print(f"   Conclusão estimada: {self.formatar_data_para_exibicao(hora_conclusao)}")
            else:
                # Se não conseguir calcular, usar data padrão
                data_padrao = self._obter_data_entrega_padrao()
                datas_calculadas[id_item] = data_padrao
                print(f"\n⚠️ [{id_item}] {nome[:40]}")
                print(f"   Não foi possível calcular duração. Usando data padrão.")
                print(f"   Conclusão: {self.formatar_data_para_exibicao(data_padrao)}")

        print("=" * 80)

        return datas_calculadas

    def gerar_csv_com_datas_individuais(
        self,
        itens_criticos: List[Dict],
        buffer_horas: float = 2.0
    ) -> Tuple[bool, str, str]:
        """
        Gera CSV com datas individuais calculadas por pedido.

        Args:
            itens_criticos: Lista de itens críticos
            buffer_horas: Buffer de tempo em horas

        Returns:
            Tupla (sucesso, caminho_arquivo, mensagem)
        """
        try:
            # Calcular datas individuais
            datas_individuais = self.calcular_datas_individuais(itens_criticos, buffer_horas)

            # Usar a data mais distante para o nome do arquivo
            data_mais_distante = max(datas_individuais.values())

            # Gerar nome do arquivo
            nome_arquivo = self._gerar_nome_arquivo(data_mais_distante)
            caminho_completo = os.path.join(self.DIR_CSV, nome_arquivo)

            # Escrever CSV com datas individuais
            linhas_escritas = self._escrever_csv_datas_individuais(
                caminho_completo,
                itens_criticos,
                datas_individuais
            )

            if linhas_escritas > 0:
                mensagem = f"✅ CSV gerado com sucesso: {linhas_escritas} item(ns) com datas individuais"
                return True, caminho_completo, mensagem
            else:
                mensagem = "⚠️ Nenhum item crítico para incluir no CSV"
                return False, "", mensagem

        except Exception as e:
            mensagem = f"❌ Erro ao gerar CSV com datas individuais: {e}"
            return False, "", mensagem

    def _escrever_csv_datas_individuais(
        self,
        caminho_arquivo: str,
        itens_criticos: List[Dict],
        datas_individuais: Dict[int, datetime]
    ) -> int:
        """
        Escreve CSV com datas individuais por pedido.

        Args:
            caminho_arquivo: Caminho do arquivo
            itens_criticos: Lista de itens críticos
            datas_individuais: Dicionário com datas por item

        Returns:
            Número de linhas escritas
        """
        with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Cabeçalho
            writer.writerow(['id', 'tipo_produto', 'quantidade', 'fim_jornada'])

            # Dados
            linhas_escritas = 0
            for item in itens_criticos:
                id_item = item['id']
                data_conclusao = datas_individuais.get(id_item, self._obter_data_entrega_padrao())

                writer.writerow([
                    id_item,
                    self.TIPO_PRODUTO,
                    int(item['quantidade_reabastecer']),
                    data_conclusao.strftime('%Y-%m-%d %H:%M:%S')
                ])
                linhas_escritas += 1

        return linhas_escritas

    def _formatar_timedelta(self, td: timedelta) -> str:
        """
        Formata timedelta para exibição (HH:MM:SS).

        Args:
            td: timedelta a formatar

        Returns:
            String formatada
        """
        total_segundos = int(td.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
