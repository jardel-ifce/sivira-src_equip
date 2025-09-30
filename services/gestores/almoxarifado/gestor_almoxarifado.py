from datetime import datetime, date, timedelta
from typing import List, Tuple, Optional, Dict, TYPE_CHECKING
from models.almoxarifado.almoxarifado import Almoxarifado
from models.almoxarifado.item_almoxarifado import ItemAlmoxarifado
from enums.producao.politica_producao import PoliticaProducao
from utils.logs.logger_factory import setup_logger

if TYPE_CHECKING:
    from parser.parser_almoxarifado import ParserAlmoxarifado

logger = setup_logger('GestorAlmoxarifado')


class GestorAlmoxarifado:
    def __init__(self, almoxarifado: Almoxarifado, parser_almoxarifado: Optional['ParserAlmoxarifado'] = None):
        self.almoxarifado = almoxarifado
        self.parser_almoxarifado = parser_almoxarifado

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
        
        # Salvar estoque automaticamente após consumos
        if consumos:
            self._salvar_estoque_automaticamente()

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

        # Salvar estoque automaticamente após separação
        if itens_separados:
            self._salvar_estoque_automaticamente()

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

    def listar_todos_os_itens(self) -> List[ItemAlmoxarifado]:
        """Lista todos os itens do almoxarifado"""
        return self.almoxarifado.listar_itens()

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

    # =============================================================================
    #                      PROCESSAMENTO DE COMANDAS
    # =============================================================================

    def processar_comandas_e_reservar_itens(self, pasta_comandas: str = "data/comandas/") -> Dict:
        """
        Processa todas as comandas da pasta especificada e RESERVA os itens do almoxarifado.
        
        Args:
            pasta_comandas: Caminho para pasta com arquivos JSON de comandas
            
        Returns:
            Dict com relatório do processamento:
            - sucesso: True se processou com sucesso
            - comandas_processadas: número de comandas processadas
            - itens_reservados: lista de itens reservados
            - itens_com_estoque_insuficiente: lista de itens sem estoque para reserva
            - total_reservas: número total de operações de reserva
            - pasta_comandas: pasta processada
            - erro: mensagem de erro se houver falha
        """
        from parser.gerenciador_json_comandas import ler_comandas_em_pasta
        from datetime import datetime
        
        logger.info(f"🧾 Iniciando processamento de comandas da pasta: {pasta_comandas}")
        
        # Resultado do processamento
        resultado = {
            "sucesso": False,
            "comandas_processadas": 0,
            "itens_reservados": [],
            "itens_com_estoque_insuficiente": [],
            "total_reservas": 0,
            "pasta_comandas": pasta_comandas,
            "erros": []
        }
        
        try:
            # Ler todas as comandas da pasta
            reservas = ler_comandas_em_pasta(pasta_comandas)
            
            if not reservas:
                logger.info("📭 Nenhuma comanda encontrada para processar")
                return resultado
            
            logger.info(f"📋 Encontradas {len(reservas)} operações de reserva para processar")
            
            # Extrair data da reserva da primeira comanda
            data_reserva = None
            comandas_ids = set()
            
            for reserva in reservas:
                comandas_ids.add(f"Ordem {reserva['id_ordem']} - Pedido {reserva['id_pedido']}")
                if not data_reserva:
                    # Extrair data da primeira reserva
                    data_str = reserva.get('data_reserva', datetime.now().strftime('%Y-%m-%d'))
                    data_reserva = datetime.strptime(data_str, '%Y-%m-%d')
            
            if not data_reserva:
                data_reserva = datetime.now()
            
            resultado["comandas_processadas"] = len(comandas_ids)
            
            logger.info(f"📊 Resumo: {len(reservas)} reservas para data {data_reserva.strftime('%Y-%m-%d')}")
            logger.info(f"🏷️ Comandas envolvidas: {', '.join(sorted(comandas_ids))}")
            
            # Processar cada reserva individualmente
            for reserva in reservas:
                try:
                    id_item = reserva['id_item']
                    quantidade = reserva['quantidade_necessaria']
                    id_ordem = reserva['id_ordem']
                    id_pedido = reserva['id_pedido']
                    id_atividade = reserva.get('id_atividade')
                    
                    item = self.almoxarifado.buscar_item_por_id(id_item)
                    
                    if not item:
                        erro_msg = f"Item {id_item} não encontrado no almoxarifado"
                        logger.error(f"❌ {erro_msg}")
                        resultado["erros"].append(erro_msg)
                        continue
                    
                    logger.info(f"📦 Reservando: {item.descricao} (ID: {id_item})")
                    logger.info(f"   📊 Quantidade: {quantidade:.2f} {item.unidade_medida.value}")
                    logger.info(f"   📅 Data: {data_reserva.strftime('%Y-%m-%d')}")
                    
                    # Verificar se tem estoque para reservar
                    if not item.tem_estoque_para(data_reserva, quantidade):
                        estoque_projetado = item.estoque_projetado_em(data_reserva)
                        logger.warning(f"   ⚠️ Estoque insuficiente para reserva!")
                        logger.warning(f"   📊 Estoque projetado: {estoque_projetado:.2f} {item.unidade_medida.value}")
                        
                        resultado["itens_com_estoque_insuficiente"].append({
                            "id_item": id_item,
                            "nome": item.descricao,
                            "estoque_projetado": round(estoque_projetado, 2),
                            "quantidade_solicitada": round(quantidade, 2),
                            "unidade": item.unidade_medida.value,
                            "data_reserva": data_reserva.strftime('%Y-%m-%d')
                        })
                        continue
                    
                    # Fazer a reserva
                    item.reservar(
                        data=data_reserva,
                        quantidade=quantidade,
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade
                    )
                    
                    resultado["itens_reservados"].append({
                        "id_item": id_item,
                        "nome": item.descricao,
                        "quantidade_reservada": round(quantidade, 2),
                        "estoque_atual": round(item.estoque_atual, 2),
                        "estoque_projetado": round(item.estoque_projetado_em(data_reserva), 2),
                        "unidade": item.unidade_medida.value,
                        "data_reserva": data_reserva.strftime('%Y-%m-%d'),
                        "id_ordem": id_ordem,
                        "id_pedido": id_pedido
                    })
                    
                    logger.info(f"   ✅ Reservado: {quantidade:.2f} {item.unidade_medida.value}")
                    resultado["total_reservas"] += 1
                    
                except Exception as e:
                    erro_msg = f"Erro ao reservar item {id_item}: {str(e)}"
                    logger.error(f"❌ {erro_msg}")
                    resultado["erros"].append(erro_msg)
                    continue
            
            # Relatório final
            logger.info("=" * 60)
            logger.info("📊 RELATÓRIO FINAL DE RESERVAS")
            logger.info("=" * 60)
            logger.info(f"✅ Comandas processadas: {resultado['comandas_processadas']}")
            logger.info(f"📋 Itens reservados com sucesso: {len(resultado['itens_reservados'])}")
            logger.info(f"⚠️ Itens com estoque insuficiente: {len(resultado['itens_com_estoque_insuficiente'])}")
            logger.info(f"🔢 Total de reservas: {resultado['total_reservas']}")
            logger.info(f"❌ Erros encontrados: {len(resultado['erros'])}")
            
            # Marcar como sucesso se não houve erros críticos
            resultado["sucesso"] = len(resultado["erros"]) == 0
            
            if resultado["erros"]:
                logger.warning("⚠️ Erros durante processamento:")
                for erro in resultado["erros"]:
                    logger.warning(f"   - {erro}")
            
        except Exception as e:
            erro_msg = f"Erro crítico no processamento de comandas: {str(e)}"
            logger.error(f"💥 {erro_msg}")
            resultado["erros"].append(erro_msg)
            resultado["erro"] = erro_msg
        
        return resultado

    def despachar_reservas_e_consumir_itens(self, data_despacho=None, id_ordem=None, id_pedido=None) -> Dict:
        """
        Despacha reservas existentes e consome os itens do almoxarifado.
        
        Args:
            data_despacho: Data do despacho (datetime). Se None, usa data atual
            id_ordem: ID da ordem específica a despachar. Se None, despacha todas
            id_pedido: ID do pedido específico a despachar. Se None, despacha todos da ordem
            
        Returns:
            Dict com relatório do despacho:
            - sucesso: True se despachado com sucesso
            - reservas_despachadas: número de reservas despachadas
            - itens_despachados: lista de itens despachados
            - reservas_nao_encontradas: reservas que não puderam ser despachadas
            - total_consumo: número total de operações de consumo
            - erro: mensagem de erro se houver falha
        """
        from datetime import datetime, date
        
        if data_despacho is None:
            data_despacho = datetime.now()
        elif isinstance(data_despacho, date):
            data_despacho = datetime.combine(data_despacho, datetime.min.time())
        
        logger.info(f"🚚 Iniciando despacho de reservas para data: {data_despacho.strftime('%Y-%m-%d')}")
        
        resultado = {
            "sucesso": False,
            "reservas_despachadas": 0,
            "itens_despachados": [],
            "reservas_nao_encontradas": [],
            "total_consumo": 0,
            "data_despacho": data_despacho.strftime('%Y-%m-%d'),
            "filtros": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido
            },
            "erros": []
        }
        
        try:
            reservas_encontradas = []
            
            # Buscar todas as reservas dos itens para a data especificada
            for item in self.almoxarifado.itens:
                reservas_do_item = item.listar_reservas_por_periodo(
                    data_despacho.date(), 
                    data_despacho.date()
                )
                
                # Filtrar por ordem/pedido se especificado
                for reserva in reservas_do_item:
                    incluir_reserva = True
                    
                    if id_ordem is not None and reserva.get("id_ordem") != id_ordem:
                        incluir_reserva = False
                    
                    if id_pedido is not None and reserva.get("id_pedido") != id_pedido:
                        incluir_reserva = False
                    
                    if incluir_reserva:
                        reservas_encontradas.append({
                            "item": item,
                            "reserva": reserva
                        })
            
            if not reservas_encontradas:
                logger.info("📭 Nenhuma reserva encontrada para despacho com os filtros especificados")
                filtros_str = []
                if id_ordem: filtros_str.append(f"Ordem {id_ordem}")
                if id_pedido: filtros_str.append(f"Pedido {id_pedido}")
                logger.info(f"🔍 Filtros aplicados: {', '.join(filtros_str) if filtros_str else 'Nenhum'}")
                resultado["sucesso"] = True  # Sucesso mesmo sem reservas
                return resultado
            
            logger.info(f"📋 Encontradas {len(reservas_encontradas)} reservas para despachar")
            
            # Processar cada reserva
            for entrada in reservas_encontradas:
                item = entrada["item"]
                reserva = entrada["reserva"]
                
                try:
                    quantidade = reserva["quantidade"]
                    id_ordem_reserva = reserva.get("id_ordem", 0)
                    id_pedido_reserva = reserva.get("id_pedido", 0)
                    id_atividade = reserva.get("id_atividade")
                    
                    logger.info(f"🚚 Despachando: {item.descricao} (ID: {item.id_item})")
                    logger.info(f"   📊 Quantidade: {quantidade:.2f} {item.unidade_medida.value}")
                    logger.info(f"   📋 Ordem {id_ordem_reserva} - Pedido {id_pedido_reserva}")
                    
                    # Consumir o item (isso automaticamente cancela a reserva)
                    item.consumir(
                        data=data_despacho,
                        quantidade=quantidade,
                        id_ordem=id_ordem_reserva,
                        id_pedido=id_pedido_reserva,
                        id_atividade=id_atividade
                    )
                    
                    resultado["itens_despachados"].append({
                        "id_item": item.id_item,
                        "nome": item.descricao,
                        "quantidade_despachada": round(quantidade, 2),
                        "estoque_anterior": round(item.estoque_atual + quantidade, 2),
                        "estoque_final": round(item.estoque_atual, 2),
                        "unidade": item.unidade_medida.value,
                        "id_ordem": id_ordem_reserva,
                        "id_pedido": id_pedido_reserva,
                        "data_despacho": data_despacho.strftime('%Y-%m-%d')
                    })
                    
                    logger.info(f"   ✅ Despachado e consumido: {quantidade:.2f} {item.unidade_medida.value}")
                    resultado["total_consumo"] += 1
                    resultado["reservas_despachadas"] += 1
                    
                except Exception as e:
                    erro_msg = f"Erro ao despachar reserva do item {item.id_item}: {str(e)}"
                    logger.error(f"❌ {erro_msg}")
                    resultado["erros"].append(erro_msg)
                    
                    resultado["reservas_nao_encontradas"].append({
                        "id_item": item.id_item,
                        "nome": item.descricao,
                        "erro": str(e)
                    })
                    continue
            
            # Relatório final
            logger.info("=" * 60)
            logger.info("📊 RELATÓRIO FINAL DE DESPACHO")
            logger.info("=" * 60)
            logger.info(f"✅ Reservas despachadas: {resultado['reservas_despachadas']}")
            logger.info(f"🚚 Itens despachados: {len(resultado['itens_despachados'])}")
            logger.info(f"⚠️ Reservas com erro: {len(resultado['reservas_nao_encontradas'])}")
            logger.info(f"🔢 Total de consumos: {resultado['total_consumo']}")
            logger.info(f"❌ Erros encontrados: {len(resultado['erros'])}")
            
            # Marcar como sucesso se não houve erros críticos
            resultado["sucesso"] = len(resultado["erros"]) == 0
            
            # Salvar estoque automaticamente se houve consumos
            if resultado['reservas_despachadas'] > 0:
                self._salvar_estoque_automaticamente()
            
            if resultado["erros"]:
                logger.warning("⚠️ Erros durante despacho:")
                for erro in resultado["erros"]:
                    logger.warning(f"   - {erro}")
        
        except Exception as e:
            erro_msg = f"Erro crítico no despacho de reservas: {str(e)}"
            logger.error(f"💥 {erro_msg}")
            resultado["erros"].append(erro_msg)
            resultado["erro"] = erro_msg
        
        return resultado

    def _salvar_estoque_automaticamente(self):
        """Salva automaticamente o estoque atualizado no arquivo JSON se parser estiver disponível"""
        if self.parser_almoxarifado:
            try:
                logger.info("💾 Salvando estoque atualizado automaticamente...")
                self.parser_almoxarifado.salvar_itens_modificados()
                logger.info("✅ Estoque salvo com sucesso no arquivo JSON")
            except Exception as e:
                logger.error(f"❌ Erro ao salvar estoque automaticamente: {e}")
        else:
            logger.debug("⚠️ Parser não disponível - estoque não salvo automaticamente")

    def __repr__(self):
        return f"<GestorAlmoxarifado com {len(self.almoxarifado)} itens>"