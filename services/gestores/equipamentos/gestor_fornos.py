from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equipamentos.forno import Forno
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.producao.conversores_ocupacao import gramas_para_niveis_tela, unidades_para_niveis_tela
from utils.logs.logger_factory import setup_logger
from enums.producao.tipo_item import TipoItem
import unicodedata


logger = setup_logger('GestorFornos')


class GestorFornos:
    """
    🔥 Gestor especializado no controle de fornos.
    Utiliza backward scheduling e FIP (Fatores de Importância de Prioridade).
    ✔️ CORREÇÃO: Implementa ETAPA 0 para soma de ocupações com horários EXATOS.
    """

    def __init__(self, fornos: List['Forno']):
        self.fornos = fornos

    # REMOVIDO: Métodos de agrupamento explícito (agora implícito nos equipamentos)

    # REMOVIDO: Método de agrupamento explícito (agora implícito nos equipamentos)


    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List['Forno']:
        ordenados = sorted(
            self.fornos,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        return ordenados

    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _normalizar_nome(self, nome: str) -> str:
        nome_bruto = nome.lower().replace(" ", "_")
        return unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

    def _obter_temperatura_desejada(self, atividade: "AtividadeModular", forno: 'Forno') -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "faixa_temperatura" in config:
                return int(config["faixa_temperatura"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter temperatura para {forno.nome}: {e}")
        return None

    def _obter_vaporizacao_desejada(self, atividade: "AtividadeModular", forno: 'Forno') -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "vaporizacao" in config:
                return int(config["vaporizacao"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter vaporizacao para {forno.nome}: {e}")
        return None

    def _obter_velocidade_desejada(self, atividade: "AtividadeModular", forno: 'Forno') -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "velocidade_mps" in config:
                return int(config["velocidade_mps"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter velocidade para {forno.nome}: {e}")
        return None

    def _obter_unidades_por_nivel(self, atividade: "AtividadeModular", forno: 'Forno') -> Optional[int]:
        """
        Obtém a quantidade de unidades por nível do forno a partir da configuração da atividade.
        """
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "unidades_por_nivel" in config:
                return int(config["unidades_por_nivel"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter unidades por nível para {forno.nome}: {e}")
        return None
    
    def _obter_gramas_por_nivel(self, atividade: "AtividadeModular", forno: 'Forno') -> Optional[int]:
        """
        Obtém a quantidade de gramas por nível do forno a partir da configuração da atividade.
        """
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "gramas_por_nivel" in config:
                return int(config["gramas_por_nivel"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter gramas por nível para {forno.nome}: {e}")
        return None

    def _obter_quantidade_niveis(
        self,
        quantidade: int,
        unidades_por_nivel: Optional[int],
        gramas_por_nivel: Optional[int]
    ) -> int:
        """
        Converte a quantidade em número de níveis de tela.
        - Se unidades_por_nivel for fornecido, converte com base em unidades.
        - Se gramas_por_nivel for fornecido, converte com base em gramas.
        """
        if unidades_por_nivel is not None:
            return unidades_para_niveis_tela(quantidade, unidades_por_nivel)
        elif gramas_por_nivel is not None:
            return gramas_para_niveis_tela(quantidade, gramas_por_nivel)
        else:
            raise ValueError("❌ Não foi possível determinar o número de níveis: informe unidades_por_nivel ou gramas_por_nivel.")

    # ==========================================================
    # 🔥 MÉTODO PRINCIPAL DE ALOCAÇÃO - INTERFACE PÚBLICA CORRIGIDA
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: float,
        
    ) -> Tuple[bool, Optional[List['Forno']], Optional[datetime], Optional[datetime]]:
        """
        🔥 ÚNICO método público - Interface para AtividadeModular.
        
        REMOVIDO: Lógica de agrupamento (agora implícita nos equipamentos):
        🔄 ETAPA 0: Tenta soma de ocupações com horários EXATOS
        🎯 FASE 1: Tenta usar UM forno completo (prioriza capacidade sobre FIP)
        🔄 FASE 2: Se produto existe, tenta compartilhar níveis + complemento no MESMO forno  
        🧩 FASE 3: Se necessário, fraciona entre múltiplos fornos
        """
        
        # 📊 Validação e conversão de entrada
        quantidade_int = int(quantidade)
        
        if quantidade_int != quantidade:
            logger.warning(f"⚠️ Quantidade {quantidade} convertida para {quantidade_int}")
        
        if quantidade_int <= 0:
            logger.error(f"❌ Quantidade inválida: {quantidade}")
            return False, None, None, None
            
        # Obter IDs da atividade
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0) 
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', getattr(atividade, 'id_produto', 0))
            
        logger.info("=" * 60)
        logger.info(f"🔥 INICIANDO ALOCAÇÃO - ALGORITMO CORRIGIDO COM ETAPA 0")
        logger.info(f"📦 Produto: {id_item}")
        logger.info(f"📊 Quantidade: {quantidade_int}")
        logger.info(f"⏰ Intervalo: {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}")
        logger.info(f"⏱️ Duração: {atividade.duracao}")
        logger.info("=" * 60)
        
        # REMOVIDO: Lógica explícita de agrupamento (agora implícita nos equipamentos)
        
        # ==========================================================
        # 🚀 ETAPAS 1-3: Executar algoritmo original das 3 fases
        # ==========================================================
        logger.info("🔍 Agrupamento não possível, executando algoritmo das 3 fases...")
        
        resultado = self._executar_algoritmo_3_fases(
            inicio=inicio,
            fim=fim,
            atividade=atividade,
            quantidade=quantidade_int
        )
        
        # 📝 Log do resultado final
        sucesso, fornos_utilizados, inicio_real, fim_real = resultado
        
        if sucesso:
            logger.info("=" * 60)
            logger.info(f"✅ ALOCAÇÃO BEM-SUCEDIDA!")
            logger.info(f"📦 Produto {id_item}: {quantidade_int} unidades")
            logger.info(f"🏭 Fornos utilizados: {[f.nome for f in fornos_utilizados]} ({len(fornos_utilizados)} forno(s))")
            logger.info(f"⏰ Horário real: {inicio_real.strftime('%H:%M')} → {fim_real.strftime('%H:%M')}")
            logger.info(f"🎯 Estratégia: {'Forno único' if len(fornos_utilizados) == 1 else 'Fracionamento'}")
            logger.info("=" * 60)
        else:
            logger.error("=" * 60)
            logger.error(f"❌ ALOCAÇÃO FALHOU!")
            logger.error(f"📦 Produto {id_item}: {quantidade_int} unidades")
            logger.error(f"⏰ Intervalo tentado: {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}")
            logger.error(f"🚫 Nenhum forno conseguiu atender a demanda")
            logger.error("=" * 60)
            
        return resultado

    # ==========================================================
    # 🔧 Métodos Auxiliares Privados (Organização Interna) - Mantidos Iguais
    # ==========================================================
    
    def _executar_algoritmo_3_fases(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: int
    ) -> Tuple[bool, Optional[List['Forno']], Optional[datetime], Optional[datetime]]:
        """
        🎯 Executa o algoritmo das 3 fases com backward scheduling.
        """
        duracao = atividade.duracao
        fornos_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim
        tentativa_count = 0

        while horario_final_tentativa - duracao >= inicio:
            tentativa_count += 1
            horario_inicial_tentativa = horario_final_tentativa - duracao
            
            if tentativa_count % 10 == 0:
                logger.debug(f"⏰ Tentativa {tentativa_count}: {horario_inicial_tentativa.strftime('%H:%M')} → {horario_final_tentativa.strftime('%H:%M')}")

            # 🎯 FASE 1: Tentar usar UM forno completo
            resultado_fase1 = self._fase1_forno_completo(
                inicio=horario_inicial_tentativa,
                fim=horario_final_tentativa,
                atividade=atividade,
                quantidade=quantidade,
                fornos_ordenados=fornos_ordenados
            )
            
            if resultado_fase1[0]:  # Sucesso na Fase 1
                logger.info("✅ Alocação resolvida na FASE 1 (forno completo)")
                return resultado_fase1

            # 🔄 FASE 2: Tentar compartilhar + complemento no MESMO forno
            resultado_fase2 = self._fase2_compartilhar_mesmo_forno(
                inicio=horario_inicial_tentativa,
                fim=horario_final_tentativa,
                atividade=atividade,
                quantidade=quantidade,
                fornos_ordenados=fornos_ordenados
            )
            
            if resultado_fase2[0]:  # Sucesso na Fase 2
                logger.info("✅ Alocação resolvida na FASE 2 (compartilhamento + complemento)")
                return resultado_fase2

            # 🧩 FASE 3: Fracionar entre múltiplos fornos
            resultado_fase3 = self._fase3_fracionamento_multiplos_fornos(
                inicio=horario_inicial_tentativa,
                fim=horario_final_tentativa,
                atividade=atividade,
                quantidade=quantidade,
                fornos_ordenados=fornos_ordenados
            )
            
            if resultado_fase3[0]:  # Sucesso na Fase 3
                logger.info("✅ Alocação resolvida na FASE 3 (fracionamento)")
                return resultado_fase3

            # Se todas as 3 fases falharam neste horário, tentar horário anterior
            horario_final_tentativa -= timedelta(minutes=1)

        logger.error("🛑 Limite da jornada atingido. Impossível alocar a atividade.")
        return False, None, None, None

    def _fase1_forno_completo(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: int,
        fornos_ordenados: List['Forno']
    ) -> Tuple[bool, Optional[List['Forno']], Optional[datetime], Optional[datetime]]:
        """
        🎯 FASE 1: Tenta usar UM forno completo (prioriza aproveitamento de espaço)
        
        Estratégia otimizada:
        1. PRIMEIRO: Verifica se algum forno pode atender COMPLETAMENTE através de aproveitamento + complemento
        2. SEGUNDO: Se não houver aproveitamento, busca fornos com níveis completamente livres
        """
        logger.info("🎯 FASE 1: Tentando alocar em um único forno completo (priorizando aproveitamento)...")
        
        # 🔄 PRIORIDADE 1: Fornos com produto existente que podem atender completamente
        fornos_com_aproveitamento = []
        
        for forno in fornos_ordenados:
            temperatura = self._obter_temperatura_desejada(atividade, forno)
            vaporizacao = self._obter_vaporizacao_desejada(atividade, forno)
            velocidade = self._obter_velocidade_desejada(atividade, forno)
            unidades_por_nivel = self._obter_unidades_por_nivel(atividade, forno)
            gramas_por_nivel = self._obter_gramas_por_nivel(atividade, forno)

            if not unidades_por_nivel and not gramas_por_nivel:
                continue

            # 🔍 Verificar se produto existe neste forno
            produto_existe = forno.existe_produto_em_algum_nivel(
                id_item=atividade.id_item,
                inicio=inicio,
                fim=fim,
                temperatura=temperatura,
                vaporizacao=vaporizacao,
                velocidade=velocidade
            )

            if produto_existe:
                logger.debug(f"🔄 FASE 1: Produto {atividade.id_item} EXISTE no {forno.nome} - verificando aproveitamento")
                
                # Calcular aproveitamento possível
                niveis_ocupados = forno.retornar_espaco_ocupado_por_nivel(
                    id_item=atividade.id_item,
                    inicio=inicio,
                    fim=fim,
                    temperatura=temperatura,
                    vaporizacao=vaporizacao,
                    velocidade=velocidade
                )

                capacidade_por_nivel = unidades_por_nivel or gramas_por_nivel
                quantidade_aproveitamento = 0

                for nivel, ocupado in niveis_ocupados:
                    capacidade_restante = capacidade_por_nivel - ocupado
                    aproveitamento = min(capacidade_restante, quantidade - quantidade_aproveitamento)
                    quantidade_aproveitamento += aproveitamento

                quantidade_restante_apos_aproveitamento = quantidade - quantidade_aproveitamento
                
                if quantidade_restante_apos_aproveitamento > 0:
                    try:
                        niveis_necessarios_restante = self._obter_quantidade_niveis(
                            quantidade=quantidade_restante_apos_aproveitamento,
                            unidades_por_nivel=unidades_por_nivel,
                            gramas_por_nivel=gramas_por_nivel
                        )
                    except ValueError:
                        continue

                    niveis_disponiveis = forno.retornar_quantidade_de_niveis_disponiveis(
                        inicio=inicio,
                        fim=fim,
                        temperatura=temperatura,
                        vaporizacao=vaporizacao,
                        velocidade=velocidade
                    )

                    if niveis_disponiveis < niveis_necessarios_restante:
                        continue

                # ✅ Este forno pode atender COMPLETAMENTE com aproveitamento!
                fornos_com_aproveitamento.append({
                    'forno': forno,
                    'tipo': 'aproveitamento',
                    'quantidade_aproveitamento': quantidade_aproveitamento,
                    'quantidade_restante': quantidade_restante_apos_aproveitamento,
                    'niveis_necessarios_restante': niveis_necessarios_restante if quantidade_restante_apos_aproveitamento > 0 else 0,
                    'temperatura': temperatura,
                    'vaporizacao': vaporizacao,
                    'velocidade': velocidade,
                    'unidades_por_nivel': unidades_por_nivel,
                    'gramas_por_nivel': gramas_por_nivel,
                    'fip': atividade.fips_equipamentos.get(forno, 999)
                })

        # 🎯 Se encontrou fornos com aproveitamento, usar o de menor FIP
        if fornos_com_aproveitamento:
            forno_escolhido = min(fornos_com_aproveitamento, key=lambda x: x['fip'])
            forno = forno_escolhido['forno']
            
            logger.info(f"🔄 FASE 1: APROVEITAMENTO - Forno {forno.nome} escolhido (FIP: {forno_escolhido['fip']})")

            # Executar aproveitamento
            sucesso_total = True
            
            if forno_escolhido['quantidade_aproveitamento'] > 0:
                sucesso_aproveitamento = forno.ocupar_niveis_parcialmente_preenchidos(
                    id_ordem=atividade.id_ordem,
                    id_pedido=atividade.id_pedido,
                    id_atividade=atividade.id_atividade,
                    id_item=atividade.id_item,
                    inicio=inicio,
                    fim=fim,
                    temperatura=forno_escolhido['temperatura'],
                    vaporizacao=forno_escolhido['vaporizacao'],
                    velocidade=forno_escolhido['velocidade'],
                    quantidade=forno_escolhido['quantidade_aproveitamento'],
                    unidades_por_nivel=forno_escolhido['unidades_por_nivel'],
                    gramas_por_nivel=forno_escolhido['gramas_por_nivel']
                )
                
                if not sucesso_aproveitamento:
                    logger.warning(f"⚠️ FASE 1: Falha no aproveitamento no forno {forno.nome}")
                    sucesso_total = False

            # Executar complemento se necessário
            if sucesso_total and forno_escolhido['quantidade_restante'] > 0:
                sucesso_complemento = forno.ocupar_niveis_exatos_com_capacidade_total(
                    id_ordem=atividade.id_ordem,
                    id_pedido=atividade.id_pedido,
                    id_atividade=atividade.id_atividade,
                    id_item=atividade.id_item,
                    inicio=inicio,
                    fim=fim,
                    temperatura=forno_escolhido['temperatura'],
                    vaporizacao=forno_escolhido['vaporizacao'],
                    velocidade=forno_escolhido['velocidade'],
                    quantidade=forno_escolhido['quantidade_restante'],
                    niveis_necessarios=forno_escolhido['niveis_necessarios_restante'],
                    unidades_por_nivel=forno_escolhido['unidades_por_nivel'],
                    gramas_por_nivel=forno_escolhido['gramas_por_nivel']
                )
                
                if not sucesso_complemento:
                    logger.warning(f"⚠️ FASE 1: Falha no complemento no forno {forno.nome}")
                    # Reverter aproveitamento se houve
                    if forno_escolhido['quantidade_aproveitamento'] > 0:
                        forno.liberar_por_atividade(atividade.id_ordem, atividade.id_pedido, atividade.id_atividade)
                    sucesso_total = False

            if sucesso_total:
                logger.info(f"✅ FASE 1: Alocação completa no forno {forno.nome} (APROVEITAMENTO + complemento)")
                return True, [forno], inicio, fim

        # 🎯 PRIORIDADE 2: Fornos com níveis completamente livres (só se não houver aproveitamento)
        logger.info("🔍 FASE 1: Não há aproveitamento viável - buscando fornos com níveis livres...")
        
        fornos_capazes = []
        
        for forno in fornos_ordenados:
            temperatura = self._obter_temperatura_desejada(atividade, forno)
            vaporizacao = self._obter_vaporizacao_desejada(atividade, forno)
            velocidade = self._obter_velocidade_desejada(atividade, forno)
            unidades_por_nivel = self._obter_unidades_por_nivel(atividade, forno)
            gramas_por_nivel = self._obter_gramas_por_nivel(atividade, forno)

            if not unidades_por_nivel and not gramas_por_nivel:
                continue

            try:
                niveis_necessarios = self._obter_quantidade_niveis(
                    quantidade=quantidade,
                    unidades_por_nivel=unidades_por_nivel,
                    gramas_por_nivel=gramas_por_nivel
                )
            except ValueError:
                continue

            niveis_disponiveis = forno.retornar_quantidade_de_niveis_disponiveis(
                inicio=inicio,
                fim=fim,
                temperatura=temperatura,
                vaporizacao=vaporizacao,
                velocidade=velocidade
            )

            if niveis_disponiveis >= niveis_necessarios:
                fornos_capazes.append({
                    'forno': forno,
                    'tipo': 'niveis_livres',
                    'niveis_disponiveis': niveis_disponiveis,
                    'niveis_necessarios': niveis_necessarios,
                    'temperatura': temperatura,
                    'vaporizacao': vaporizacao,
                    'velocidade': velocidade,
                    'unidades_por_nivel': unidades_por_nivel,
                    'gramas_por_nivel': gramas_por_nivel,
                    'fip': atividade.fips_equipamentos.get(forno, 999)
                })

        if not fornos_capazes:
            logger.debug("❌ FASE 1: Nenhum forno consegue atender completamente")
            return False, None, None, None

        # 🎯 Escolher o de menor FIP entre os capazes
        forno_escolhido = min(fornos_capazes, key=lambda x: x['fip'])
        forno = forno_escolhido['forno']
        
        logger.info(f"✅ FASE 1: NÍVEIS LIVRES - Forno {forno.nome} escolhido (pode atender completamente)")

        sucesso = forno.ocupar_niveis_exatos_com_capacidade_total(
            id_ordem=atividade.id_ordem,
            id_pedido=atividade.id_pedido,
            id_atividade=atividade.id_atividade,
            id_item=atividade.id_item,
            inicio=inicio,
            fim=fim,
            temperatura=forno_escolhido['temperatura'],
            vaporizacao=forno_escolhido['vaporizacao'],
            velocidade=forno_escolhido['velocidade'],
            quantidade=quantidade,
            niveis_necessarios=forno_escolhido['niveis_necessarios'],
            unidades_por_nivel=forno_escolhido['unidades_por_nivel'],
            gramas_por_nivel=forno_escolhido['gramas_por_nivel']
        )

        if sucesso:
            logger.info(f"✅ FASE 1: Alocação completa no forno {forno.nome} (NÍVEIS LIVRES)")
            return True, [forno], inicio, fim
        else:
            logger.warning(f"⚠️ FASE 1: Falha na alocação no forno {forno.nome}")
            return False, None, None, None

    def _fase2_compartilhar_mesmo_forno(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: int,
        fornos_ordenados: List['Forno']
    ) -> Tuple[bool, Optional[List['Forno']], Optional[datetime], Optional[datetime]]:
        """
        🔄 FASE 2: Tenta compartilhar níveis do mesmo produto + complemento no MESMO forno
        """
        logger.debug("🔄 FASE 2: Tentando compartilhamento + complemento no mesmo forno...")
        
        for forno in fornos_ordenados:
            temperatura = self._obter_temperatura_desejada(atividade, forno)
            vaporizacao = self._obter_vaporizacao_desejada(atividade, forno)
            velocidade = self._obter_velocidade_desejada(atividade, forno)
            unidades_por_nivel = self._obter_unidades_por_nivel(atividade, forno)
            gramas_por_nivel = self._obter_gramas_por_nivel(atividade, forno)

            if not unidades_por_nivel and not gramas_por_nivel:
                continue

            # Verificar se o produto existe neste forno
            produto_existe = forno.existe_produto_em_algum_nivel(
                id_item=atividade.id_item,
                inicio=inicio,
                fim=fim,
                temperatura=temperatura,
                vaporizacao=vaporizacao,
                velocidade=velocidade
            )

            if not produto_existe:
                continue

            logger.debug(f"🔍 FASE 2: Produto {atividade.id_item} existe no {forno.nome}")
            # Esta fase é similar à FASE 1 prioridade 1, mas foi mantida para organização
            # Na prática, a FASE 1 já cobre este cenário, então retornamos False
            
        logger.debug("❌ FASE 2: Nenhum forno consegue compartilhar + complementar")
        return False, None, None, None

    def _fase3_fracionamento_multiplos_fornos(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: int,
        fornos_ordenados: List['Forno']
    ) -> Tuple[bool, Optional[List['Forno']], Optional[datetime], Optional[datetime]]:
        """
        🧩 FASE 3: Fraciona entre múltiplos fornos
        """
        logger.debug("🧩 FASE 3: Tentando fracionamento entre múltiplos fornos...")
        
        # Verificar viabilidade primeiro
        plano_alocacao = []
        quantidade_restante = quantidade
        
        for forno in fornos_ordenados:
            if quantidade_restante <= 0:
                break
                
            temperatura = self._obter_temperatura_desejada(atividade, forno)
            vaporizacao = self._obter_vaporizacao_desejada(atividade, forno)
            velocidade = self._obter_velocidade_desejada(atividade, forno)
            unidades_por_nivel = self._obter_unidades_por_nivel(atividade, forno)
            gramas_por_nivel = self._obter_gramas_por_nivel(atividade, forno)

            if not unidades_por_nivel and not gramas_por_nivel:
                continue

            capacidade_por_nivel = unidades_por_nivel or gramas_por_nivel

            # Calcular níveis livres disponíveis
            niveis_disponiveis = forno.retornar_quantidade_de_niveis_disponiveis(
                inicio=inicio,
                fim=fim,
                temperatura=temperatura,
                vaporizacao=vaporizacao,
                velocidade=velocidade
            )

            capacidade_maxima = niveis_disponiveis * capacidade_por_nivel
            quantidade_para_este_forno = min(quantidade_restante, capacidade_maxima)

            if quantidade_para_este_forno > 0:
                try:
                    niveis_necessarios = self._obter_quantidade_niveis(
                        quantidade=quantidade_para_este_forno,
                        unidades_por_nivel=unidades_por_nivel,
                        gramas_por_nivel=gramas_por_nivel
                    )
                except ValueError:
                    continue

                plano_alocacao.append({
                    'forno': forno,
                    'quantidade': quantidade_para_este_forno,
                    'niveis_necessarios': niveis_necessarios,
                    'temperatura': temperatura,
                    'vaporizacao': vaporizacao,
                    'velocidade': velocidade,
                    'unidades_por_nivel': unidades_por_nivel,
                    'gramas_por_nivel': gramas_por_nivel,
                    'fip': atividade.fips_equipamentos.get(forno, 999)
                })

                quantidade_restante -= quantidade_para_este_forno

        # Verificar se plano é viável
        if quantidade_restante > 0:
            logger.debug(f"❌ FASE 3: Plano inviável - Faltam {quantidade_restante} unidades")
            return False, None, None, None
        
        # Executar o plano
        fornos_utilizados = []
        
        for alocacao in plano_alocacao:
            forno = alocacao['forno']
            
            sucesso = forno.ocupar_niveis_exatos_com_capacidade_total(
                id_ordem=atividade.id_ordem,
                id_pedido=atividade.id_pedido,
                id_atividade=atividade.id_atividade,
                id_item=atividade.id_item,
                inicio=inicio,
                fim=fim,
                temperatura=alocacao['temperatura'],
                vaporizacao=alocacao['vaporizacao'],
                velocidade=alocacao['velocidade'],
                quantidade=alocacao['quantidade'],
                niveis_necessarios=alocacao['niveis_necessarios'],
                unidades_por_nivel=alocacao['unidades_por_nivel'],
                gramas_por_nivel=alocacao['gramas_por_nivel']
            )
            
            if sucesso:
                fornos_utilizados.append(forno)
                logger.debug(f"✅ {alocacao['quantidade']} unidades alocadas no {forno.nome}")
            else:
                # Rollback
                for f in fornos_utilizados:
                    f.liberar_por_atividade(atividade.id_ordem, atividade.id_pedido, atividade.id_atividade)
                return False, None, None, None

        logger.info(f"✅ FASE 3: Fracionamento bem-sucedido em {len(fornos_utilizados)} fornos")
        return True, fornos_utilizados, inicio, fim

    # ==========================================================
    # 🔓 Liberação (Métodos de Conveniência)
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por atividade em todos os fornos."""
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0)
        id_atividade = getattr(atividade, 'id_atividade', 0)
        
        for forno in self.fornos:
            forno.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por pedido em todos os fornos."""
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0)
        
        for forno in self.fornos:
            forno.liberar_por_pedido(id_ordem, id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por ordem em todos os fornos."""
        id_ordem = getattr(atividade, 'id_ordem', 0)
        
        for forno in self.fornos:
            forno.liberar_por_ordem(id_ordem)

    def liberar_todas_ocupacoes(self):
        """Libera todas as ocupações de todos os fornos."""
        for forno in self.fornos:
            # Limpar ocupações
            for nivel_ocupacoes in forno.niveis_ocupacoes:
                nivel_ocupacoes.clear()
            
            # Limpar registros de parâmetros
            forno.registro_temperatura.clear()
            forno.registro_vaporizacao.clear()
            forno.registro_velocidade.clear()
            
        logger.info("🔓 Todas as ocupações de todos os fornos foram removidas.")

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda de todos os fornos."""
        logger.info("==============================================")
        logger.info("📅 Agenda dos Fornos")
        logger.info("==============================================")
        
        for forno in self.fornos:
            logger.info(f"\n🔥 FORNO: {forno.nome}")
            tem_ocupacao = False
            
            for nivel_idx in range(forno.qtd_niveis):
                if forno.niveis_ocupacoes[nivel_idx]:
                    tem_ocupacao = True
                    logger.info(f"  📊 Nível {nivel_idx}:")
                    
                    for ocupacao in forno.niveis_ocupacoes[nivel_idx]:
                        logger.info(
                            f"    🔹 Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | "
                            f"Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                            f"{ocupacao[4]:.0f} unidades | "
                            f"{ocupacao[5].strftime('%H:%M')} → {ocupacao[6].strftime('%H:%M')}"
                        )
            
            if not tem_ocupacao:
                logger.info("  📭 Nenhuma ocupação registrada")

    def obter_estatisticas_globais(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas consolidadas de todos os fornos."""
        estatisticas = {
            'total_fornos': len(self.fornos),
            'total_niveis': sum(f.qtd_niveis for f in self.fornos),
            'niveis_utilizados': 0,
            'quantidade_total': 0.0,
            'fornos_utilizados': 0,
            'detalhes_por_forno': {}
        }

        for forno in self.fornos:
            niveis_utilizados_forno = 0
            quantidade_forno = 0.0
            
            for nivel_idx in range(forno.qtd_niveis):
                ocupacoes_periodo = [
                    ocupacao for ocupacao in forno.niveis_ocupacoes[nivel_idx]
                    if not (fim <= ocupacao[5] or inicio >= ocupacao[6])
                ]
                
                if ocupacoes_periodo:
                    niveis_utilizados_forno += 1
                    quantidade_forno += sum(oc[4] for oc in ocupacoes_periodo)
            
            estatisticas['detalhes_por_forno'][forno.nome] = {
                'niveis_utilizados': niveis_utilizados_forno,
                'niveis_total': forno.qtd_niveis,
                'quantidade_total': quantidade_forno,
                'taxa_utilizacao': (niveis_utilizados_forno / forno.qtd_niveis * 100) if forno.qtd_niveis > 0 else 0.0
            }
            
            estatisticas['niveis_utilizados'] += niveis_utilizados_forno
            estatisticas['quantidade_total'] += quantidade_forno
            
            if niveis_utilizados_forno > 0:
                estatisticas['fornos_utilizados'] += 1

        # Calcula taxa de utilização global
        if estatisticas['total_niveis'] > 0:
            estatisticas['taxa_utilizacao_global'] = (estatisticas['niveis_utilizados'] / estatisticas['total_niveis']) * 100
        else:
            estatisticas['taxa_utilizacao_global'] = 0.0

        return estatisticas