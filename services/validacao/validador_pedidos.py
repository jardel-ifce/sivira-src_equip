#!/usr/bin/env python3
"""
📋 VALIDADOR DE PEDIDOS
======================

Valida se pedidos estão completos (equipamentos + funcionários) antes de exportar para o banco.

Regras de validação:
- Equipamentos: Todas as atividades devem ter ✅
- Funcionários: Todas as atividades devem ter ✅
- Se qualquer validação falhar, o pedido é CANCELADO
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from utils.logs.logger_factory import setup_logger

logger = setup_logger("ValidadorPedidos")


class StatusValidacao:
    """Status possíveis de validação."""
    APROVADO = "aprovado"
    CANCELADO = "cancelado"
    PENDENTE = "pendente"


class ValidadorPedidos:
    """
    Valida pedidos verificando se todas as alocações (equipamentos + funcionários) foram bem-sucedidas.
    """

    def __init__(self):
        self.dir_equipamentos_sucesso = "logs/equipamentos/sucesso"
        self.dir_equipamentos_erros = "logs/equipamentos/erros"
        self.dir_funcionarios_sucesso = "logs/funcionarios/sucesso"
        self.dir_funcionarios_erro = "logs/funcionarios/erro"
        self.dir_aprovados = "logs/validacao/aprovados"
        self.dir_cancelados = "logs/validacao/cancelados"
        self.dir_pendentes = "logs/validacao/pendentes"

        # Criar diretórios se não existirem
        for diretorio in [self.dir_aprovados, self.dir_cancelados, self.dir_pendentes]:
            os.makedirs(diretorio, exist_ok=True)

    def validar_pedido(self, id_ordem: int, id_pedido: int, cancelar_se_invalido: bool = True) -> Dict:
        """
        Valida um pedido específico verificando equipamentos e funcionários.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            cancelar_se_invalido: Se True, cancela automaticamente pedidos inválidos

        Returns:
            Dict com resultado da validação
        """
        logger.info(f"🔍 Iniciando validação: Ordem {id_ordem} | Pedido {id_pedido}")

        resultado = {
            'id_ordem': id_ordem,
            'id_pedido': id_pedido,
            'valido': False,
            'equipamentos_ok': False,
            'funcionarios_ok': False,
            'status': StatusValidacao.PENDENTE,
            'data_validacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'detalhes': {}
        }

        # 1. Validar equipamentos
        equip_valido, equip_detalhes = self.validar_equipamentos(id_ordem, id_pedido)
        resultado['equipamentos_ok'] = equip_valido
        resultado['detalhes']['equipamentos'] = equip_detalhes

        # 2. Validar funcionários
        func_valido, func_detalhes = self.validar_funcionarios(id_ordem, id_pedido)
        resultado['funcionarios_ok'] = func_valido
        resultado['detalhes']['funcionarios'] = func_detalhes

        # 3. Determinar status
        if equip_valido and func_valido:
            resultado['valido'] = True
            resultado['status'] = StatusValidacao.APROVADO
            logger.info(f"✅ Pedido {id_ordem}|{id_pedido} VÁLIDO - pode ser exportado")
            self.aprovar_pedido(id_ordem, id_pedido, resultado)
        else:
            motivos = []
            if not equip_valido:
                motivos.append(equip_detalhes.get('motivo', 'Falha na alocação de equipamentos'))
            if not func_valido:
                motivos.append(func_detalhes.get('motivo', 'Falha na alocação de funcionários'))

            resultado['status'] = StatusValidacao.CANCELADO
            resultado['motivo_cancelamento'] = '; '.join(motivos)

            logger.warning(f"❌ Pedido {id_ordem}|{id_pedido} INVÁLIDO - {resultado['motivo_cancelamento']}")

            if cancelar_se_invalido:
                self.cancelar_pedido(id_ordem, id_pedido, resultado['motivo_cancelamento'], resultado)

        return resultado

    def validar_equipamentos(self, id_ordem: int, id_pedido: int) -> Tuple[bool, Dict]:
        """
        Verifica se todas as atividades de equipamentos foram alocadas com sucesso.

        ✅ NOVA REGRA SIMPLIFICADA:
        - Arquivo em /equipamentos/sucesso → APROVADO
        - Arquivo em /equipamentos/erros → REPROVADO
        - Arquivo não existe → REPROVADO

        Returns:
            Tuple[bool, Dict]: (valido, detalhes)
        """
        nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
        arquivo_sucesso = os.path.join(self.dir_equipamentos_sucesso, nome_arquivo)
        arquivo_erro = os.path.join(self.dir_equipamentos_erros, nome_arquivo)

        detalhes = {
            'total_atividades': 0,
            'atividades_sucesso': 0,
            'atividades_falha': 0,
            'arquivo_log': None,
            'motivo': None
        }

        # 1. Verificar se está na pasta de sucesso
        if os.path.exists(arquivo_sucesso):
            detalhes['arquivo_log'] = arquivo_sucesso

            try:
                # Contar atividades bem-sucedidas
                with open(arquivo_sucesso, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if not linha or not linha[0].isdigit():
                            continue
                        detalhes['total_atividades'] += 1
                        detalhes['atividades_sucesso'] += 1

                if detalhes['total_atividades'] == 0:
                    detalhes['motivo'] = "Arquivo de sucesso está vazio"
                    return False, detalhes

                logger.info(f"✅ Equipamentos OK: {detalhes['atividades_sucesso']}/{detalhes['total_atividades']} (pasta /sucesso)")
                return True, detalhes

            except Exception as e:
                detalhes['motivo'] = f"Erro ao ler log de sucesso: {e}"
                logger.error(detalhes['motivo'])
                return False, detalhes

        # 2. Verificar se está na pasta de erros
        elif os.path.exists(arquivo_erro):
            detalhes['arquivo_log'] = arquivo_erro
            detalhes['motivo'] = "Pedido tem erros de alocação de equipamentos"
            logger.warning(f"❌ Equipamentos FALHOU: {detalhes['motivo']} (pasta /erros)")
            return False, detalhes

        # 3. Arquivo não encontrado em nenhuma pasta
        else:
            detalhes['motivo'] = f"Arquivo de log de equipamentos não encontrado em /sucesso nem /erros"
            logger.warning(f"⚠️ {detalhes['motivo']}")
            return False, detalhes

    def validar_funcionarios(self, id_ordem: int, id_pedido: int) -> Tuple[bool, Dict]:
        """
        Verifica se todas as atividades de funcionários foram alocadas com sucesso.

        ✅ NOVA REGRA SIMPLIFICADA:
        - Arquivo em /funcionarios/sucesso → APROVADO
        - Arquivo em /funcionarios/erro → REPROVADO
        - Arquivo não existe → REPROVADO

        Returns:
            Tuple[bool, Dict]: (valido, detalhes)
        """
        nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
        arquivo_sucesso = os.path.join(self.dir_funcionarios_sucesso, nome_arquivo)
        arquivo_erro = os.path.join(self.dir_funcionarios_erro, nome_arquivo)

        detalhes = {
            'total_atividades': 0,
            'atividades_sucesso': 0,
            'atividades_falha': 0,
            'arquivo_log': None,
            'motivo': None
        }

        # 1. Verificar se está na pasta de sucesso
        if os.path.exists(arquivo_sucesso):
            detalhes['arquivo_log'] = arquivo_sucesso

            try:
                # Contar atividades bem-sucedidas
                with open(arquivo_sucesso, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if not linha or not linha[0].isdigit():
                            continue
                        detalhes['total_atividades'] += 1
                        if '✅' in linha:
                            detalhes['atividades_sucesso'] += 1

                if detalhes['total_atividades'] == 0:
                    detalhes['motivo'] = "Arquivo de sucesso está vazio"
                    return False, detalhes

                logger.info(f"✅ Funcionários OK: {detalhes['atividades_sucesso']}/{detalhes['total_atividades']} (pasta /sucesso)")
                return True, detalhes

            except Exception as e:
                detalhes['motivo'] = f"Erro ao ler log de sucesso: {e}"
                logger.error(detalhes['motivo'])
                return False, detalhes

        # 2. Verificar se está na pasta de erro
        elif os.path.exists(arquivo_erro):
            detalhes['arquivo_log'] = arquivo_erro

            try:
                # Contar atividades com erro
                with open(arquivo_erro, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if not linha or not linha[0].isdigit():
                            continue
                        detalhes['total_atividades'] += 1

                        if 'Funcionário Indisponível' in linha:
                            detalhes['atividades_falha'] += 1
                        elif '✅' in linha:
                            detalhes['atividades_sucesso'] += 1

                detalhes['motivo'] = f"Pelo menos uma atividade com Funcionário Indisponível ({detalhes['atividades_falha']} falha(s))"
                logger.warning(f"❌ Funcionários FALHOU: {detalhes['motivo']} (pasta /erro)")
                return False, detalhes

            except Exception as e:
                detalhes['motivo'] = f"Erro ao ler log de erro: {e}"
                logger.error(detalhes['motivo'])
                return False, detalhes

        # 3. Arquivo não encontrado em nenhuma pasta
        else:
            detalhes['motivo'] = f"Arquivo de log de funcionários não encontrado em /sucesso nem /erro"
            logger.warning(f"⚠️ {detalhes['motivo']}")
            return False, detalhes

    def aprovar_pedido(self, id_ordem: int, id_pedido: int, dados_validacao: Dict):
        """
        Aprova um pedido, salvando-o em logs/validacao/aprovados/.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            dados_validacao: Dados da validação
        """
        arquivo_aprovacao = os.path.join(self.dir_aprovados, f"ordem_{id_ordem}_pedido_{id_pedido}.json")

        dados_aprovacao = {
            **dados_validacao,
            'aprovado_por': 'sistema',
            'data_aprovacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_exportacao': None,
            'exportado': False
        }

        try:
            with open(arquivo_aprovacao, 'w', encoding='utf-8') as f:
                json.dump(dados_aprovacao, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Pedido {id_ordem}|{id_pedido} APROVADO e salvo em {arquivo_aprovacao}")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar aprovação: {e}")

    def cancelar_pedido(self, id_ordem: int, id_pedido: int, motivo: str, dados_validacao: Dict):
        """
        Cancela um pedido, salvando-o em logs/validacao/cancelados/.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            motivo: Motivo do cancelamento
            dados_validacao: Dados da validação
        """
        arquivo_cancelamento = os.path.join(self.dir_cancelados, f"ordem_{id_ordem}_pedido_{id_pedido}.json")

        dados_cancelamento = {
            **dados_validacao,
            'motivo_cancelamento': motivo,
            'cancelado_por': 'sistema',
            'data_cancelamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            with open(arquivo_cancelamento, 'w', encoding='utf-8') as f:
                json.dump(dados_cancelamento, f, indent=2, ensure_ascii=False)

            logger.warning(f"❌ Pedido {id_ordem}|{id_pedido} CANCELADO: {motivo}")
            logger.info(f"📄 Detalhes salvos em {arquivo_cancelamento}")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar cancelamento: {e}")

    def listar_pedidos_aprovados(self) -> List[Dict]:
        """Lista todos os pedidos aprovados."""
        return self._listar_pedidos_por_status(self.dir_aprovados)

    def listar_pedidos_cancelados(self) -> List[Dict]:
        """Lista todos os pedidos cancelados."""
        return self._listar_pedidos_por_status(self.dir_cancelados)

    def _listar_pedidos_por_status(self, diretorio: str) -> List[Dict]:
        """Lista pedidos de um diretório específico."""
        pedidos = []

        if not os.path.exists(diretorio):
            return pedidos

        for arquivo in os.listdir(diretorio):
            if arquivo.endswith('.json'):
                caminho = os.path.join(diretorio, arquivo)
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        pedido = json.load(f)
                        pedidos.append(pedido)
                except Exception as e:
                    logger.error(f"Erro ao ler {caminho}: {e}")

        return sorted(pedidos, key=lambda x: (x['id_ordem'], x['id_pedido']))

    def gerar_relatorio_validacao(self) -> str:
        """Gera relatório com estatísticas de validação."""
        aprovados = self.listar_pedidos_aprovados()
        cancelados = self.listar_pedidos_cancelados()

        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("📋 RELATÓRIO DE VALIDAÇÃO DE PEDIDOS")
        relatorio.append("=" * 80)
        relatorio.append("")

        # Estatísticas gerais
        total = len(aprovados) + len(cancelados)
        relatorio.append("📊 ESTATÍSTICAS GERAIS:")
        relatorio.append(f"   Total de pedidos validados: {total}")
        relatorio.append(f"   ✅ Aprovados: {len(aprovados)} ({len(aprovados)/total*100 if total > 0 else 0:.1f}%)")
        relatorio.append(f"   ❌ Cancelados: {len(cancelados)} ({len(cancelados)/total*100 if total > 0 else 0:.1f}%)")
        relatorio.append("")

        # Pedidos aprovados
        if aprovados:
            relatorio.append("✅ PEDIDOS APROVADOS (prontos para exportação):")
            relatorio.append("-" * 60)
            for pedido in aprovados:
                exportado = "✓ Exportado" if pedido.get('exportado', False) else "○ Pendente exportação"
                relatorio.append(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']} - {exportado}")
                relatorio.append(f"     Aprovado em: {pedido.get('data_aprovacao', 'N/A')}")
            relatorio.append("")

        # Pedidos cancelados
        if cancelados:
            relatorio.append("❌ PEDIDOS CANCELADOS:")
            relatorio.append("-" * 60)
            for pedido in cancelados:
                relatorio.append(f"   • Ordem {pedido['id_ordem']} | Pedido {pedido['id_pedido']}")
                relatorio.append(f"     Motivo: {pedido.get('motivo_cancelamento', 'N/A')}")
                relatorio.append(f"     Cancelado em: {pedido.get('data_cancelamento', 'N/A')}")
            relatorio.append("")

        relatorio.append("=" * 80)
        return "\n".join(relatorio)
