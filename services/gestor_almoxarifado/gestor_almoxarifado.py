from datetime import datetime, date, timedelta
from typing import List, Tuple, Optional, Dict
from models.almoxarifado.almoxarifado import Almoxarifado
from models.almoxarifado.item_almoxarifado import ItemAlmoxarifado
from enums.producao.politica_producao import PoliticaProducao
from utils.logs.logger_factory import setup_logger

logger = setup_logger('GestorAlmoxarifado')


class GestorAlmoxarifado:
    def __init__(self, almoxarifado: Almoxarifado):
        self.almoxarifado = almoxarifado

    # =============================================================================
    #                     VERIFICAÇÕES DE DISPONIBILIDADE
    # =============================================================================

    def verificar_disponibilidade(self, reservas: List[Tuple[int, float, datetime]]) -> bool:
        """Verifica se todos os itens da lista têm estoque disponível"""
        for id_item, quantidade, data in reservas:
            item = self.almoxarifado.buscar_item_por_id(id_item)
            if item is None or not item.tem_estoque_para(data, quantidade):
                logger.warning(f"❌ Item {id_item} indisponível: quantidade {quantidade} em {data.strftime('%Y-%m-%d')}")
                return False
        return True
    
    def verificar_disponibilidade_projetada_para_data(
        self,
        id_item: int,
        data: date,
        quantidade: float = 0.0
    ) -> float:
        """
        Verifica a disponibilidade projetada de um item para uma data futura.
        - Se `quantidade` for informada, retorna True/False.
        - Se não for informada, retorna a quantidade projetada.
        """
        return self.almoxarifado.verificar_disponibilidade_projetada_para_data(
            id_item=id_item,
            data=data,
            quantidade=quantidade
        )

    def verificar_estoque_atual_suficiente(self, id_item: int, quantidade: float) -> bool:
        """Verifica se há estoque atual suficiente (sem considerar reservas futuras)"""
        item = self.almoxarifado.buscar_item_por_id(id_item)
        if not item:
            return False
        return item.tem_estoque_atual_suficiente(quantidade)

    def verificar_disponibilidade_multiplos_itens(
        self, 
        itens_requisitados: List[Tuple[int, float]], 
        data: date
    ) -> Dict[int, bool]:
        """
        Verifica disponibilidade para múltiplos itens de uma vez.
        Otimizado para verificações em lote.
        """
        return self.almoxarifado.verificar_disponibilidade_multiplos_itens(
            itens_requisitados, data
        )

    # =============================================================================
    #                        OPERAÇÕES DE RESERVA
    # =============================================================================

    def reservar_itens(self, reservas: List[Tuple[int, float, datetime]], id_ordem: int = 0, id_pedido: int = 0):
        """Reserva múltiplos itens verificando disponibilidade primeiro"""
        # Verificar disponibilidade primeiro
        if not self.verificar_disponibilidade(reservas):
            raise ValueError("❌ Um ou mais itens não têm estoque suficiente para reserva")
        
        # Executar reservas
        itens_reservados = []
        try:
            for id_item, quantidade, data in reservas:
                item = self.almoxarifado.buscar_item_por_id(id_item)
                if item:
                    item.reservar(data, quantidade, id_ordem, id_pedido)
                    itens_reservados.append((id_item, quantidade, data))
                    logger.info(f"✅ Reservado: {quantidade} de {item.nome} para {data.strftime('%Y-%m-%d')}")
        
        except Exception as e:
            # Rollback das reservas já feitas
            self._rollback_reservas(itens_reservados, id_ordem, id_pedido)
            raise e

    def _rollback_reservas(self, reservas: List[Tuple], id_ordem: int, id_pedido: int):
        """Executa rollback de reservas em caso de erro"""
        for id_item, quantidade, data in reservas:
            item = self.almoxarifado.buscar_item_por_id(id_item)
            if item:
                item.cancelar_reserva(data, quantidade, id_ordem, id_pedido)
                logger.info(f"🔄 Rollback: cancelada reserva de {quantidade} de {item.nome}")

    def cancelar_reservas(self, reservas: List[Tuple[int, float, datetime]], id_ordem: int = 0, id_pedido: int = 0):
        """Cancela múltiplas reservas"""
        for id_item, quantidade, data in reservas:
            item = self.almoxarifado.buscar_item_por_id(id_item)
            if item:
                item.cancelar_reserva(data, quantidade, id_ordem, id_pedido)
                logger.info(f"❌ Cancelada reserva: {quantidade} de {item.nome} para {data.strftime('%Y-%m-%d')}")

    def cancelar_todas_reservas_pedido(self, id_pedido: int, data: Optional[datetime] = None):
        """Cancela todas as reservas de um pedido específico"""
        self.almoxarifado.cancelar_reservas_pedido(id_pedido, data)
        logger.info(f"🔄 Canceladas todas as reservas do pedido {id_pedido}")

    # =============================================================================
    #                        OPERAÇÕES DE CONSUMO
    # =============================================================================

    def consumir_itens(self, consumos: List[Tuple[int, float, datetime]], id_ordem: int = 0, id_pedido: int = 0):
        """Consome múltiplos itens (reduz estoque atual)"""
        for id_item, quantidade, data in consumos:
            item = self.almoxarifado.buscar_item_por_id(id_item)
            if item:
                item.consumir(data, quantidade, id_ordem, id_pedido)
                logger.info(f"📉 Consumido: {quantidade} de {item.nome} em {data.strftime('%Y-%m-%d')}")

    def separar_itens_para_producao(
        self,
        id_ordem: int,
        id_pedido: int,
        funcionario_id: int,
        itens: List[Tuple[int, float, datetime]]
    ):
        """
        Efetiva o consumo dos itens de uma ordem/pedido,
        registrando o funcionário responsável.
        """
        itens_separados = []
        
        try:
            for id_item, quantidade, data in itens:
                item = self.almoxarifado.buscar_item_por_id(id_item)
                if not item:
                    raise ValueError(f"Item {id_item} não encontrado")
                
                # Verificar disponibilidade antes de consumir
                if not item.tem_estoque_para(data, quantidade):
                    raise ValueError(
                        f"Estoque insuficiente para {item.nome}: "
                        f"necessário {quantidade}, disponível {item.estoque_projetado_em(data)}"
                    )
                
                item.consumir(data, quantidade, id_ordem, id_pedido)
                itens_separados.append((id_item, item.nome, quantidade))
        
        except Exception as e:
            logger.error(f"❌ Erro na separação: {e}")
            raise e

        # Registrar separação bem-sucedida
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        logger.info(
            f"📦 Estoque separado para Ordem {id_ordem}, Pedido {id_pedido} "
            f"por Funcionário {funcionario_id} em {timestamp}"
        )
        
        for id_item, nome, quantidade in itens_separados:
            logger.info(f"   - {nome}: {quantidade}")

    # =============================================================================
    #                         CONSULTAS E RELATÓRIOS
    # =============================================================================

    def obter_estoque_atual(self, id_item: int) -> float:
        """Retorna o estoque atual de um item"""
        return self.almoxarifado.obter_estoque_atual_item(id_item)

    def obter_estoque_projetado(self, id_item: int, data: date) -> float:
        """Retorna o estoque projetado de um item para uma data"""
        item = self.almoxarifado.buscar_item_por_id(id_item)
        return item.estoque_projetado_em(data) if item else 0.0

    def obter_item_por_id(self, id_item: int) -> Optional[ItemAlmoxarifado]:
        """Retorna um item específico por ID"""
        return self.almoxarifado.buscar_item_por_id(id_item)

    def listar_itens_por_tipo(self, tipo_item: str) -> List[ItemAlmoxarifado]:
        """Lista itens filtrados por tipo"""
        return self.almoxarifado.buscar_itens_por_tipo(tipo_item)

    def verificar_estoque_minimo(self) -> List[Dict]:
        """
        Retorna lista de itens com política ESTOCADO abaixo do estoque mínimo.
        Versão otimizada com mais informações.
        """
        itens_em_alerta = []
        total_itens = len(self.almoxarifado.itens)
        
        logger.info(f"📦 Total de itens carregados no almoxarifado: {total_itens}")
        logger.info("🔍 Verificando estoque mínimo apenas para itens com política ESTOCADO:")

        for item in self.almoxarifado.itens:
            logger.debug(f"🧪 {item.descricao} - política: {item.politica_producao}")

            # Verificar apenas itens ESTOCADOS
            if item.politica_producao != PoliticaProducao.ESTOCADO:
                continue

            atual = item.estoque_atual
            minimo = item.estoque_min
            unidade = item.unidade_medida.value

            logger.debug(f"🔸 {item.descricao} (ID {item.id_item}): {atual:.2f} / mínimo {minimo:.2f} {unidade}")

            if item.esta_abaixo_do_minimo():
                logger.warning(f"   ❗ {item.descricao} está abaixo do mínimo!")
                
                itens_em_alerta.append({
                    "id_item": item.id_item,
                    "nome": item.nome,
                    "descricao": item.descricao,
                    "estoque_atual": round(atual, 2),
                    "estoque_min": round(minimo, 2),
                    "estoque_max": round(item.estoque_max, 2),
                    "falta": round(minimo - atual, 2),
                    "percentual_atual": round(item.percentual_estoque_atual(), 2),
                    "dias_restantes": item.dias_de_estoque_restante(),
                    "unidade": unidade
                })
            else:
                logger.debug("   ✅ Estoque suficiente.")

        return itens_em_alerta

    def gerar_relatorio_estoque_completo(self, data_referencia: Optional[date] = None) -> Dict:
        """Gera relatório completo do estado do almoxarifado"""
        if data_referencia is None:
            data_referencia = date.today()
        
        estatisticas = self.almoxarifado.estatisticas_almoxarifado()
        itens_criticos = self.verificar_estoque_minimo()
        relatorio_por_data = self.almoxarifado.relatorio_estoque_por_data(data_referencia)
        
        return {
            "data_relatorio": data_referencia.isoformat(),
            "estatisticas_gerais": estatisticas,
            "itens_criticos": itens_criticos,
            "estoque_por_item": relatorio_por_data,
            "total_itens_criticos": len(itens_criticos),
            "percentual_itens_criticos": (len(itens_criticos) / estatisticas["total_itens"] * 100) if estatisticas["total_itens"] > 0 else 0
        }

    # =============================================================================
    #                           EXIBIÇÃO E LOGS
    # =============================================================================

    def exibir_itens_estoque(self, data: Optional[datetime] = None):
        """Exibe itens do estoque com formatação melhorada"""
        print("📦 Itens no Almoxarifado:")
        
        if not self.almoxarifado.itens:
            print("   ⚠️ Nenhum item encontrado no almoxarifado")
            return
        
        for item in self.almoxarifado.itens:
            if data:
                estoque = item.estoque_projetado_em(data)
                reservado = item.quantidade_reservada_em(data)
                print(
                    f"🔹 ID: {item.id_item} | {item.descricao}\n"
                    f"   📅 Estoque projetado ({data.strftime('%Y-%m-%d')}): {estoque:.2f} {item.unidade_medida.value}\n"
                    f"   📋 Reservado: {reservado:.2f} | Política: {item.politica_producao.value}\n"
                )
            else:
                status = "❗ Crítico" if item.esta_abaixo_do_minimo() else "✅ Normal"
                print(
                    f"🔹 ID: {item.id_item} | {item.descricao}\n"
                    f"   📊 Estoque atual: {item.estoque_atual:.2f} {item.unidade_medida.value}\n"
                    f"   📏 Min/Max: {item.estoque_min:.2f} / {item.estoque_max:.2f}\n"
                    f"   🏷️ Política: {item.politica_producao.value} | Status: {status}\n"
                )

    def resumir_estoque_projetado(self, data: date):
        """
        📊 Gera um resumo de estoque projetado para uma data com melhor formatação
        """
        print(f"\n📅 Estoque projetado para {data.strftime('%d/%m/%Y')}:\n")
        print("=" * 80)

        itens_criticos = []
        
        for item in self.almoxarifado.itens:
            reservado = item.quantidade_reservada_em(data)
            projetado = item.estoque_projetado_em(data)
            percentual = item.percentual_estoque_atual()

            # Determinar status
            if item.politica_producao == PoliticaProducao.SOB_DEMANDA:
                status = "🔄 SOB DEMANDA"
            elif projetado <= 0:
                status = "🚨 ESGOTADO"
                itens_criticos.append(item.descricao)
            elif item.esta_abaixo_do_minimo():
                status = "⚠️ ABAIXO DO MÍNIMO"
                itens_criticos.append(item.descricao)
            else:
                status = "✅ NORMAL"

            print(
                f"🔹 {item.descricao} (ID: {item.id_item})\n"
                f"   📊 Atual: {item.estoque_atual:.2f} | Reservado: {reservado:.2f} | Projetado: {projetado:.2f}\n"
                f"   📈 Percentual do máximo: {percentual:.1f}% | {status}\n"
            )
        
        # Resumo final
        print("=" * 80)
        print(f"📋 Resumo: {len(self.almoxarifado.itens)} itens analisados")
        if itens_criticos:
            print(f"⚠️ {len(itens_criticos)} itens necessitam atenção:")
            for item in itens_criticos:
                print(f"   - {item}")
        else:
            print("✅ Todos os itens estão em situação normal")

    # =============================================================================
    #                            UTILITÁRIOS
    # =============================================================================

    def buscar_itens_por_criterio(
        self, 
        nome_parcial: Optional[str] = None,
        tipo_item: Optional[str] = None,
        politica: Optional[str] = None,
        abaixo_minimo: bool = False
    ) -> List[ItemAlmoxarifado]:
        """Busca avançada com múltiplos critérios"""
        resultado = self.almoxarifado.listar_itens()
        
        if nome_parcial:
            resultado = [item for item in resultado 
                        if nome_parcial.lower() in item.nome.lower() 
                        or nome_parcial.lower() in item.descricao.lower()]
        
        if tipo_item:
            resultado = [item for item in resultado if item.tipo_item == tipo_item]
        
        if politica:
            resultado = [item for item in resultado if item.politica_producao.value == politica]
        
        if abaixo_minimo:
            resultado = [item for item in resultado if item.esta_abaixo_do_minimo()]
        
        return resultado

    def validar_almoxarifado(self) -> List[str]:
        """Valida a integridade do almoxarifado"""
        problemas = self.almoxarifado.validar_integridade()
        
        if problemas:
            logger.warning(f"⚠️ Encontrados {len(problemas)} problemas de integridade:")
            for problema in problemas:
                logger.warning(f"   - {problema}")
        else:
            logger.info("✅ Almoxarifado validado com sucesso")
        
        return problemas

    def limpar_reservas_antigas(self, dias_atras: int = 30):
        """Remove reservas mais antigas que X dias"""
        data_limite = date.today() - timedelta(days=dias_atras)
        self.almoxarifado.limpar_reservas_expiradas(data_limite)
        logger.info(f"🧹 Removidas reservas anteriores a {data_limite}")

    def __repr__(self):
        return f"<GestorAlmoxarifado com {len(self.almoxarifado)} itens>"