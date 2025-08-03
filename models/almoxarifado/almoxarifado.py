from datetime import datetime, date
from typing import List, Optional, Dict
from models.almoxarifado.item_almoxarifado import ItemAlmoxarifado


class Almoxarifado:
    def __init__(self):
        self.itens: List[ItemAlmoxarifado] = []
        self._cache_itens: Dict[int, ItemAlmoxarifado] = {}  # Cache para busca rápida por ID

    # =============================================================================
    #                        GERENCIAMENTO DE ITENS
    # =============================================================================

    def adicionar_item(self, item: ItemAlmoxarifado):
        """Adiciona um item ao almoxarifado"""
        if self.buscar_item_por_id(item.id_item):
            raise ValueError(f"Item com ID {item.id_item} já existe no almoxarifado")
        
        self.itens.append(item)
        self._cache_itens[item.id_item] = item

    def remover_item(self, id_item: int) -> bool:
        """Remove um item do almoxarifado"""
        item = self.buscar_item_por_id(id_item)
        if item:
            self.itens.remove(item)
            del self._cache_itens[id_item]
            return True
        return False

    # =============================================================================
    #                            BUSCAS OTIMIZADAS
    # =============================================================================

    def buscar_item_por_id(self, id_item: int) -> Optional[ItemAlmoxarifado]:
        """Busca item por ID usando cache para performance otimizada"""
        return self._cache_itens.get(id_item)

    def buscar_por_id(self, id_item: int) -> Optional[ItemAlmoxarifado]:
        """Método de compatibilidade - delega para buscar_item_por_id"""
        return self.buscar_item_por_id(id_item)

    def buscar_por_nome(self, nome: str) -> Optional[ItemAlmoxarifado]:
        """Busca item por nome (busca exata)"""
        return next((item for item in self.itens if item.nome == nome), None)

    def buscar_itens_por_nome_parcial(self, termo: str) -> List[ItemAlmoxarifado]:
        """Busca itens que contenham o termo no nome ou descrição"""
        termo_lower = termo.lower()
        return [
            item for item in self.itens
            if termo_lower in item.nome.lower() or termo_lower in item.descricao.lower()
        ]

    def buscar_itens_por_tipo(self, tipo_item: str) -> List[ItemAlmoxarifado]:
        """Busca itens por tipo (INSUMO, PRODUTO, SUBPRODUTO)"""
        return [item for item in self.itens if item.tipo_item == tipo_item]

    def buscar_itens_por_politica(self, politica: str) -> List[ItemAlmoxarifado]:
        """Busca itens por política de produção"""
        return [item for item in self.itens if item.politica_producao.value == politica]

    # =============================================================================
    #                      VERIFICAÇÕES DE DISPONIBILIDADE
    # =============================================================================

    def verificar_disponibilidade_projetada_para_data(
        self, 
        id_item: int, 
        data: date, 
        quantidade: float = 0.0
    ) -> float:
        """
        Retorna a quantidade projetada para o item em uma data futura.
        Se `quantidade` for informada, retorna True/False para disponibilidade.
        Caso contrário, retorna o valor do estoque projetado.
        """
        item = self.buscar_item_por_id(id_item)
        if not item:
            return 0.0 if quantidade == 0.0 else False

        estoque_projetado = item.estoque_projetado_em(data)
        
        if quantidade > 0:
            return estoque_projetado >= quantidade
        
        return estoque_projetado

    def verificar_disponibilidade_multiplos_itens(
        self, 
        requisicoes: List[tuple], 
        data: date
    ) -> Dict[int, bool]:
        """
        Verifica disponibilidade para múltiplos itens de uma vez.
        requisicoes: Lista de tuplas (id_item, quantidade)
        Retorna: Dict {id_item: disponivel}
        """
        resultado = {}
        
        for id_item, quantidade in requisicoes:
            disponivel = self.verificar_disponibilidade_projetada_para_data(
                id_item, data, quantidade
            )
            resultado[id_item] = bool(disponivel)
        
        return resultado

    def obter_estoque_atual_item(self, id_item: int) -> float:
        """Retorna o estoque atual de um item específico"""
        item = self.buscar_item_por_id(id_item)
        return item.estoque_atual if item else 0.0

    # =============================================================================
    #                         OPERAÇÕES EM LOTE
    # =============================================================================

    def reservar_multiplos_itens(
        self, 
        reservas: List[tuple], 
        data: datetime, 
        id_ordem: int, 
        id_pedido: int
    ):
        """
        Reserva múltiplos itens de uma vez.
        reservas: Lista de tuplas (id_item, quantidade)
        """
        itens_reservados = []
        try:
            for id_item, quantidade in reservas:
                item = self.buscar_item_por_id(id_item)
                if not item:
                    raise ValueError(f"Item {id_item} não encontrado")
                
                item.reservar(data, quantidade, id_ordem, id_pedido)
                itens_reservados.append((id_item, quantidade))
                
        except Exception as e:
            # Rollback das reservas já feitas
            for id_item, quantidade in itens_reservados:
                item = self.buscar_item_por_id(id_item)
                if item:
                    item.cancelar_reserva(data, quantidade, id_ordem, id_pedido)
            raise e

    def cancelar_reservas_pedido(self, id_pedido: int, data: Optional[datetime] = None):
        """Cancela todas as reservas de um pedido específico"""
        for item in self.itens:
            reservas_para_remover = []
            
            for reserva in item.reservas_futuras:
                if reserva["id_pedido"] == id_pedido:
                    if data is None or reserva["data"].date() == data.date():
                        reservas_para_remover.append(reserva)
            
            for reserva in reservas_para_remover:
                item.cancelar_reserva(
                    reserva["data"], 
                    reserva["quantidade"], 
                    reserva["id_ordem"], 
                    reserva["id_pedido"]
                )

    # =============================================================================
    #                        RELATÓRIOS E CONSULTAS
    # =============================================================================

    def listar_itens(self) -> List[ItemAlmoxarifado]:
        """Retorna lista de todos os itens"""
        return self.itens.copy()

    def itens_abaixo_do_minimo(self) -> List[ItemAlmoxarifado]:
        """Retorna itens com estoque abaixo do mínimo"""
        return [item for item in self.itens if item.esta_abaixo_do_minimo()]

    def itens_com_estoque_zero(self) -> List[ItemAlmoxarifado]:
        """Retorna itens com estoque atual zero"""
        return [item for item in self.itens if item.estoque_atual <= 0]

    def relatorio_estoque_por_data(self, data: date) -> List[Dict]:
        """Gera relatório de estoque projetado para uma data específica"""
        relatorio = []
        
        for item in self.itens:
            relatorio.append({
                "id_item": item.id_item,
                "nome": item.nome,
                "descricao": item.descricao,
                "estoque_atual": item.estoque_atual,
                "reservado_na_data": item.quantidade_reservada_em(data),
                "estoque_projetado": item.estoque_projetado_em(data),
                "unidade": item.unidade_medida.value,
                "politica": item.politica_producao.value
            })
        
        return relatorio

    def estatisticas_almoxarifado(self) -> Dict:
        """Retorna estatísticas gerais do almoxarifado"""
        total_itens = len(self.itens)
        itens_abaixo_minimo = len(self.itens_abaixo_do_minimo())
        itens_sem_estoque = len(self.itens_com_estoque_zero())
        
        # Agrupar por tipo
        tipos = {}
        for item in self.itens:
            tipos[item.tipo_item] = tipos.get(item.tipo_item, 0) + 1
        
        # Agrupar por política
        politicas = {}
        for item in self.itens:
            politica = item.politica_producao.value
            politicas[politica] = politicas.get(politica, 0) + 1
        
        return {
            "total_itens": total_itens,
            "itens_abaixo_minimo": itens_abaixo_minimo,
            "itens_sem_estoque": itens_sem_estoque,
            "distribuicao_por_tipo": tipos,
            "distribuicao_por_politica": politicas,
            "percentual_critico": (itens_abaixo_minimo / total_itens * 100) if total_itens > 0 else 0
        }

    # =============================================================================
    #                           UTILITÁRIOS
    # =============================================================================

    def validar_integridade(self) -> List[str]:
        """Valida a integridade dos dados do almoxarifado"""
        problemas = []
        
        # Verificar IDs duplicados
        ids_vistos = set()
        for item in self.itens:
            if item.id_item in ids_vistos:
                problemas.append(f"ID duplicado encontrado: {item.id_item}")
            ids_vistos.add(item.id_item)
        
        # Verificar consistência do cache
        if len(self._cache_itens) != len(self.itens):
            problemas.append("Cache de itens inconsistente com lista principal")
        
        # Verificar estoque negativo
        for item in self.itens:
            if item.estoque_atual < 0:
                problemas.append(f"Estoque negativo para item {item.id_item}: {item.estoque_atual}")
        
        return problemas

    def reconstruir_cache(self):
        """Reconstrói o cache de itens"""
        self._cache_itens.clear()
        for item in self.itens:
            self._cache_itens[item.id_item] = item

    def limpar_reservas_expiradas(self, data_limite: date):
        """Remove reservas anteriores à data limite"""
        for item in self.itens:
            item.reservas_futuras = [
                r for r in item.reservas_futuras
                if r["data"].date() >= data_limite
            ]

    def __len__(self):
        return len(self.itens)

    def __repr__(self):
        return f"<Almoxarifado com {len(self.itens)} itens>"