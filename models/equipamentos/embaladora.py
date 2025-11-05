from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor  
from enums.equipamentos.tipo_embalagem import TipoEmbalagem
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('Embaladora')


class Embaladora(Equipamento):
    """
    ✉️ Classe que representa uma Embaladora SIMPLIFICADA.
    ✅ SEMPRE disponível para alocação
    ✅ Ignora capacidade_gramas_max para validação
    ✅ Aceita múltiplas alocações no mesmo horário
    ✅ Sem restrições de sobreposição
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        lista_tipo_embalagem: List[TipoEmbalagem],
        numero_operadores: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.EMBALADORAS,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max  # Mantido para compatibilidade mas não usado na validação
        self.lista_tipo_embalagem = lista_tipo_embalagem

        # Propriedade de compatibilidade
        self.capacidade_gramas = capacidade_gramas_max

        # ✉️ Ocupações: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, lista_tipo_embalagem, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, int, int, float, List[TipoEmbalagem], datetime, datetime]] = []

    # ==========================================================
    # ✅ Validações SIMPLIFICADAS - SEMPRE DISPONÍVEL
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        """
        🟢 SEMPRE RETORNA TRUE - Embaladora sempre disponível
        """
        return True

    def esta_disponivel_para_item(self, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """
        🟢 SEMPRE RETORNA TRUE - Aceita qualquer item a qualquer momento
        """
        return True

    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        """
        🟢 SIMPLIFICADO: Só valida capacidade mínima, ignora máxima
        """
        if quantidade_gramas < self.capacidade_gramas_min:
            logger.warning(
                f"⚠️ Quantidade {quantidade_gramas}g abaixo da capacidade mínima ({self.capacidade_gramas_min}g) da embaladora {self.nome}."
            )
            return False
        
        # NÃO valida capacidade máxima - aceita qualquer quantidade acima do mínimo
        return True

    def validar_capacidade_individual(self, quantidade_gramas: float) -> bool:
        """Método de compatibilidade que chama validar_capacidade."""
        return self.validar_capacidade(quantidade_gramas)

    def obter_quantidade_maxima_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        🟢 SIMPLIFICADO: Sempre retorna 0 para indicar que há capacidade disponível
        """
        return 0.0  # Sempre há capacidade disponível

    def validar_nova_ocupacao_item(self, id_item: int, quantidade_nova: float, 
                                  inicio: datetime, fim: datetime) -> bool:
        """
        🟢 SIMPLIFICADO: Só valida quantidade mínima, sempre aceita se >= mínimo
        """
        if quantidade_nova < self.capacidade_gramas_min:
            logger.debug(
                f"❌ {self.nome} | Item {id_item}: Quantidade {quantidade_nova}g abaixo do mínimo ({self.capacidade_gramas_min}g)"
            )
            return False
        
        # SEMPRE aceita se quantidade >= mínimo
        return True

    def validar_tipos_embalagem(self, tipos_embalagem: List[TipoEmbalagem]) -> bool:
        """Valida se os tipos de embalagem são suportados pela embaladora."""
        tipos_nao_suportados = [tipo for tipo in tipos_embalagem if tipo not in self.lista_tipo_embalagem]
        
        if tipos_nao_suportados:
            logger.warning(
                f"⚠️ Tipos de embalagem não suportados pela {self.nome}: "
                f"{[tipo.name for tipo in tipos_nao_suportados]}. "
                f"Suportados: {[tipo.name for tipo in self.lista_tipo_embalagem]}"
            )
            return False
        return True

    def verificar_disponibilidade(self, quantidade: float, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """
        🟢 SIMPLIFICADO: Só verifica quantidade mínima
        """
        return quantidade >= self.capacidade_gramas_min

    # ==========================================================
    # 🔍 Consulta de Ocupação (mantidos para compatibilidade)
    # ==========================================================
    def obter_quantidade_alocada_periodo(self, inicio: datetime, fim: datetime) -> float:
        """Retorna a quantidade total alocada no período especificado."""
        quantidade_total = 0.0
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[6] or inicio >= ocupacao[7]):  # há sobreposição temporal
                quantidade_total += ocupacao[4]  # quantidade_alocada
        return quantidade_total

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, float, List[TipoEmbalagem], datetime, datetime]]:
        """Retorna todas as ocupações que se sobrepõem ao período especificado."""
        ocupacoes_periodo = []
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[6] or inicio >= ocupacao[7]):  # há sobreposição temporal
                ocupacoes_periodo.append(ocupacao)
        return ocupacoes_periodo

    def obter_capacidade_disponivel_periodo(self, inicio: datetime, fim: datetime) -> float:
        """
        🟢 SIMPLIFICADO: Sempre retorna capacidade máxima (infinita disponibilidade)
        """
        return float('inf')  # Capacidade infinita

    def obter_capacidade_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        🟢 SIMPLIFICADO: Sempre retorna capacidade máxima (infinita disponibilidade)
        """
        return float('inf')  # Capacidade infinita

    def obter_proxima_liberacao(self, momento_atual: datetime) -> Optional[datetime]:
        """Retorna próximo horário de liberação de capacidade."""
        proximas_liberacoes = [
            ocupacao[7]  # fim
            for ocupacao in self.ocupacoes
            if ocupacao[7] > momento_atual
        ]
        return min(proximas_liberacoes) if proximas_liberacoes else None

    def obter_todas_ocupacoes(self) -> List[Tuple[int, int, int, int, float, List[TipoEmbalagem], datetime, datetime]]:
        """Retorna todas as ocupações da embaladora."""
        return self.ocupacoes.copy()

    # ==========================================================
    # 🔄 Ocupação - SIMPLIFICADA
    # ==========================================================
    def ocupar(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        lista_tipo_embalagem: List[TipoEmbalagem],
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        🟢 SIMPLIFICADO: Aceita qualquer ocupação desde que:
        - Quantidade >= capacidade mínima
        - Tipos de embalagem sejam suportados
        NÃO valida capacidade máxima ou sobreposições
        """
        # Validação dos tipos de embalagem
        if not self.validar_tipos_embalagem(lista_tipo_embalagem):
            return False

        # Só valida quantidade mínima
        if quantidade < self.capacidade_gramas_min:
            logger.error(
                f"❌ {self.nome} | Item {id_item}: Quantidade {quantidade}g "
                f"abaixo do mínimo ({self.capacidade_gramas_min}g)"
            )
            return False

        # SEMPRE aceita se passou nas validações acima
        # Cria nova ocupação
        self.ocupacoes.append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade, lista_tipo_embalagem, inicio, fim)
        )

        # Log informativo
        logger.info(
            f"✅ {self.nome} | Item {id_item}: Ocupação aceita {quantidade}g "
            f"de {inicio.strftime('%Y-%m-%d %H:%M')} até {fim.strftime('%Y-%m-%d %H:%M')} "
            f"(Ordem {id_ordem}, Pedido {id_pedido}, Atividade {id_atividade}) | "
            f"Embalagens: {[emb.name for emb in lista_tipo_embalagem]} | "
            f"Total de ocupações: {len(self.ocupacoes)}"
        )
        
        return True

    def adicionar_ocupacao(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_alocada: float,
        lista_tipo_embalagem: List[TipoEmbalagem],
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Método de compatibilidade."""
        return self.ocupar(
            id_ordem, id_pedido, id_atividade, id_item,
            quantidade_alocada, lista_tipo_embalagem, inicio, fim
        )

    def sobrescrever_ocupacoes(
        self,
        ocupacoes: List[Tuple[int, int, int, int, float, List[TipoEmbalagem], datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações da embaladora."""
        self.ocupacoes = ocupacoes.copy()
        
        logger.info(
            f"🔄 Ocupações da {self.nome} foram sobrescritas. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    def atualizar_ocupacao_especifica(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nova_quantidade: float,
        nova_lista_embalagem: List[TipoEmbalagem],
        novo_inicio: datetime,
        novo_fim: datetime
    ) -> bool:
        """
        🟢 SIMPLIFICADO: Atualiza uma ocupação específica
        """
        for i, ocupacao in enumerate(self.ocupacoes):
            if ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade:
                id_item = ocupacao[3]  # Mantém o id_item original
                
                # Validação dos tipos de embalagem
                if not self.validar_tipos_embalagem(nova_lista_embalagem):
                    return False

                # Só valida quantidade mínima
                if nova_quantidade < self.capacidade_gramas_min:
                    logger.error(
                        f"❌ {self.nome} | Nova quantidade {nova_quantidade}g "
                        f"abaixo do mínimo ({self.capacidade_gramas_min}g)"
                    )
                    return False

                # Atualiza a ocupação
                self.ocupacoes[i] = (
                    id_ordem, id_pedido, id_atividade, id_item, nova_quantidade, 
                    nova_lista_embalagem, novo_inicio, novo_fim
                )
                
                logger.info(
                    f"🔄 Ocupação atualizada na {self.nome} | "
                    f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
                    f"Nova quantidade: {nova_quantidade:.2f}g | {novo_inicio.strftime('%Y-%m-%d %H:%M')} → {novo_fim.strftime('%Y-%m-%d %H:%M')} | "
                    f"Embalagens: {[emb.name for emb in nova_lista_embalagem]}"
                )
                return True

        logger.warning(
            f"❌ Ocupação não encontrada para atualizar na {self.nome} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade}"
        )
        return False

    # ============================================
    # 🔓 Liberação (mantidos iguais)
    # ============================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """Libera ocupações específicas por pedido."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_ordem(self, id_ordem: int):
        """Libera ocupações específicas por ordem."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[0] != id_ordem
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"para Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Ordem {id_ordem}."
            )

    def liberar_por_item(self, id_item: int):
        """Libera ocupações vinculadas a um item específico."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[3] != id_item
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} | Liberadas {liberadas} ocupações do item {id_item}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação da {self.nome} estava associada ao item {id_item}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[7] > horario_atual  # fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🟩 {self.nome} | Liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%Y-%m-%d %H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar na {self.nome} até {horario_atual.strftime('%Y-%m-%d %H:%M')}."
            )
        return liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações da embaladora."""
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 Todas as {total} ocupações da {self.nome} foram removidas.")

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[6] < fim and ocupacao[7] > inicio)  # remove qualquer sobreposição
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}."
            )

    # ============================================
    # 📅 Agenda e Relatórios
    # ============================================
    def mostrar_agenda(self):
        """
        Mostra agenda detalhada da embaladora.
        """
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome} (SEMPRE DISPONÍVEL)")
        logger.info(f"📊 Capacidade mínima: {self.capacidade_gramas_min}g")
        logger.info(f"📊 Capacidade máxima: ILIMITADA (aceita múltiplas alocações)")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        # Agrupa ocupações por horário para melhor visualização
        ocupacoes_por_horario = {}
        for ocupacao in self.ocupacoes:
            chave_horario = f"{ocupacao[6].strftime('%Y-%m-%d %H:%M')} → {ocupacao[7].strftime('%Y-%m-%d %H:%M')}"
            if chave_horario not in ocupacoes_por_horario:
                ocupacoes_por_horario[chave_horario] = []
            ocupacoes_por_horario[chave_horario].append(ocupacao)

        for horario, ocupacoes in sorted(ocupacoes_por_horario.items()):
            logger.info(f"\n⏰ {horario}:")
            for ocupacao in ocupacoes:
                logger.info(
                    f"   ✉️ Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | "
                    f"Item {ocupacao[3]} | {ocupacao[4]:.2f}g | "
                    f"Embalagens: {[emb.name for emb in ocupacao[5]]}"
                )
            total_periodo = sum(oc[4] for oc in ocupacoes)
            logger.info(f"   📊 Total no período: {total_periodo:.2f}g")

    def obter_estatisticas_embalagem(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso por tipo de embalagem no período."""
        ocupacoes_periodo = self.obter_ocupacoes_periodo(inicio, fim)
        
        if not ocupacoes_periodo:
            return {}
        
        estatisticas_embalagem = {}
        
        for ocupacao in ocupacoes_periodo:
            qtd = ocupacao[4]  # quantidade_alocada
            emb_list = ocupacao[5]  # lista_tipo_embalagem
            
            for tipo_embalagem in emb_list:
                nome_embalagem = tipo_embalagem.name
                if nome_embalagem not in estatisticas_embalagem:
                    estatisticas_embalagem[nome_embalagem] = {
                        'quantidade_total': 0.0,
                        'ocorrencias': 0
                    }
                
                estatisticas_embalagem[nome_embalagem]['quantidade_total'] += qtd
                estatisticas_embalagem[nome_embalagem]['ocorrencias'] += 1
        
        return estatisticas_embalagem

    def obter_tipos_embalagem_periodo(self, inicio: datetime, fim: datetime) -> List[TipoEmbalagem]:
        """Retorna lista única de tipos de embalagem utilizados no período."""
        ocupacoes_periodo = self.obter_ocupacoes_periodo(inicio, fim)
        tipos_utilizados = set()
        
        for ocupacao in ocupacoes_periodo:
            emb_list = ocupacao[5]  # lista_tipo_embalagem
            for tipo_embalagem in emb_list:
                tipos_utilizados.add(tipo_embalagem)
        
        return list(tipos_utilizados)

    # ==========================================================
    # 📊 Métodos de Análise por Item
    # ==========================================================
    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico na embaladora.
        """
        ocupacoes_item = [
            oc for oc in self.ocupacoes if oc[3] == id_item
        ]
        
        if ocupacoes_item:
            quantidade_total = sum(oc[4] for oc in ocupacoes_item)
            periodo_inicio = min(oc[6] for oc in ocupacoes_item)
            periodo_fim = max(oc[7] for oc in ocupacoes_item)
            
            return {
                'quantidade_total': quantidade_total,
                'num_ocupacoes': len(ocupacoes_item),
                'periodo_inicio': periodo_inicio.strftime('%Y-%m-%d %H:%M'),
                'periodo_fim': periodo_fim.strftime('%Y-%m-%d %H:%M'),
                'ocupacoes': [
                    {
                        'id_ordem': oc[0],
                        'id_pedido': oc[1],
                        'quantidade': oc[4],
                        'inicio': oc[6].strftime('%Y-%m-%d %H:%M'),
                        'fim': oc[7].strftime('%Y-%m-%d %H:%M'),
                        'tipos_embalagem': [emb.name for emb in oc[5]]
                    }
                    for oc in ocupacoes_item
                ]
            }
        
        return {}

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 SIMPLIFICADO: Retorna soma total do item (não há limite de capacidade)
        """
        ocupacoes_item = [oc for oc in self.ocupacoes if oc[3] == id_item]
        
        if not ocupacoes_item:
            return {}
            
        quantidade_total = sum(oc[4] for oc in ocupacoes_item)
        
        return {
            'quantidade_total': quantidade_total,
            'num_ocupacoes': len(ocupacoes_item),
            'capacidade_ilimitada': True
        }