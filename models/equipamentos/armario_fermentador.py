from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logs.logger_factory import setup_logger

# 🗄️ Logger específico para o Armário Fermentador
logger = setup_logger('ArmarioFermentador')


class ArmarioFermentador(Equipamento):
    """
    🗄️ Representa um ArmárioFermentador para fermentação.
    ✔️ Armazenamento exclusivo por níveis de tela individualizados.
    ✔️ Sem controle de temperatura.
    ✔️ Controle individual de ocupação por nível de tela.
    ✔️ Capacidade total = capacidade_niveis × (nivel_tela_max - nivel_tela_min + 1).
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
        nivel_tela_min: int,
        nivel_tela_max: int,
        capacidade_niveis: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.ARMARIOS_PARA_FERMENTACAO,
            setor=setor,
            numero_operadores=0,
            status_ativo=True,
        )

        self.nivel_tela_min = nivel_tela_min
        self.nivel_tela_max = nivel_tela_max
        self.capacidade_niveis = capacidade_niveis

        # Calcula o total de níveis de tela: andares × níveis por andar
        self.niveis_por_andar = self.nivel_tela_max - self.nivel_tela_min + 1
        self.total_niveis_tela = self.capacidade_niveis * self.niveis_por_andar

        # 📦 Ocupações individualizadas por nível de tela: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
        self.niveis_ocupacoes: List[List[Tuple[int, int, int, int, float, datetime, datetime]]] = [[] for _ in range(self.total_niveis_tela)]

    # ============================================
    # 🔄 Conversão de Índices
    # ============================================
    def obter_andar_e_nivel_por_indice(self, nivel_index: int) -> Tuple[int, int]:
        """Retorna o andar e o nível dentro do andar baseado no índice."""
        if nivel_index < 0 or nivel_index >= self.total_niveis_tela:
            return -1, -1
        
        andar = nivel_index // self.niveis_por_andar
        nivel_no_andar = (nivel_index % self.niveis_por_andar) + self.nivel_tela_min
        return andar, nivel_no_andar

    def obter_indice_por_andar_e_nivel(self, andar: int, nivel_tela: int) -> int:
        """Retorna o índice baseado no andar e nível de tela."""
        if andar < 0 or andar >= self.capacidade_niveis:
            return -1
        if nivel_tela < self.nivel_tela_min or nivel_tela > self.nivel_tela_max:
            return -1
        
        return andar * self.niveis_por_andar + (nivel_tela - self.nivel_tela_min)

    # ==========================================================
    # 🔍 Consulta de Ocupação (para o Gestor)
    # ==========================================================
    def obter_ocupacao_nivel(self, nivel_index: int, inicio: datetime, fim: datetime) -> float:
        """Retorna a quantidade total ocupada em um nível no período especificado."""
        if nivel_index < 0 or nivel_index >= self.total_niveis_tela:
            return 0.0
        
        ocupada = 0.0
        for ocupacao in self.niveis_ocupacoes[nivel_index]:
            if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição temporal
                ocupada += ocupacao[4]  # quantidade_alocada
        return ocupada

    def obter_ocupacao_todos_niveis(self, inicio: datetime, fim: datetime) -> List[float]:
        """Retorna lista com a ocupação de todos os níveis no período especificado."""
        ocupacoes = []
        for i in range(self.total_niveis_tela):
            ocupacoes.append(self.obter_ocupacao_nivel(i, inicio, fim))
        return ocupacoes

    def nivel_disponivel(self, nivel_index: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se um nível está completamente livre no período."""
        return self.obter_ocupacao_nivel(nivel_index, inicio, fim) == 0.0

    def niveis_disponiveis_periodo(self, inicio: datetime, fim: datetime) -> List[int]:
        """Retorna lista de índices dos níveis completamente livres no período."""
        niveis_livres = []
        for i in range(self.total_niveis_tela):
            if self.nivel_disponivel(i, inicio, fim):
                niveis_livres.append(i)
        return niveis_livres

    def quantidade_niveis_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        """Retorna quantidade de níveis completamente livres no período."""
        return len(self.niveis_disponiveis_periodo(inicio, fim))

    def verificar_espaco_niveis(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se há níveis suficientes completamente livres no período."""
        return self.quantidade_niveis_disponiveis(inicio, fim) >= quantidade

    def encontrar_niveis_para_ocupacao(self, quantidade: int, inicio: datetime, fim: datetime) -> Optional[List[int]]:
        """Encontra níveis completamente livres para ocupação."""
        niveis_livres = self.niveis_disponiveis_periodo(inicio, fim)
        if len(niveis_livres) >= quantidade:
            return niveis_livres[:quantidade]
        return None

    def obter_ocupacoes_nivel(self, nivel_index: int) -> List[Tuple[int, int, int, int, float, datetime, datetime]]:
        """Retorna todas as ocupações de um nível específico."""
        if nivel_index < 0 or nivel_index >= self.total_niveis_tela:
            return []
        return self.niveis_ocupacoes[nivel_index].copy()

    def obter_status_niveis(self, momento: datetime) -> List[bool]:
        """Retorna status de ocupação de cada nível em um momento específico."""
        status = []
        for nivel_index in range(self.total_niveis_tela):
            ocupado = any(
                ocupacao[5] <= momento < ocupacao[6]  # inicio <= momento < fim
                for ocupacao in self.niveis_ocupacoes[nivel_index]
            )
            status.append(ocupado)
        return status

    def obter_proxima_liberacao(self, nivel_index: int, momento_atual: datetime) -> Optional[datetime]:
        """Retorna próximo horário de liberação de um nível específico."""
        if nivel_index < 0 or nivel_index >= self.total_niveis_tela:
            return None
        
        proximas_liberacoes = [
            ocupacao[6]  # fim
            for ocupacao in self.niveis_ocupacoes[nivel_index]
            if ocupacao[6] > momento_atual
        ]
        
        return min(proximas_liberacoes) if proximas_liberacoes else None

    # ==========================================================
    # 🔄 Ocupação e Atualização (para o Gestor)
    # ==========================================================
    def adicionar_ocupacao_nivel(
        self,
        nivel_index: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Adiciona uma ocupação específica a um nível específico."""
        if nivel_index < 0 or nivel_index >= self.total_niveis_tela:
            logger.warning(f"❌ Índice de nível inválido: {nivel_index}")
            return False

        self.niveis_ocupacoes[nivel_index].append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
        )

        andar, nivel_tela = self.obter_andar_e_nivel_por_indice(nivel_index)
        logger.info(
            f"📥 Ocupação adicionada no {self.nome} - Andar {andar}, Nível {nivel_tela} (índice {nivel_index}) | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
            f"{quantidade:.2f} unidades/gramas | {inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
        )
        return True

    def adicionar_ocupacao_por_andar_nivel(
        self,
        andar: int,
        nivel_tela: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Adiciona ocupação usando andar e nível de tela diretamente."""
        nivel_index = self.obter_indice_por_andar_e_nivel(andar, nivel_tela)
        if nivel_index == -1:
            logger.warning(f"❌ Andar {andar} ou nível {nivel_tela} inválido")
            return False
        
        return self.adicionar_ocupacao_nivel(
            nivel_index, id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim
        )

    def sobrescrever_ocupacao_nivel(
        self,
        nivel_index: int,
        ocupacoes: List[Tuple[int, int, int, int, float, datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações de um nível específico."""
        if nivel_index < 0 or nivel_index >= self.total_niveis_tela:
            logger.warning(f"❌ Índice de nível inválido: {nivel_index}")
            return False

        self.niveis_ocupacoes[nivel_index] = ocupacoes.copy()
        
        andar, nivel_tela = self.obter_andar_e_nivel_por_indice(nivel_index)
        logger.info(
            f"🔄 Ocupações do Andar {andar}, Nível {nivel_tela} (índice {nivel_index}) do {self.nome} foram sobrescritas. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    # ==========================================================
    # 🔐 Ocupação (Métodos de Compatibilidade)
    # ==========================================================
    def ocupar_niveis_especificos(
        self,
        niveis: List[int],
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_por_nivel: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Ocupa níveis específicos (mantido para compatibilidade)."""
        sucesso = True
        for nivel_index in niveis:
            if not self.adicionar_ocupacao_nivel(
                nivel_index, id_ordem, id_pedido, id_atividade, id_item, 
                quantidade_por_nivel, inicio, fim
            ):
                sucesso = False

        if sucesso:
            quantidade_total = quantidade_por_nivel * len(niveis)
            logger.info(
                f"📥 Ocupação múltipla registrada no {self.nome} | "
                f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
                f"{len(niveis)} níveis ({quantidade_total:.2f} total) | "
                f"{inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')} | "
                f"Níveis: {niveis}"
            )
        return sucesso

    def ocupar_niveis(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: int,
        quantidade_por_nivel: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Ocupa automaticamente a quantidade de níveis necessária (mantido para compatibilidade)."""
        niveis_para_ocupar = self.encontrar_niveis_para_ocupacao(quantidade, inicio, fim)
        
        if niveis_para_ocupar is None:
            logger.warning(
                f"❌ Níveis insuficientes no {self.nome} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}. "
                f"Necessários: {quantidade}, Disponíveis: {self.quantidade_niveis_disponiveis(inicio, fim)}"
            )
            return False

        return self.ocupar_niveis_especificos(
            niveis_para_ocupar, id_ordem, id_pedido, id_atividade, id_item, 
            quantidade_por_nivel, inicio, fim
        )

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade."""
        total_liberadas = 0
        
        for nivel_index in range(self.total_niveis_tela):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
            ]
            liberadas_nivel = antes - len(self.niveis_ocupacoes[nivel_index])
            total_liberadas += liberadas_nivel

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """Libera ocupações específicas por pedido."""
        total_liberadas = 0
        
        for nivel_index in range(self.total_niveis_tela):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
            ]
            liberadas_nivel = antes - len(self.niveis_ocupacoes[nivel_index])
            total_liberadas += liberadas_nivel

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_ordem(self, id_ordem: int):
        """Libera ocupações específicas por ordem."""
        total_liberadas = 0
        
        for nivel_index in range(self.total_niveis_tela):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if ocupacao[0] != id_ordem
            ]
            liberadas_nivel = antes - len(self.niveis_ocupacoes[nivel_index])
            total_liberadas += liberadas_nivel

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} "
                f"para Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Ordem {id_ordem}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        total_liberadas = 0
        
        for nivel_index in range(self.total_niveis_tela):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if ocupacao[6] > horario_atual  # fim > horario_atual
            ]
            liberadas_nivel = antes - len(self.niveis_ocupacoes[nivel_index])
            total_liberadas += liberadas_nivel

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} finalizadas até {horario_atual.strftime('%Y-%m-%d %H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar no {self.nome} até {horario_atual.strftime('%Y-%m-%d %H:%M')}."
            )
        return total_liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações de todos os níveis."""
        total = sum(len(ocupacoes) for ocupacoes in self.niveis_ocupacoes)
        for nivel_ocupacoes in self.niveis_ocupacoes:
            nivel_ocupacoes.clear()
        logger.info(f"🔓 Todas as {total} ocupações do {self.nome} foram removidas.")

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        total_liberadas = 0
        
        for nivel_index in range(self.total_niveis_tela):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if not (ocupacao[5] < fim and ocupacao[6] > inicio)  # remove qualquer sobreposição
            ]
            liberadas_nivel = antes - len(self.niveis_ocupacoes[nivel_index])
            total_liberadas += liberadas_nivel

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}."
            )

    def liberar_nivel_especifico(self, nivel_index: int, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupação específica de um nível."""
        if nivel_index < 0 or nivel_index >= self.total_niveis_tela:
            logger.warning(f"❌ Índice de nível inválido: {nivel_index}")
            return

        antes = len(self.niveis_ocupacoes[nivel_index])
        self.niveis_ocupacoes[nivel_index] = [
            ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]
        liberadas = antes - len(self.niveis_ocupacoes[nivel_index])
        
        if liberadas > 0:
            andar, nivel_tela = self.obter_andar_e_nivel_por_indice(nivel_index)
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações do Andar {andar}, Nível {nivel_tela} do {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada por andar e nível de tela."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info(f"📊 Total: {self.capacidade_niveis} andares × {self.niveis_por_andar} níveis = {self.total_niveis_tela} níveis de tela")
        logger.info("==============================================")

        tem_ocupacao = False
        for nivel_index in range(self.total_niveis_tela):
            if self.niveis_ocupacoes[nivel_index]:
                tem_ocupacao = True
                andar, nivel_tela = self.obter_andar_e_nivel_por_indice(nivel_index)
                logger.info(f"🔹 Andar {andar}, Nível {nivel_tela} (índice {nivel_index}):")
                for ocupacao in self.niveis_ocupacoes[nivel_index]:
                    logger.info(
                        f"   🗂️ Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                        f"{ocupacao[4]:.2f} unidades/gramas | {ocupacao[5].strftime('%Y-%m-%d %H:%M')} → {ocupacao[6].strftime('%Y-%m-%d %H:%M')}"
                    )

        if not tem_ocupacao:
            logger.info("🔹 Nenhuma ocupação registrada em nenhum nível.")

    def obter_estatisticas_uso(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso do armário no período."""
        total_ocupacoes = 0
        niveis_utilizados = 0
        
        for nivel_index in range(self.total_niveis_tela):
            ocupacoes_nivel = []
            for ocupacao in self.niveis_ocupacoes[nivel_index]:
                if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição temporal
                    ocupacoes_nivel.append(ocupacao)
            
            if ocupacoes_nivel:
                niveis_utilizados += 1
                total_ocupacoes += len(ocupacoes_nivel)
        
        taxa_utilizacao_niveis = (niveis_utilizados / self.total_niveis_tela * 100) if self.total_niveis_tela > 0 else 0.0
        
        return {
            'niveis_utilizados': niveis_utilizados,
            'niveis_total': self.total_niveis_tela,
            'capacidade_niveis': self.capacidade_niveis,
            'niveis_por_andar': self.niveis_por_andar,
            'taxa_utilizacao_niveis': taxa_utilizacao_niveis,
            'total_ocupacoes': total_ocupacoes
        }