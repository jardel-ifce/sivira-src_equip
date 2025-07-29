from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logs.logger_factory import setup_logger

# 🪵 Logger específico para Bancada
logger = setup_logger('Bancada')


class Bancada(Equipamento):
    """
    🪵 Classe que representa uma Bancada com controle de ocupação por frações individuais.
    Cada fração é de uso exclusivo - não permite sobreposição.
    ✔️ Ocupação individualizada por fração.
    ✔️ Cada fração pode estar livre ou ocupada independentemente.
    ✔️ Gestor controla capacidades via JSON.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        numero_fracoes: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.BANCADAS,
            status_ativo=True
        )

        self.numero_fracoes = numero_fracoes

        # 🪵 Ocupações individualizadas por fração: (id_ordem, id_pedido, id_atividade, id_item, inicio, fim)
        self.fracoes_ocupacoes: List[List[Tuple[int, int, int, int, datetime, datetime]]] = [[] for _ in range(self.numero_fracoes)]

    # ==========================================================
    # 🔍 Consulta de Ocupação (para o Gestor)
    # ==========================================================
    def obter_ocupacao_fracao(self, fracao_index: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se uma fração está ocupada no período especificado."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            return False
        
        for ocupacao in self.fracoes_ocupacoes[fracao_index]:
            if not (fim <= ocupacao[4] or inicio >= ocupacao[5]):  # há sobreposição temporal
                return True
        return False

    def obter_ocupacao_todas_fracoes(self, inicio: datetime, fim: datetime) -> List[bool]:
        """Retorna lista com o status de ocupação de todas as frações no período especificado."""
        ocupacoes = []
        for i in range(self.numero_fracoes):
            ocupacoes.append(self.obter_ocupacao_fracao(i, inicio, fim))
        return ocupacoes

    def fracao_disponivel(self, fracao_index: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se uma fração está completamente livre no período."""
        return not self.obter_ocupacao_fracao(fracao_index, inicio, fim)

    def fracoes_disponiveis_periodo(self, inicio: datetime, fim: datetime) -> List[int]:
        """Retorna lista de índices das frações completamente livres no período."""
        fracoes_livres = []
        for i in range(self.numero_fracoes):
            if self.fracao_disponivel(i, inicio, fim):
                fracoes_livres.append(i)
        return fracoes_livres

    def quantidade_fracoes_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        """Retorna quantidade de frações completamente livres no período."""
        return len(self.fracoes_disponiveis_periodo(inicio, fim))

    def verificar_espaco_fracoes(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se há frações suficientes completamente livres no período."""
        return self.quantidade_fracoes_disponiveis(inicio, fim) >= quantidade

    def encontrar_fracoes_para_ocupacao(self, quantidade: int, inicio: datetime, fim: datetime) -> Optional[List[int]]:
        """Encontra frações completamente livres para ocupação."""
        fracoes_livres = self.fracoes_disponiveis_periodo(inicio, fim)
        if len(fracoes_livres) >= quantidade:
            return fracoes_livres[:quantidade]
        return None

    def obter_ocupacoes_fracao(self, fracao_index: int) -> List[Tuple[int, int, int, int, datetime, datetime]]:
        """Retorna todas as ocupações de uma fração específica."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            return []
        return self.fracoes_ocupacoes[fracao_index].copy()

    def obter_status_fracoes(self, momento: datetime) -> List[bool]:
        """Retorna status de ocupação de cada fração em um momento específico."""
        status = []
        for fracao_index in range(self.numero_fracoes):
            ocupado = any(
                ocupacao[4] <= momento < ocupacao[5]  # inicio <= momento < fim
                for ocupacao in self.fracoes_ocupacoes[fracao_index]
            )
            status.append(ocupado)
        return status

    def obter_proxima_liberacao(self, fracao_index: int, momento_atual: datetime) -> Optional[datetime]:
        """Retorna próximo horário de liberação de uma fração específica."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            return None
        
        proximas_liberacoes = [
            ocupacao[5]  # fim
            for ocupacao in self.fracoes_ocupacoes[fracao_index]
            if ocupacao[5] > momento_atual
        ]
        
        return min(proximas_liberacoes) if proximas_liberacoes else None

    # ==========================================================
    # 🔄 Ocupação e Atualização (para o Gestor)
    # ==========================================================
    def adicionar_ocupacao_fracao(
        self,
        fracao_index: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Adiciona uma ocupação específica a uma fração específica."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            logger.warning(f"❌ Índice de fração inválido: {fracao_index}")
            return False

        # Verificar se fração está livre (uso exclusivo)
        if not self.fracao_disponivel(fracao_index, inicio, fim):
            logger.warning(
                f"❌ Fração {fracao_index} da {self.nome} não disponível entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        self.fracoes_ocupacoes[fracao_index].append(
            (id_ordem, id_pedido, id_atividade, id_item, inicio, fim)
        )

        logger.info(
            f"🪵 Ocupação adicionada na {self.nome} - Fração {fracao_index} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
            f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}"
        )
        return True

    def sobrescrever_ocupacao_fracao(
        self,
        fracao_index: int,
        ocupacoes: List[Tuple[int, int, int, int, datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações de uma fração específica."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            logger.warning(f"❌ Índice de fração inválido: {fracao_index}")
            return False

        self.fracoes_ocupacoes[fracao_index] = ocupacoes.copy()
        
        logger.info(
            f"🔄 Ocupações da fração {fracao_index} da {self.nome} foram sobrescritas. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    # ==========================================================
    # 🔐 Ocupação (Métodos de Compatibilidade)
    # ==========================================================
    def ocupar_fracoes_especificas(
        self,
        fracoes: List[int],
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Ocupa frações específicas (mantido para compatibilidade)."""
        sucesso = True
        for fracao_index in fracoes:
            if not self.adicionar_ocupacao_fracao(
                fracao_index, id_ordem, id_pedido, id_atividade, id_item, inicio, fim
            ):
                sucesso = False

        if sucesso:
            logger.info(
                f"📥 Ocupação múltipla registrada na {self.nome} | "
                f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
                f"{len(fracoes)} frações | {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
                f"Frações: {fracoes}"
            )
        return sucesso

    def ocupar_fracoes(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_fracoes: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Ocupa automaticamente a quantidade de frações necessária (mantido para compatibilidade)."""
        fracoes_para_ocupar = self.encontrar_fracoes_para_ocupacao(quantidade_fracoes, inicio, fim)
        
        if fracoes_para_ocupar is None:
            logger.warning(
                f"❌ Frações insuficientes na {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}. "
                f"Necessárias: {quantidade_fracoes}, Disponíveis: {self.quantidade_fracoes_disponiveis(inicio, fim)}"
            )
            return False

        return self.ocupar_fracoes_especificas(
            fracoes_para_ocupar, id_ordem, id_pedido, id_atividade, id_item, inicio, fim
        )

    def ocupar(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_fracoes: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Método de compatibilidade para ocupação."""
        return self.ocupar_fracoes(
            id_ordem, id_pedido, id_atividade, id_item, quantidade_fracoes, inicio, fim
        )

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.fracoes_ocupacoes[fracao_index])
            self.fracoes_ocupacoes[fracao_index] = [
                ocupacao for ocupacao in self.fracoes_ocupacoes[fracao_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
            ]
            liberadas_fracao = antes - len(self.fracoes_ocupacoes[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """Libera ocupações específicas por pedido."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.fracoes_ocupacoes[fracao_index])
            self.fracoes_ocupacoes[fracao_index] = [
                ocupacao for ocupacao in self.fracoes_ocupacoes[fracao_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
            ]
            liberadas_fracao = antes - len(self.fracoes_ocupacoes[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_ordem(self, id_ordem: int):
        """Libera ocupações específicas por ordem."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.fracoes_ocupacoes[fracao_index])
            self.fracoes_ocupacoes[fracao_index] = [
                ocupacao for ocupacao in self.fracoes_ocupacoes[fracao_index]
                if ocupacao[0] != id_ordem
            ]
            liberadas_fracao = antes - len(self.fracoes_ocupacoes[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} "
                f"para Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Ordem {id_ordem}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.fracoes_ocupacoes[fracao_index])
            self.fracoes_ocupacoes[fracao_index] = [
                ocupacao for ocupacao in self.fracoes_ocupacoes[fracao_index]
                if ocupacao[5] > horario_atual  # fim > horario_atual
            ]
            liberadas_fracao = antes - len(self.fracoes_ocupacoes[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} finalizadas até {horario_atual.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar na {self.nome} até {horario_atual.strftime('%H:%M')}."
            )
        return total_liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações de todas as frações."""
        total = sum(len(ocupacoes) for ocupacoes in self.fracoes_ocupacoes)
        for fracao_ocupacoes in self.fracoes_ocupacoes:
            fracao_ocupacoes.clear()
        logger.info(f"🔓 Todas as {total} ocupações da {self.nome} foram removidas.")

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.fracoes_ocupacoes[fracao_index])
            self.fracoes_ocupacoes[fracao_index] = [
                ocupacao for ocupacao in self.fracoes_ocupacoes[fracao_index]
                if not (ocupacao[4] < fim and ocupacao[5] > inicio)  # remove qualquer sobreposição
            ]
            liberadas_fracao = antes - len(self.fracoes_ocupacoes[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )

    def liberar_fracao_especifica(self, fracao_index: int, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupação específica de uma fração."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            logger.warning(f"❌ Índice de fração inválido: {fracao_index}")
            return

        antes = len(self.fracoes_ocupacoes[fracao_index])
        self.fracoes_ocupacoes[fracao_index] = [
            ocupacao for ocupacao in self.fracoes_ocupacoes[fracao_index]
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]
        liberadas = antes - len(self.fracoes_ocupacoes[fracao_index])
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da fração {fracao_index} da {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada por fração."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")

        tem_ocupacao = False
        for fracao_index in range(self.numero_fracoes):
            if self.fracoes_ocupacoes[fracao_index]:
                tem_ocupacao = True
                logger.info(f"🔹 Fração {fracao_index + 1}:")
                for ocupacao in self.fracoes_ocupacoes[fracao_index]:
                    logger.info(
                        f"   🪵 Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                        f"{ocupacao[4].strftime('%H:%M')} → {ocupacao[5].strftime('%H:%M')}"
                    )

        if not tem_ocupacao:
            logger.info("🔹 Nenhuma ocupação registrada em nenhuma fração.")

    def obter_estatisticas_uso(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso da bancada no período."""
        total_ocupacoes = 0
        fracoes_utilizadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            ocupacoes_fracao = []
            for ocupacao in self.fracoes_ocupacoes[fracao_index]:
                if not (fim <= ocupacao[4] or inicio >= ocupacao[5]):  # há sobreposição temporal
                    ocupacoes_fracao.append(ocupacao)
            
            if ocupacoes_fracao:
                fracoes_utilizadas += 1
                total_ocupacoes += len(ocupacoes_fracao)
        
        taxa_utilizacao_fracoes = (fracoes_utilizadas / self.numero_fracoes * 100) if self.numero_fracoes > 0 else 0.0
        
        return {
            'fracoes_utilizadas': fracoes_utilizadas,
            'fracoes_total': self.numero_fracoes,
            'taxa_utilizacao_fracoes': taxa_utilizacao_fracoes,
            'total_ocupacoes': total_ocupacoes
        }

    def obter_distribuicao_fracoes_periodo(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna distribuição de uso de frações por atividade no período."""
        distribuicao = {}
        
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.fracoes_ocupacoes[fracao_index]:
                if not (fim <= ocupacao[4] or inicio >= ocupacao[5]):  # há sobreposição temporal
                    key = f"Atividade_{ocupacao[2]}"  # id_atividade
                    if key not in distribuicao:
                        distribuicao[key] = {
                            'fracoes_utilizadas': set(),
                            'ocupacoes_count': 0
                        }
                    
                    distribuicao[key]['fracoes_utilizadas'].add(fracao_index)
                    distribuicao[key]['ocupacoes_count'] += 1
        
        # Converter sets para contadores
        for key in distribuicao:
            distribuicao[key]['fracoes_utilizadas'] = len(distribuicao[key]['fracoes_utilizadas'])
        
        return distribuicao