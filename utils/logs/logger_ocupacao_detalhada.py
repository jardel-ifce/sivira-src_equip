"""
Logger para Ocupação Detalhada de Equipamentos
=============================================

Sistema de logging específico para capturar detalhes técnicos dos equipamentos:
- Bocas do fogão (chamas, pressões, quantidades)
- Frações de bancadas e fritadeiras
- Níveis e caixas de refrigeração/congelamento
- Configurações específicas de cada equipamento

Formato de saída: logs/equipamentos_detalhados/
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class TipoLogDetalhado(Enum):
    """Tipos de log detalhado por equipamento"""
    FOGAO_BOCA = "fogao_boca"
    BANCADA_FRACAO = "bancada_fracao"
    FRITADEIRA_FRACAO = "fritadeira_fracao"
    REFRIGERADOR_NIVEL = "refrigerador_nivel"
    HOTMIX_JANELA = "hotmix_janela"
    BALANCA_PESAGEM = "balanca_pesagem"


class LoggerOcupacaoDetalhada:
    """
    📋 Logger especializado para capturar detalhes técnicos de ocupação dos equipamentos
    """

    def __init__(self, pasta_logs: str = "logs/equipamentos_detalhados"):
        self.pasta_logs = pasta_logs
        self.logs_buffer: Dict[str, List[Dict]] = {}
        self._garantir_pasta_existe()

    def _garantir_pasta_existe(self):
        """Garante que a pasta de logs existe"""
        os.makedirs(self.pasta_logs, exist_ok=True)

    def _obter_timestamp(self) -> str:
        """Retorna timestamp atual formatado"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _obter_nome_arquivo(self, id_ordem: int, id_pedido: int) -> str:
        """Retorna nome do arquivo de log para ordem/pedido"""
        return f"detalhes_ordem_{id_ordem}_pedido_{id_pedido}.log"

    def registrar_ocupacao_fogao_boca(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_equipamento: str,
        boca_numero: int,
        id_item: int,
        nome_item: str,
        quantidade_gramas: float,
        tipo_chama: str,
        pressoes_chama: List[str],
        inicio: datetime,
        fim: datetime,
        observacoes: Optional[str] = None
    ):
        """
        🔥 Registra ocupação detalhada de boca do fogão
        """
        registro = {
            "timestamp": self._obter_timestamp(),
            "tipo": TipoLogDetalhado.FOGAO_BOCA.value,
            "equipamento": nome_equipamento,
            "detalhes": {
                "boca_numero": boca_numero,
                "id_item": id_item,
                "nome_item": nome_item,
                "quantidade_gramas": quantidade_gramas,
                "tipo_chama": tipo_chama,
                "pressoes_chama": pressoes_chama,
                "configuracao": f"Boca {boca_numero} - {tipo_chama} - {', '.join(pressoes_chama)}"
            },
            "atividade": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_atividade": id_atividade,
                "inicio": inicio.strftime("%H:%M [%d/%m]"),
                "fim": fim.strftime("%H:%M [%d/%m]"),
                "duracao_minutos": int((fim - inicio).total_seconds() / 60)
            },
            "observacoes": observacoes
        }

        self._adicionar_registro(id_ordem, id_pedido, registro)

    def registrar_ocupacao_bancada_fracao(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_equipamento: str,
        fracao_numero: int,
        total_fracoes: int,
        id_item: int,
        nome_item: str,
        tipo_atividade: str,
        inicio: datetime,
        fim: datetime,
        observacoes: Optional[str] = None
    ):
        """
        🛠️ Registra ocupação detalhada de fração da bancada
        """
        registro = {
            "timestamp": self._obter_timestamp(),
            "tipo": TipoLogDetalhado.BANCADA_FRACAO.value,
            "equipamento": nome_equipamento,
            "detalhes": {
                "fracao_numero": fracao_numero,
                "total_fracoes": total_fracoes,
                "percentual_uso": f"{(1/total_fracoes)*100:.1f}%",
                "id_item": id_item,
                "nome_item": nome_item,
                "tipo_atividade": tipo_atividade,
                "configuracao": f"Fração {fracao_numero}/{total_fracoes} - {tipo_atividade}"
            },
            "atividade": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_atividade": id_atividade,
                "inicio": inicio.strftime("%H:%M [%d/%m]"),
                "fim": fim.strftime("%H:%M [%d/%m]"),
                "duracao_minutos": int((fim - inicio).total_seconds() / 60)
            },
            "observacoes": observacoes
        }

        self._adicionar_registro(id_ordem, id_pedido, registro)

    def registrar_ocupacao_fritadeira_fracao(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_equipamento: str,
        fracao_numero: int,
        total_fracoes: int,
        id_item: int,
        nome_item: str,
        quantidade_gramas: float,
        temperatura: Optional[float],
        inicio: datetime,
        fim: datetime,
        observacoes: Optional[str] = None
    ):
        """
        🍳 Registra ocupação detalhada de fração da fritadeira
        """
        registro = {
            "timestamp": self._obter_timestamp(),
            "tipo": TipoLogDetalhado.FRITADEIRA_FRACAO.value,
            "equipamento": nome_equipamento,
            "detalhes": {
                "fracao_numero": fracao_numero,
                "total_fracoes": total_fracoes,
                "percentual_uso": f"{(1/total_fracoes)*100:.1f}%",
                "id_item": id_item,
                "nome_item": nome_item,
                "quantidade_gramas": quantidade_gramas,
                "temperatura": temperatura,
                "configuracao": f"Fração {fracao_numero}/{total_fracoes} - {quantidade_gramas}g"
            },
            "atividade": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_atividade": id_atividade,
                "inicio": inicio.strftime("%H:%M [%d/%m]"),
                "fim": fim.strftime("%H:%M [%d/%m]"),
                "duracao_minutos": int((fim - inicio).total_seconds() / 60)
            },
            "observacoes": observacoes
        }

        self._adicionar_registro(id_ordem, id_pedido, registro)

    def registrar_ocupacao_refrigerador_nivel(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_equipamento: str,
        nivel_numero: int,
        caixa_numero: int,
        id_item: int,
        nome_item: str,
        temperatura_configurada: float,
        capacidade_utilizada: float,
        inicio: datetime,
        fim: datetime,
        observacoes: Optional[str] = None
    ):
        """
        ❄️ Registra ocupação detalhada de nível/caixa do refrigerador
        """
        registro = {
            "timestamp": self._obter_timestamp(),
            "tipo": TipoLogDetalhado.REFRIGERADOR_NIVEL.value,
            "equipamento": nome_equipamento,
            "detalhes": {
                "nivel_numero": nivel_numero,
                "caixa_numero": caixa_numero,
                "id_item": id_item,
                "nome_item": nome_item,
                "temperatura_configurada": temperatura_configurada,
                "capacidade_utilizada": capacidade_utilizada,
                "configuracao": f"Nível {nivel_numero} / Caixa {caixa_numero} - {temperatura_configurada}°C"
            },
            "atividade": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_atividade": id_atividade,
                "inicio": inicio.strftime("%H:%M [%d/%m]"),
                "fim": fim.strftime("%H:%M [%d/%m]"),
                "duracao_minutos": int((fim - inicio).total_seconds() / 60)
            },
            "observacoes": observacoes
        }

        self._adicionar_registro(id_ordem, id_pedido, registro)

    def registrar_ocupacao_hotmix_janela(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_equipamento: str,
        id_item: int,
        nome_item: str,
        quantidade_gramas: float,
        capacidade_minima: float,
        capacidade_maxima: float,
        janela_simultanea: bool,
        inicio: datetime,
        fim: datetime,
        observacoes: Optional[str] = None
    ):
        """
        🌪️ Registra ocupação detalhada de janela do HotMix
        """
        registro = {
            "timestamp": self._obter_timestamp(),
            "tipo": TipoLogDetalhado.HOTMIX_JANELA.value,
            "equipamento": nome_equipamento,
            "detalhes": {
                "id_item": id_item,
                "nome_item": nome_item,
                "quantidade_gramas": quantidade_gramas,
                "capacidade_minima": capacidade_minima,
                "capacidade_maxima": capacidade_maxima,
                "janela_simultanea": janela_simultanea,
                "percentual_capacidade": f"{(quantidade_gramas/capacidade_maxima)*100:.1f}%",
                "configuracao": f"Janela {'Simultânea' if janela_simultanea else 'Individual'} - {quantidade_gramas}g"
            },
            "atividade": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_atividade": id_atividade,
                "inicio": inicio.strftime("%H:%M [%d/%m]"),
                "fim": fim.strftime("%H:%M [%d/%m]"),
                "duracao_minutos": int((fim - inicio).total_seconds() / 60)
            },
            "observacoes": observacoes
        }

        self._adicionar_registro(id_ordem, id_pedido, registro)

    def registrar_ocupacao_balanca_pesagem(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_equipamento: str,
        id_item: int,
        nome_item: str,
        peso_medido: float,
        precisao_equipamento: float,
        tipo_operacao: str,
        inicio: datetime,
        fim: datetime,
        observacoes: Optional[str] = None
    ):
        """
        ⚖️ Registra ocupação detalhada da balança
        """
        registro = {
            "timestamp": self._obter_timestamp(),
            "tipo": TipoLogDetalhado.BALANCA_PESAGEM.value,
            "equipamento": nome_equipamento,
            "detalhes": {
                "id_item": id_item,
                "nome_item": nome_item,
                "peso_medido": peso_medido,
                "precisao_equipamento": precisao_equipamento,
                "tipo_operacao": tipo_operacao,
                "configuracao": f"Pesagem {tipo_operacao} - {peso_medido}g (±{precisao_equipamento}g)"
            },
            "atividade": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_atividade": id_atividade,
                "inicio": inicio.strftime("%H:%M [%d/%m]"),
                "fim": fim.strftime("%H:%M [%d/%m]"),
                "duracao_minutos": int((fim - inicio).total_seconds() / 60)
            },
            "observacoes": observacoes
        }

        self._adicionar_registro(id_ordem, id_pedido, registro)

    def _adicionar_registro(self, id_ordem: int, id_pedido: int, registro: Dict[str, Any]):
        """Adiciona registro ao buffer"""
        chave = f"ordem_{id_ordem}_pedido_{id_pedido}"

        if chave not in self.logs_buffer:
            self.logs_buffer[chave] = []

        self.logs_buffer[chave].append(registro)

    def salvar_logs_ordem_pedido(self, id_ordem: int, id_pedido: int) -> Optional[str]:
        """
        💾 Salva todos os logs de uma ordem/pedido em arquivo
        """
        chave = f"ordem_{id_ordem}_pedido_{id_pedido}"

        if chave not in self.logs_buffer or not self.logs_buffer[chave]:
            return None

        try:
            nome_arquivo = self._obter_nome_arquivo(id_ordem, id_pedido)
            caminho_completo = os.path.join(self.pasta_logs, nome_arquivo)

            # Ordenar registros por timestamp
            registros = sorted(self.logs_buffer[chave], key=lambda x: x['atividade']['inicio'])

            with open(caminho_completo, 'w', encoding='utf-8') as f:
                # Cabeçalho
                f.write("=" * 80 + "\n")
                f.write(f"📋 LOG DETALHADO DE OCUPAÇÃO - Ordem {id_ordem} | Pedido {id_pedido}\n")
                f.write("=" * 80 + "\n")
                f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Total de ocupações registradas: {len(registros)}\n")
                f.write("=" * 80 + "\n\n")

                # Registros agrupados por equipamento
                equipamentos = {}
                for registro in registros:
                    equipamento = registro['equipamento']
                    if equipamento not in equipamentos:
                        equipamentos[equipamento] = []
                    equipamentos[equipamento].append(registro)

                for equipamento, regs in equipamentos.items():
                    f.write(f"\n🔧 {equipamento}\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"📊 Ocupações registradas: {len(regs)}\n\n")

                    for i, reg in enumerate(regs, 1):
                        self._escrever_registro_formatado(f, i, reg)

                    f.write("-" * 50 + "\n")

                # Resumo final
                f.write("\n" + "=" * 80 + "\n")
                f.write("📊 RESUMO FINAL\n")
                f.write("=" * 80 + "\n")

                tipos_ocupacao = {}
                for reg in registros:
                    tipo = reg['tipo']
                    if tipo not in tipos_ocupacao:
                        tipos_ocupacao[tipo] = 0
                    tipos_ocupacao[tipo] += 1

                f.write("🏷️ TIPOS DE OCUPAÇÃO:\n")
                for tipo, count in tipos_ocupacao.items():
                    f.write(f"   • {tipo.replace('_', ' ').title()}: {count} ocupações\n")

                duracao_total = sum(reg['atividade']['duracao_minutos'] for reg in registros)
                f.write(f"\n⏱️ Duração total acumulada: {duracao_total} minutos\n")
                f.write(f"📈 Equipamentos únicos utilizados: {len(equipamentos)}\n")

                f.write("\n" + "=" * 80 + "\n")

            # Limpar buffer após salvar
            del self.logs_buffer[chave]

            return caminho_completo

        except Exception as e:
            print(f"❌ Erro ao salvar log detalhado para ordem {id_ordem}/pedido {id_pedido}: {e}")
            return None

    def _escrever_registro_formatado(self, arquivo, numero: int, registro: Dict[str, Any]):
        """Escreve registro formatado no arquivo"""
        arquivo.write(f"📋 OCUPAÇÃO {numero}\n")
        arquivo.write(f"   🕒 {registro['atividade']['inicio']} - {registro['atividade']['fim']} ({registro['atividade']['duracao_minutos']}min)\n")
        arquivo.write(f"   🆔 Atividade: {registro['atividade']['id_atividade']}\n")
        arquivo.write(f"   🏷️ Tipo: {registro['tipo'].replace('_', ' ').title()}\n")

        detalhes = registro['detalhes']
        arquivo.write(f"   ⚙️ Configuração: {detalhes['configuracao']}\n")
        arquivo.write(f"   📦 Item: {detalhes['nome_item']} (ID: {detalhes['id_item']})\n")

        # Detalhes específicos por tipo
        if registro['tipo'] == TipoLogDetalhado.FOGAO_BOCA.value:
            arquivo.write(f"   🔥 Quantidade: {detalhes['quantidade_gramas']}g\n")
            arquivo.write(f"   🔥 Chama: {detalhes['tipo_chama']}\n")
            arquivo.write(f"   🔥 Pressões: {', '.join(detalhes['pressoes_chama'])}\n")

        elif registro['tipo'] in [TipoLogDetalhado.BANCADA_FRACAO.value, TipoLogDetalhado.FRITADEIRA_FRACAO.value]:
            arquivo.write(f"   📐 Fração: {detalhes['fracao_numero']}/{detalhes['total_fracoes']} ({detalhes['percentual_uso']})\n")
            if 'quantidade_gramas' in detalhes:
                arquivo.write(f"   ⚖️ Quantidade: {detalhes['quantidade_gramas']}g\n")
            if 'temperatura' in detalhes and detalhes['temperatura']:
                arquivo.write(f"   🌡️ Temperatura: {detalhes['temperatura']}°C\n")

        elif registro['tipo'] == TipoLogDetalhado.REFRIGERADOR_NIVEL.value:
            arquivo.write(f"   ❄️ Nível/Caixa: {detalhes['nivel_numero']}/{detalhes['caixa_numero']}\n")
            arquivo.write(f"   🌡️ Temperatura: {detalhes['temperatura_configurada']}°C\n")
            arquivo.write(f"   📦 Capacidade: {detalhes['capacidade_utilizada']}\n")

        elif registro['tipo'] == TipoLogDetalhado.HOTMIX_JANELA.value:
            arquivo.write(f"   🌪️ Quantidade: {detalhes['quantidade_gramas']}g ({detalhes['percentual_capacidade']})\n")
            arquivo.write(f"   📏 Capacidade: {detalhes['capacidade_minima']}-{detalhes['capacidade_maxima']}g\n")
            arquivo.write(f"   🔄 Janela: {'Simultânea' if detalhes['janela_simultanea'] else 'Individual'}\n")

        elif registro['tipo'] == TipoLogDetalhado.BALANCA_PESAGEM.value:
            arquivo.write(f"   ⚖️ Peso: {detalhes['peso_medido']}g (±{detalhes['precisao_equipamento']}g)\n")
            arquivo.write(f"   🎯 Operação: {detalhes['tipo_operacao']}\n")

        if registro.get('observacoes'):
            arquivo.write(f"   💬 Observações: {registro['observacoes']}\n")

        arquivo.write("\n")

    def limpar_buffer(self):
        """Limpa todos os buffers de logs"""
        self.logs_buffer.clear()

    def remover_logs_ordem_pedido(self, id_ordem: int, id_pedido: int) -> bool:
        """
        🗑️ Remove logs detalhados de uma ordem/pedido específico (para rollback)
        """
        try:
            nome_arquivo = self._obter_nome_arquivo(id_ordem, id_pedido)
            caminho_completo = os.path.join(self.pasta_logs, nome_arquivo)

            # Remove arquivo se existir
            if os.path.exists(caminho_completo):
                os.remove(caminho_completo)
                logger.info(f"🗑️ Log detalhado removido: {caminho_completo}")

            # Remove do buffer se estiver lá
            chave = f"ordem_{id_ordem}_pedido_{id_pedido}"
            if chave in self.logs_buffer:
                del self.logs_buffer[chave]

            return True

        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover log detalhado ordem {id_ordem}/pedido {id_pedido}: {e}")
            return False

    def rollback_ordem_pedido(self, id_ordem: int, id_pedido: int):
        """
        🔄 Executa rollback completo dos logs detalhados para uma ordem/pedido
        Alias para remover_logs_ordem_pedido para compatibilidade com sistema de rollback
        """
        return self.remover_logs_ordem_pedido(id_ordem, id_pedido)

    def obter_estatisticas_buffer(self) -> Dict[str, Any]:
        """Retorna estatísticas dos logs em buffer"""
        return {
            "ordens_pedidos_em_buffer": len(self.logs_buffer),
            "total_registros": sum(len(registros) for registros in self.logs_buffer.values()),
            "tipos_ocupacao": self._contar_tipos_ocupacao()
        }

    def _contar_tipos_ocupacao(self) -> Dict[str, int]:
        """Conta tipos de ocupação nos buffers"""
        contadores = {}
        for registros in self.logs_buffer.values():
            for registro in registros:
                tipo = registro['tipo']
                contadores[tipo] = contadores.get(tipo, 0) + 1
        return contadores


# Instância global para uso em todo o sistema
logger_ocupacao_detalhada = LoggerOcupacaoDetalhada()