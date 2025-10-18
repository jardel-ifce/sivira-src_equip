#!/usr/bin/env python3
"""
💾 EXPORTADOR PARA BANCO DE DADOS
=================================

Prepara pedidos aprovados para exportação ao banco de dados.
Gera scripts SQL e relatórios, garantindo compatibilidade futura.

NOTA: A exportação real para o banco será implementada posteriormente.
      Este módulo garante que os dados estejam prontos e compatíveis.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from utils.logs.logger_factory import setup_logger

logger = setup_logger("ExportadorBanco")


class ExportadorBanco:
    """
    Prepara e exporta pedidos aprovados para o banco de dados.
    """

    def __init__(self):
        self.dir_aprovados = "logs/validacao/aprovados"
        self.dir_scripts_sql = "logs/exportacao/banco"
        self.dir_relatorios = "logs/exportacao/relatorios"

        # Criar diretórios se não existirem
        for diretorio in [self.dir_scripts_sql, self.dir_relatorios]:
            os.makedirs(diretorio, exist_ok=True)

    def listar_pedidos_pendentes_exportacao(self) -> List[Dict]:
        """
        Lista pedidos aprovados que ainda não foram exportados.

        Returns:
            List[Dict]: Lista de pedidos pendentes
        """
        pedidos_pendentes = []

        if not os.path.exists(self.dir_aprovados):
            return pedidos_pendentes

        for arquivo in os.listdir(self.dir_aprovados):
            if arquivo.endswith('.json'):
                caminho = os.path.join(self.dir_aprovados, arquivo)
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        pedido = json.load(f)
                        # Verificar se não foi exportado
                        if not pedido.get('exportado', False):
                            pedidos_pendentes.append(pedido)
                except Exception as e:
                    logger.error(f"Erro ao ler {caminho}: {e}")

        return sorted(pedidos_pendentes, key=lambda x: (x['id_ordem'], x['id_pedido']))

    def preparar_lote_exportacao(self, pedidos: List[Dict]) -> Dict:
        """
        Prepara um lote de pedidos para exportação.

        Args:
            pedidos: Lista de pedidos aprovados

        Returns:
            Dict com informações do lote
        """
        if not pedidos:
            logger.warning("⚠️ Nenhum pedido para exportar")
            return None

        lote_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        lote = {
            'lote_id': lote_id,
            'data_preparacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_pedidos': len(pedidos),
            'pedidos': [],
            'status': 'preparado'
        }

        for pedido in pedidos:
            lote['pedidos'].append({
                'id_ordem': pedido['id_ordem'],
                'id_pedido': pedido['id_pedido'],
                'data_aprovacao': pedido.get('data_aprovacao')
            })

        logger.info(f"📦 Lote {lote_id} preparado com {len(pedidos)} pedido(s)")
        return lote

    def gerar_script_sql(self, pedidos: List[Dict]) -> str:
        """
        Gera script SQL para inserção dos pedidos no banco.

        NOTA: Este é um script exemplo/template. A estrutura real do banco
              deve ser definida posteriormente.

        Args:
            pedidos: Lista de pedidos aprovados

        Returns:
            str: Script SQL gerado
        """
        if not pedidos:
            return ""

        lote_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        script = []

        # Header do script
        script.append("-- ================================================")
        script.append("-- SCRIPT DE EXPORTAÇÃO DE PEDIDOS")
        script.append(f"-- Lote: {lote_id}")
        script.append(f"-- Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        script.append(f"-- Total de pedidos: {len(pedidos)}")
        script.append("-- ================================================")
        script.append("")
        script.append("BEGIN TRANSACTION;")
        script.append("")

        for pedido in pedidos:
            id_ordem = pedido['id_ordem']
            id_pedido = pedido['id_pedido']

            script.append(f"-- Pedido: Ordem {id_ordem} | Pedido {id_pedido}")
            script.append(f"-- Status: {pedido['status']}")
            script.append(f"-- Aprovado em: {pedido.get('data_aprovacao', 'N/A')}")

            # Exemplo de INSERT - estrutura a ser definida posteriormente
            script.append(f"INSERT INTO pedidos (id_ordem, id_pedido, status, data_aprovacao)")
            script.append(f"VALUES ({id_ordem}, {id_pedido}, '{pedido['status']}', '{pedido.get('data_aprovacao', 'NULL')}');")
            script.append("")

            # Inserir detalhes de equipamentos
            equip = pedido['detalhes']['equipamentos']
            script.append(f"-- Equipamentos: {equip['atividades_sucesso']}/{equip['total_atividades']}")
            script.append(f"-- INSERT INTO alocacao_equipamentos (...) VALUES (...);")
            script.append("")

            # Inserir detalhes de funcionários
            func = pedido['detalhes']['funcionarios']
            script.append(f"-- Funcionários: {func['atividades_sucesso']}/{func['total_atividades']}")
            script.append(f"-- INSERT INTO alocacao_funcionarios (...) VALUES (...);")
            script.append("")

        script.append("COMMIT;")
        script.append("")
        script.append("-- Fim do script")

        return "\n".join(script)

    def exportar_lote(self, pedidos: List[Dict], executar_sql: bool = False) -> Dict:
        """
        Exporta um lote de pedidos.

        Args:
            pedidos: Lista de pedidos aprovados
            executar_sql: Se True, executa o SQL (não implementado ainda)

        Returns:
            Dict com resultado da exportação
        """
        if not pedidos:
            logger.warning("⚠️ Nenhum pedido para exportar")
            return {'sucesso': False, 'erro': 'Nenhum pedido fornecido'}

        lote = self.preparar_lote_exportacao(pedidos)
        lote_id = lote['lote_id']

        try:
            # 1. Gerar script SQL
            script_sql = self.gerar_script_sql(pedidos)
            arquivo_sql = os.path.join(self.dir_scripts_sql, f"lote_{lote_id}.sql")

            with open(arquivo_sql, 'w', encoding='utf-8') as f:
                f.write(script_sql)

            logger.info(f"📄 Script SQL gerado: {arquivo_sql}")

            # 2. Salvar metadados do lote
            arquivo_lote = os.path.join(self.dir_scripts_sql, f"lote_{lote_id}_metadata.json")
            with open(arquivo_lote, 'w', encoding='utf-8') as f:
                json.dump(lote, f, indent=2, ensure_ascii=False)

            logger.info(f"📋 Metadados salvos: {arquivo_lote}")

            # 3. Marcar pedidos como exportados
            if not executar_sql:
                logger.info("ℹ️ executar_sql=False - Apenas gerando scripts (exportação real desabilitada)")

            self._marcar_pedidos_exportados(pedidos, lote_id)

            # 4. Gerar relatório
            relatorio = self.gerar_relatorio_exportacao(lote, pedidos)
            arquivo_relatorio = os.path.join(self.dir_relatorios, f"export_{lote_id}.txt")

            with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
                f.write(relatorio)

            logger.info(f"📊 Relatório gerado: {arquivo_relatorio}")

            logger.info(f"✅ Exportação do lote {lote_id} concluída com sucesso")

            return {
                'sucesso': True,
                'lote_id': lote_id,
                'total_pedidos': len(pedidos),
                'arquivo_sql': arquivo_sql,
                'arquivo_relatorio': arquivo_relatorio,
                'executado': executar_sql
            }

        except Exception as e:
            logger.error(f"❌ Erro ao exportar lote: {e}")
            return {'sucesso': False, 'erro': str(e)}

    def _marcar_pedidos_exportados(self, pedidos: List[Dict], lote_id: str):
        """
        Marca pedidos como exportados nos arquivos de aprovação.

        Args:
            pedidos: Lista de pedidos
            lote_id: ID do lote de exportação
        """
        for pedido in pedidos:
            arquivo = os.path.join(
                self.dir_aprovados,
                f"ordem_{pedido['id_ordem']}_pedido_{pedido['id_pedido']}.json"
            )

            if os.path.exists(arquivo):
                try:
                    # Atualizar arquivo
                    pedido['exportado'] = True
                    pedido['data_exportacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    pedido['lote_exportacao'] = lote_id

                    with open(arquivo, 'w', encoding='utf-8') as f:
                        json.dump(pedido, f, indent=2, ensure_ascii=False)

                    logger.debug(f"✓ Pedido {pedido['id_ordem']}|{pedido['id_pedido']} marcado como exportado")

                except Exception as e:
                    logger.error(f"Erro ao marcar pedido {pedido['id_ordem']}|{pedido['id_pedido']}: {e}")

    def gerar_relatorio_exportacao(self, lote: Dict, pedidos: List[Dict]) -> str:
        """
        Gera relatório detalhado da exportação.

        Args:
            lote: Dados do lote
            pedidos: Lista de pedidos exportados

        Returns:
            str: Relatório formatado
        """
        relatorio = []

        relatorio.append("=" * 80)
        relatorio.append("💾 RELATÓRIO DE EXPORTAÇÃO PARA BANCO DE DADOS")
        relatorio.append("=" * 80)
        relatorio.append("")

        # Informações do lote
        relatorio.append(f"📦 ID do Lote: {lote['lote_id']}")
        relatorio.append(f"📅 Data: {lote['data_preparacao']}")
        relatorio.append(f"📊 Total de pedidos: {lote['total_pedidos']}")
        relatorio.append(f"🔄 Status: {lote['status']}")
        relatorio.append("")

        # Lista de pedidos
        relatorio.append("📋 PEDIDOS EXPORTADOS:")
        relatorio.append("-" * 80)

        for pedido in pedidos:
            relatorio.append(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']}")
            relatorio.append(f"     Aprovado em: {pedido.get('data_aprovacao', 'N/A')}")

            # Detalhes de equipamentos
            equip = pedido['detalhes']['equipamentos']
            relatorio.append(f"     Equipamentos: {equip['atividades_sucesso']}/{equip['total_atividades']} ✅")

            # Detalhes de funcionários
            func = pedido['detalhes']['funcionarios']
            relatorio.append(f"     Funcionários: {func['atividades_sucesso']}/{func['total_atividades']} ✅")
            relatorio.append("")

        # Resumo
        relatorio.append("=" * 80)
        relatorio.append("📊 RESUMO:")
        relatorio.append(f"   ✅ Total de pedidos exportados: {len(pedidos)}")
        relatorio.append(f"   📄 Script SQL gerado: lote_{lote['lote_id']}.sql")
        relatorio.append(f"   ⚠️ Exportação real para banco: PENDENTE (a ser implementada)")
        relatorio.append("=" * 80)

        return "\n".join(relatorio)

    def listar_historico_exportacoes(self) -> List[Dict]:
        """
        Lista histórico de exportações realizadas.

        Returns:
            List[Dict]: Lista de lotes exportados
        """
        historico = []

        if not os.path.exists(self.dir_scripts_sql):
            return historico

        for arquivo in os.listdir(self.dir_scripts_sql):
            if arquivo.endswith('_metadata.json'):
                caminho = os.path.join(self.dir_scripts_sql, arquivo)
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        lote = json.load(f)
                        historico.append(lote)
                except Exception as e:
                    logger.error(f"Erro ao ler {caminho}: {e}")

        return sorted(historico, key=lambda x: x['lote_id'], reverse=True)

    def gerar_dashboard(self) -> str:
        """
        Gera dashboard com estatísticas de exportação.

        Returns:
            str: Dashboard formatado
        """
        from services.validacao.validador_pedidos import ValidadorPedidos

        validador = ValidadorPedidos()
        aprovados = validador.listar_pedidos_aprovados()
        pendentes = [p for p in aprovados if not p.get('exportado', False)]
        exportados = [p for p in aprovados if p.get('exportado', False)]

        dashboard = []
        dashboard.append("=" * 80)
        dashboard.append("📊 DASHBOARD DE EXPORTAÇÃO")
        dashboard.append("=" * 80)
        dashboard.append("")

        # Estatísticas
        dashboard.append("📈 ESTATÍSTICAS:")
        dashboard.append(f"   Total de pedidos aprovados: {len(aprovados)}")
        dashboard.append(f"   ✅ Já exportados: {len(exportados)}")
        dashboard.append(f"   ⏳ Pendentes de exportação: {len(pendentes)}")
        dashboard.append("")

        # Pedidos pendentes
        if pendentes:
            dashboard.append("⏳ PEDIDOS PENDENTES DE EXPORTAÇÃO:")
            dashboard.append("-" * 60)
            for pedido in pendentes[:10]:  # Mostrar até 10
                dashboard.append(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']}")
                dashboard.append(f"     Aprovado em: {pedido.get('data_aprovacao', 'N/A')}")
            if len(pendentes) > 10:
                dashboard.append(f"   ... e mais {len(pendentes) - 10} pedido(s)")
            dashboard.append("")

        # Histórico de exportações
        historico = self.listar_historico_exportacoes()
        if historico:
            dashboard.append("📜 ÚLTIMAS EXPORTAÇÕES:")
            dashboard.append("-" * 60)
            for lote in historico[:5]:  # Mostrar últimas 5
                dashboard.append(f"   📦 Lote {lote['lote_id']}")
                dashboard.append(f"      Data: {lote['data_preparacao']}")
                dashboard.append(f"      Pedidos: {lote['total_pedidos']}")
            dashboard.append("")

        dashboard.append("=" * 80)

        return "\n".join(dashboard)
