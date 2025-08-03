from datetime import datetime, date
from typing import List, Tuple, Optional, Dict, Union
from enums.producao.unidade_medida import UnidadeMedida
from enums.producao.politica_producao import PoliticaProducao


class ItemAlmoxarifado:
    def __init__(
        self,
        id_item: int,
        nome: str,
        descricao: str,
        tipo_item: str,
        politica_producao: str,
        peso: float,
        unidade_medida: UnidadeMedida,
        estoque_min: float,
        estoque_max: float,
        estoque_atual: float,
        consumo_diario_estimado: float,
        reabastecimento_previsto_em: Optional[str] = None,
        reservas_futuras: Optional[List[dict]] = None,
        ficha_tecnica: Optional[int] = None
    ):
        self.id_item = id_item
        self.nome = nome
        self.descricao = descricao
        self.tipo_item = tipo_item
        
        # Converter string para enum para consistência
        self.politica_producao = (
            PoliticaProducao[politica_producao] 
            if isinstance(politica_producao, str) 
            else politica_producao
        )
        
        self.peso = peso
        self.unidade_medida = unidade_medida
        self.estoque_min = estoque_min
        self.estoque_max = estoque_max
        self.estoque_atual = estoque_atual
        self.consumo_diario_estimado = consumo_diario_estimado
        self.reabastecimento_previsto_em = (
            datetime.strptime(reabastecimento_previsto_em, "%Y-%m-%d")
            if reabastecimento_previsto_em else None
        )
        self.ficha_tecnica_id = ficha_tecnica
        self.reservas_futuras: List[Dict[str, Union[datetime, float, int]]] = self._parse_reservas_futuras(reservas_futuras)

    def _parse_reservas_futuras(self, reservas_raw: Optional[List[dict]]) -> List[dict]:
        """Converte reservas do formato JSON para formato interno otimizado"""
        if not reservas_raw:
            return []
        
        reservas_convertidas = []
        for r in reservas_raw:
            try:
                reservas_convertidas.append({
                    "data": datetime.strptime(r["data"], "%Y-%m-%d"),
                    "quantidade": float(r["quantidade_reservada"]),
                    "id_ordem": r.get("id_ordem", 0),
                    "id_pedido": r.get("id_pedido", 0),
                    "id_atividade": r.get("id_atividade")
                })
            except (KeyError, ValueError) as e:
                print(f"⚠️ Erro ao processar reserva {r}: {e}")
                continue
        
        return reservas_convertidas

    # =============================================================================
    #                           RESERVAS E CONSUMO
    # =============================================================================

    def reservar(self, data: datetime, quantidade: float, id_ordem: int, id_pedido: int, id_atividade: Optional[int] = None):
        """Reserva uma quantidade do item para uma data específica"""
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser positiva")
        
        if not self.tem_estoque_para(data, quantidade):
            raise ValueError(
                f"❌ Estoque insuficiente para reservar {quantidade} de {self.nome} "
                f"na data {data.strftime('%Y-%m-%d')}. "
                f"Estoque projetado: {self.estoque_projetado_em(data)}"
            )
        
        self.reservas_futuras.append({
            "data": data,
            "quantidade": quantidade,
            "id_ordem": id_ordem,
            "id_pedido": id_pedido,
            "id_atividade": id_atividade
        })

    def cancelar_reserva(self, data: datetime, quantidade: float, id_ordem: int, id_pedido: int, id_atividade: Optional[int] = None):
        """Cancela uma reserva específica"""
        reservas_antes = len(self.reservas_futuras)
        
        self.reservas_futuras = [
            r for r in self.reservas_futuras
            if not self._reserva_coincide(r, data, quantidade, id_ordem, id_pedido, id_atividade)
        ]
        
        reservas_canceladas = reservas_antes - len(self.reservas_futuras)
        if reservas_canceladas == 0:
            print(f"⚠️ Nenhuma reserva encontrada para cancelar: {self.nome} - {quantidade} em {data.strftime('%Y-%m-%d')}")

    def _reserva_coincide(self, reserva: dict, data: datetime, quantidade: float, 
                         id_ordem: int, id_pedido: int, id_atividade: Optional[int] = None) -> bool:
        """Verifica se uma reserva coincide com os parâmetros fornecidos"""
        return (
            reserva["data"].date() == data.date() and
            abs(reserva["quantidade"] - quantidade) < 0.001 and  # Comparação float segura
            reserva["id_ordem"] == id_ordem and
            reserva["id_pedido"] == id_pedido and
            (id_atividade is None or reserva.get("id_atividade") == id_atividade)
        )

    def consumir(self, data: datetime, quantidade: float, id_ordem: int, id_pedido: int, id_atividade: Optional[int] = None):
        """Consome uma quantidade do item, reduzindo o estoque atual"""
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser positiva")
            
        if not self.tem_estoque_para(data, quantidade):
            raise ValueError(
                f"❌ Estoque insuficiente para consumir {quantidade} de {self.nome} "
                f"na data {data.strftime('%Y-%m-%d')}. "
                f"Estoque projetado: {self.estoque_projetado_em(data)}"
            )
        
        self.estoque_atual -= quantidade
        self.cancelar_reserva(data, quantidade, id_ordem, id_pedido, id_atividade)

    # =============================================================================
    #                        VERIFICAÇÕES DE ESTOQUE
    # =============================================================================

    def tem_estoque_para(self, data: datetime, quantidade: float) -> bool:
        """Verifica se há estoque suficiente para uma quantidade em uma data"""
        if self.politica_producao == PoliticaProducao.SOB_DEMANDA:
            return True
        return self.estoque_projetado_em(data) >= quantidade

    def tem_estoque_atual_suficiente(self, quantidade: float) -> bool:
        """
        Verifica se há estoque atual suficiente (sem considerar reservas).
        
        CORREÇÃO DO BUG: SOB_DEMANDA não significa estoque infinito!
        Deve verificar o estoque real independente da política.
        """
        # ✅ CORREÇÃO: Verificar estoque real para TODOS os tipos
        return self.estoque_atual >= quantidade

        # ❌ CÓDIGO BUGADO ORIGINAL:
        # if self.politica_producao == PoliticaProducao.SOB_DEMANDA:
        #     return True  # BUG: Sempre retorna True mesmo com estoque 0!
        # return self.estoque_atual >= quantidade

    def estoque_projetado_em(self, data: Union[datetime, date]) -> float:
        """
        📉 Retorna o estoque projetado para uma data (datetime ou date).
        Subtrai as reservas feitas para o mesmo dia da data informada.
        """
        data_base = data.date() if isinstance(data, datetime) else data
        
        reservas_no_dia = sum(
            r["quantidade"]
            for r in self.reservas_futuras
            if r["data"].date() == data_base
        )
        
        return max(0, self.estoque_atual - reservas_no_dia)

    def quantidade_reservada_em(self, data: Union[datetime, date]) -> float:
        """Retorna a quantidade total reservada em uma data específica"""
        data_base = data.date() if isinstance(data, datetime) else data
        return sum(
            r["quantidade"]
            for r in self.reservas_futuras
            if r["data"].date() == data_base
        )

    def quantidade_disponivel_em(self, data: Union[datetime, date]) -> float:
        """Retorna a quantidade disponível (não reservada) em uma data"""
        return self.estoque_projetado_em(data)

    # =============================================================================
    #                           CONSULTAS E RELATÓRIOS
    # =============================================================================

    def esta_abaixo_do_minimo(self) -> bool:
        """Verifica se o estoque atual está abaixo do mínimo"""
        return self.estoque_atual < self.estoque_min

    def percentual_estoque_atual(self) -> float:
        """Retorna o percentual do estoque atual em relação ao máximo"""
        if self.estoque_max <= 0:
            return 0.0
        return (self.estoque_atual / self.estoque_max) * 100

    def dias_de_estoque_restante(self) -> Optional[float]:
        """Calcula quantos dias de estoque restam baseado no consumo diário"""
        if self.consumo_diario_estimado <= 0:
            return None
        return self.estoque_atual / self.consumo_diario_estimado

    def listar_reservas_por_periodo(self, data_inicio: date, data_fim: date) -> List[dict]:
        """Lista todas as reservas em um período específico"""
        return [
            r for r in self.reservas_futuras
            if data_inicio <= r["data"].date() <= data_fim
        ]

    def total_reservado_por_pedido(self, id_pedido: int) -> float:
        """Retorna o total reservado para um pedido específico"""
        return sum(
            r["quantidade"]
            for r in self.reservas_futuras
            if r["id_pedido"] == id_pedido
        )

    # =============================================================================
    #                              UTILITÁRIOS
    # =============================================================================

    def resumo_estoque(self, data_referencia: Optional[date] = None) -> dict:
        """Retorna um resumo completo do estoque do item"""
        if data_referencia is None:
            data_referencia = date.today()
        
        return {
            "id_item": self.id_item,
            "nome": self.nome,
            "descricao": self.descricao,
            "estoque_atual": self.estoque_atual,
            "estoque_min": self.estoque_min,
            "estoque_max": self.estoque_max,
            "estoque_projetado": self.estoque_projetado_em(data_referencia),
            "quantidade_reservada": self.quantidade_reservada_em(data_referencia),
            "percentual_estoque": self.percentual_estoque_atual(),
            "abaixo_do_minimo": self.esta_abaixo_do_minimo(),
            "dias_restantes": self.dias_de_estoque_restante(),
            "politica_producao": self.politica_producao.value,
            "unidade_medida": self.unidade_medida.value
        }

    def __repr__(self):
        return (
            f"<ItemAlmoxarifado {self.nome} | "
            f"Estoque: {self.estoque_atual} {self.unidade_medida.value} | "
            f"Política: {self.politica_producao.value}>"
        )
    
    def __str__(self):
        return f"{self.descricao} (ID: {self.id_item}) - {self.estoque_atual} {self.unidade_medida.value}"