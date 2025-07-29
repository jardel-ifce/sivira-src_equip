from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.equipamentos.tipo_coccao import TipoCoccao
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('Forno')


class Forno(Equipamento):
    """
    🔥 Classe que representa um Forno para cocção de produtos.
    ✔️ Controle de temperatura, vaporização e velocidade.
    ✔️ Ocupação individual por nível com quantidade.
    ✔️ Permite sobreposição de produtos iguais no mesmo nível APENAS com horários EXATOS.
    ✔️ CORREÇÃO: Verifica coincidência exata de horários para compartilhamento.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        nivel_tela_min: int,
        nivel_tela_max: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int,
        setup_min: int,
        capacidade_niveis_min: int,
        capacidade_niveis_max: int,
        tipo_coccao: TipoCoccao,
        vaporizacao_seg_min: Optional[int] = None,
        vaporizacao_seg_max: Optional[int] = None,
        velocidade_mps_min: Optional[int] = None,
        velocidade_mps_max: Optional[int] = None,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.FORNOS,
            setor=setor,
            numero_operadores=0,
            status_ativo=True,
        )

        self.nivel_tela_min = nivel_tela_min
        self.capacidade_niveis_min = capacidade_niveis_min
        self.nivel_tela_max = nivel_tela_max
        self.qtd_niveis = nivel_tela_max * capacidade_niveis_max
        self.capacidade_por_nivel = capacidade_niveis_max
        # 📦 Ocupações: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
        self.niveis_ocupacoes: List[List[Tuple[int, int, int, int, float, datetime, datetime]]] = [[] for _ in range(self.qtd_niveis)]

        # 🌡️ Temperatura
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.temperatura_atual: Optional[int] = None

        # 💨 Vaporização
        self.tem_vaporizacao = vaporizacao_seg_min is not None and vaporizacao_seg_max is not None
        self.faixa_vaporizacao_min = vaporizacao_seg_min
        self.faixa_vaporizacao_max = vaporizacao_seg_max
        self.vaporizacao_atual: Optional[int] = None

        # 🚀 Velocidade
        self.tem_velocidade = velocidade_mps_min is not None and velocidade_mps_max is not None
        self.faixa_velocidade_min = velocidade_mps_min
        self.faixa_velocidade_max = velocidade_mps_max
        self.velocidade_atual: Optional[int] = None

        # 🔧 Outras configurações
        self.setup_min = setup_min
        self.tipo_coccao = tipo_coccao

        # 🧾 Registros de parâmetros aplicados por atividade: (id_ordem, id_pedido, id_atividade, nivel, valor_parametro, inicio, fim)
        self.registro_temperatura: List[Tuple[int, int, int, int, int, datetime, datetime]] = []
        self.registro_vaporizacao: List[Tuple[int, int, int, int, Optional[int], datetime, datetime]] = []
        self.registro_velocidade: List[Tuple[int, int, int, int, Optional[int], datetime, datetime]] = []

    # ==========================================================
    # 🌡️ Validação de temperatura
    # ==========================================================
    def selecionar_temperatura(self, temperatura: int) -> bool:
        if not self.faixa_temperatura_min <= temperatura <= self.faixa_temperatura_max:
            logger.warning(f"❌ Temperatura {temperatura}°C fora dos limites do forno {self.nome}.")
            return False
        self.temperatura_atual = temperatura
        return True

    def verificar_compatibilidade_temperatura(self, inicio: datetime, fim: datetime, temperatura: int) -> bool:
        conflitos = [registro[4] for registro in self.registro_temperatura if not (fim <= registro[5] or inicio >= registro[6])]
        if conflitos and not all(t == temperatura for t in conflitos):
            logger.warning(f"🚫 Incompatibilidade de temperatura no forno {self.nome}: esperada {temperatura}, encontradas {set(conflitos)}")
        return all(t == temperatura for t in conflitos) if conflitos else True

    # ==========================================================
    # 💨 Validação de vaporização
    # ==========================================================
    def selecionar_vaporizacao(self, vaporizacao: Optional[int], atividade_exige: bool) -> bool:
        if not self.tem_vaporizacao or not atividade_exige:
            return True
        if vaporizacao is None:
            logger.warning(f"❌ Vaporização não definida para o forno {self.nome}, mas é obrigatória.")
            return False
        if not self.faixa_vaporizacao_min <= vaporizacao <= self.faixa_vaporizacao_max:
            logger.warning(f"❌ Vaporização {vaporizacao}s fora dos limites.")
            return False
        self.vaporizacao_atual = vaporizacao
        return True

    def verificar_compatibilidade_vaporizacao(self, inicio: datetime, fim: datetime, vaporizacao: Optional[int]) -> bool:
        if not self.tem_vaporizacao:
            return True

        conflitos = [registro[4] for registro in self.registro_vaporizacao if not (fim <= registro[5] or inicio >= registro[6])]

        if conflitos and not all(v == vaporizacao for v in conflitos):
            logger.warning(
                f"🚫 Incompatibilidade de vaporização no forno {self.nome}: "
                f"esperada {vaporizacao}, encontradas {set(conflitos)}"
            )
            return False

        return True

    # ==========================================================
    # 🚀 Validação de velocidade
    # ==========================================================
    def selecionar_velocidade(self, velocidade: Optional[int], atividade_exige: bool) -> bool:
        if not self.tem_velocidade or not atividade_exige:
            return True
        if velocidade is None:
            logger.warning(f"❌ Velocidade não definida, mas é obrigatória.")
            return False
        if not self.faixa_velocidade_min <= velocidade <= self.faixa_velocidade_max:
            logger.warning(f"❌ Velocidade {velocidade} m/s fora dos limites.")
            return False
        self.velocidade_atual = velocidade
        return True

    def verificar_compatibilidade_velocidade(self, inicio: datetime, fim: datetime, velocidade: Optional[int]) -> bool:
        if not self.tem_velocidade:
            return True

        conflitos = [registro[4] for registro in self.registro_velocidade if not (fim <= registro[5] or inicio >= registro[6])]

        if conflitos and not all(v == velocidade for v in conflitos):
            logger.warning(
                f"🚫 Incompatibilidade de velocidade no forno {self.nome}: "
                f"esperada {velocidade}, encontradas {set(conflitos)}"
            )
            return False

        return True

    # ==========================================================
    # 📊 Verificação e ocupação
    # ==========================================================
    def retornar_quantidade_de_niveis_disponiveis(
        self,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int],
        vaporizacao: Optional[int],
        velocidade: Optional[int]
    ) -> int:
        """
        📊 Retorna a quantidade de níveis que estão livres e compatíveis
        com os parâmetros fornecidos.
        """
        quantidade = 0

        for idx in range(self.qtd_niveis):
            if self._nivel_esta_ocupado(idx, inicio, fim):
                logger.debug(f"⛔ Nível {idx} está ocupado entre {inicio} e {fim}")
                continue

            # 🔍 Verificação de compatibilidade de temperatura
            temp_ok = all(
                registro[4] == temperatura
                for registro in self.registro_temperatura
                if registro[3] == idx and not (fim <= registro[5] or inicio >= registro[6])
            )
            if not temp_ok:
                logger.debug(f"⛔ Nível {idx} reprovado por temperatura.")
                continue

            # 💨 Verificação de compatibilidade de vaporização
            if self.tem_vaporizacao:
                vapo_ok = all(
                    registro[4] == vaporizacao
                    for registro in self.registro_vaporizacao
                    if registro[3] == idx and not (fim <= registro[5] or inicio >= registro[6])
                )
                if not vapo_ok:
                    logger.debug(f"⛔ Nível {idx} reprovado por vaporização.")
                    continue

            # 🌀 Verificação de compatibilidade de velocidade
            if self.tem_velocidade:
                velo_ok = all(
                    registro[4] == velocidade
                    for registro in self.registro_velocidade
                    if registro[3] == idx and not (fim <= registro[5] or inicio >= registro[6])
                )
                if not velo_ok:
                    logger.debug(f"⛔ Nível {idx} reprovado por velocidade.")
                    continue

            # ✅ Aprovado
            logger.debug(f"✅ Nível {idx} considerado disponível.")
            quantidade += 1

        logger.info(f"📈 Total de níveis disponíveis: {quantidade}")
        return quantidade

    def existe_produto_em_algum_nivel(
        self,
        id_item: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int],
        vaporizacao: Optional[int],
        velocidade: Optional[int]
    ) -> bool:
        """
        🔍 Verifica se o produto está presente em algum nível com os parâmetros e intervalo informados.
        ✔️ CORREÇÃO: Verifica coincidência EXATA de horários.
        """
        for idx, ocupacoes in enumerate(self.niveis_ocupacoes):
            for ocupacao in ocupacoes:
                # 🎯 CORREÇÃO: Verifica horários EXATOS, não apenas sobreposição
                if (ocupacao[3] != id_item or 
                    ocupacao[5] != inicio or 
                    ocupacao[6] != fim):
                    continue

                temp_ok = all(registro[4] == temperatura for registro in self.registro_temperatura
                            if registro[3] == idx and registro[5] == inicio and registro[6] == fim)
                vap_ok = all(registro[4] == vaporizacao for registro in self.registro_vaporizacao
                            if self.tem_vaporizacao and registro[3] == idx and registro[5] == inicio and registro[6] == fim)
                vel_ok = all(registro[4] == velocidade for registro in self.registro_velocidade
                            if self.tem_velocidade and registro[3] == idx and registro[5] == inicio and registro[6] == fim)

                if temp_ok and vap_ok and vel_ok:
                    logger.info(f"🔁 Produto {id_item} já alocado no nível {idx} com parâmetros compatíveis e horários EXATOS.")
                    return True

        logger.debug(f"🚫 Produto {id_item} não encontrado em nenhum nível com os parâmetros e horários EXATOS fornecidos.")
        return False

    def retornar_espaco_ocupado_por_nivel(
        self,
        id_item: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int],
        vaporizacao: Optional[int],
        velocidade: Optional[int]
    ) -> List[Tuple[int, float]]:
        """
        📏 Retorna, para cada nível onde o produto já está presente e os parâmetros são compatíveis,
        uma tupla com (índice_nivel, quantidade_ocupada).
        ✔️ CORREÇÃO PRINCIPAL: Verifica coincidência EXATA de horários para compartilhamento.
        """
        niveis_ocupados = []

        for idx, ocupacoes in enumerate(self.niveis_ocupacoes):
            ocupacoes_ativas = []
            
            for ocupacao in ocupacoes:
                # 🎯 CORREÇÃO CRÍTICA: Só considera ocupações com horários EXATOS
                if (ocupacao[3] == id_item and 
                    ocupacao[5] == inicio and  # início EXATO
                    ocupacao[6] == fim):       # fim EXATO
                    ocupacoes_ativas.append(ocupacao)
            
            if not ocupacoes_ativas:
                continue

            # Verificar compatibilidade de parâmetros para horários EXATOS
            temp_ok = all(registro[4] == temperatura for registro in self.registro_temperatura
                        if registro[3] == idx and registro[5] == inicio and registro[6] == fim)
            vap_ok = all(registro[4] == vaporizacao for registro in self.registro_vaporizacao
                        if self.tem_vaporizacao and registro[3] == idx and registro[5] == inicio and registro[6] == fim)
            vel_ok = all(registro[4] == velocidade for registro in self.registro_velocidade
                        if self.tem_velocidade and registro[3] == idx and registro[5] == inicio and registro[6] == fim)

            if not (temp_ok and vap_ok and vel_ok):
                continue

            quantidade_ocupada = sum(ocupacao[4] for ocupacao in ocupacoes_ativas)
            niveis_ocupados.append((idx, quantidade_ocupada))
            logger.info(f"📊 Nível {idx} já possui {quantidade_ocupada}g do produto id {id_item} alocados com horários EXATOS.")

        if not niveis_ocupados:
            logger.debug(f"📭 Nenhum nível com o produto id {id_item}, parâmetros compatíveis e horários EXATOS encontrado.")

        return niveis_ocupados

    def ocupar_niveis_parcialmente_preenchidos(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int],
        vaporizacao: Optional[int],
        velocidade: Optional[int],
        quantidade: int,
        unidades_por_nivel: Optional[int],
        gramas_por_nivel: Optional[int]
    ) -> bool:
        """
        🔄 Ocupa parcialmente níveis já utilizados pelo mesmo produto e parâmetros compatíveis.
        Complementa a ocupação até atingir a quantidade desejada.
        ✔️ CORREÇÃO: Agora funciona apenas com horários EXATOS (através do método corrigido).
        """
        capacidade_por_nivel = unidades_por_nivel or gramas_por_nivel
        tipo = "unidades" if unidades_por_nivel else "gramas"

        # Lista de tuplas (nivel, quantidade_ocupada) - agora só retorna horários EXATOS
        ocupados = self.retornar_espaco_ocupado_por_nivel(
            id_item=id_item,
            inicio=inicio,
            fim=fim,
            temperatura=temperatura,
            vaporizacao=vaporizacao,
            velocidade=velocidade
        )

        restante = quantidade
        for nivel, ocupado in ocupados:
            capacidade_restante = capacidade_por_nivel - ocupado
            if capacidade_restante <= 0:
                continue

            a_ocupar = min(capacidade_restante, restante)

            self._registrar_ocupacao_nivel(
                nivel=nivel,
                quantidade_alocada=a_ocupar,
                inicio=inicio,
                fim=fim,
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                temperatura=temperatura,
                vaporizacao=vaporizacao,
                velocidade=velocidade
            )

            logger.info(
                f"♻️ Forno {self.nome} | Nível {nivel} complementado com {a_ocupar} {tipo} "
                f"(total após complemento: {ocupado + a_ocupar}/{capacidade_por_nivel}) - HORÁRIOS EXATOS"
            )

            restante -= a_ocupar

            if restante <= 0:
                return True

        if restante > 0:
            logger.info(
                f"ℹ️ Forno {self.nome} não conseguiu ocupar parcialmente toda a quantidade desejada através de compartilhamento. "
                f"Restante: {restante} {tipo} (será alocado em níveis livres se disponíveis)"
            )
        return restante <= 0

    def ocupar_niveis_exatos_com_capacidade_total(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int],
        vaporizacao: Optional[int],
        velocidade: Optional[int],
        quantidade: int,
        niveis_necessarios: int,
        unidades_por_nivel: Optional[int],
        gramas_por_nivel: Optional[int]
    ) -> bool:
        """
        🎯 Ocupa exatamente o número de níveis necessários com capacidade total.
        Usado quando não há produto igual já alocado - ocupação em níveis completamente livres.
        """
        capacidade_por_nivel = unidades_por_nivel or gramas_por_nivel
        tipo = "unidades" if unidades_por_nivel else "gramas"
        
        if capacidade_por_nivel is None:
            logger.error(f"❌ Capacidade por nível não definida para o forno {self.nome}")
            return False

        # 🔍 Encontrar níveis consecutivos livres e compatíveis
        niveis_selecionados = []
        
        for nivel_inicial in range(self.qtd_niveis - niveis_necessarios + 1):
            # Verificar se todos os níveis necessários estão livres e compatíveis
            todos_livres = True
            
            for offset in range(niveis_necessarios):
                nivel_atual = nivel_inicial + offset
                
                # Verificar se está ocupado
                if self._nivel_esta_ocupado(nivel_atual, inicio, fim):
                    todos_livres = False
                    break
                    
                # Verificar compatibilidade de parâmetros
                if not self._nivel_aceita_parametros(nivel_atual, inicio, fim, temperatura, vaporizacao, velocidade):
                    todos_livres = False
                    break
            
            if todos_livres:
                niveis_selecionados = [nivel_inicial + i for i in range(niveis_necessarios)]
                break
        
        if not niveis_selecionados:
            logger.warning(f"❌ Não foi possível encontrar {niveis_necessarios} níveis consecutivos livres no forno {self.nome}")
            return False

        # 📦 Distribuir a quantidade pelos níveis selecionados
        quantidade_restante = quantidade
        
        for i, nivel in enumerate(niveis_selecionados):
            # Para os primeiros níveis, usar capacidade total
            # Para o último nível, usar o que sobrar
            if i == len(niveis_selecionados) - 1:
                # Último nível - usar o que restou
                quantidade_nivel = quantidade_restante
            else:
                # Nível intermediário - usar capacidade total
                quantidade_nivel = min(capacidade_por_nivel, quantidade_restante)
            
            self._registrar_ocupacao_nivel(
                nivel=nivel,
                quantidade_alocada=quantidade_nivel,
                inicio=inicio,
                fim=fim,
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                temperatura=temperatura,
                vaporizacao=vaporizacao,
                velocidade=velocidade
            )
            
            quantidade_restante -= quantidade_nivel
            
            logger.info(
                f"🎯 Forno {self.nome} | Nível {nivel} ocupado com {quantidade_nivel} {tipo} "
                f"(capacidade: {capacidade_por_nivel})"
            )
        
        if quantidade_restante > 0:
            logger.warning(f"⚠️ Sobrou {quantidade_restante} {tipo} não alocados no forno {self.nome}")
            return False
            
        logger.info(
            f"✅ Forno {self.nome} | Ocupação completa: {quantidade} {tipo} em {len(niveis_selecionados)} níveis"
        )
        return True

    def _nivel_aceita_parametros(
        self,
        nivel: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int],
        vaporizacao: Optional[int],
        velocidade: Optional[int]
    ) -> bool:
        temp_ok = all(registro[4] == temperatura for registro in self.registro_temperatura
                    if registro[3] == nivel and not (fim <= registro[5] or inicio >= registro[6]))
        vap_ok = all(registro[4] == vaporizacao for registro in self.registro_vaporizacao
                    if self.tem_vaporizacao and registro[3] == nivel and not (fim <= registro[5] or inicio >= registro[6]))
        vel_ok = all(registro[4] == velocidade for registro in self.registro_velocidade
                    if self.tem_velocidade and registro[3] == nivel and not (fim <= registro[5] or inicio >= registro[6]))
        return temp_ok and vap_ok and vel_ok

    def _registrar_ocupacao_nivel(
        self,
        nivel: int,
        quantidade_alocada: float,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        temperatura: Optional[int],
        vaporizacao: Optional[int],
        velocidade: Optional[int],
    ):
        """
        🔐 Registra ocupação do nível com todos os parâmetros.
        """
        # Ocupação principal do nível
        self.niveis_ocupacoes[nivel].append(
            (
                id_ordem,
                id_pedido,
                id_atividade,
                id_item,
                quantidade_alocada,
                inicio,
                fim,
            )
        )

        # Parâmetros de cocção por nível
        self.registro_temperatura.append(
            (
                id_ordem,
                id_pedido,
                id_atividade,
                nivel,
                temperatura,
                inicio,
                fim
            )
        )

        if self.tem_vaporizacao:
            self.registro_vaporizacao.append(
                (
                    id_ordem,
                    id_pedido,
                    id_atividade,
                    nivel,
                    vaporizacao,
                    inicio,
                    fim
                )
            )

        if self.tem_velocidade:
            self.registro_velocidade.append(
                (
                    id_ordem,
                    id_pedido,
                    id_atividade,
                    nivel,
                    velocidade,
                    inicio,
                    fim
                )
            )
            
    def _nivel_esta_ocupado(self, nivel: int, inicio: datetime, fim: datetime) -> bool:
        """
        🔐 Verifica se o nível está ocupado em algum intervalo que colida com o fornecido.
        """
        for ocupacao in self.niveis_ocupacoes[nivel]:
            if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):
                logger.debug(
                    f"🚫 Nível {nivel} ocupado de {ocupacao[5].strftime('%H:%M')} até {ocupacao[6].strftime('%H:%M')}, "
                    f"colide com tentativa de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}"
                )
                return True
        return False

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """
        🔓 Libera todas as ocupações e registros da atividade especificada,
        respeitando id_ordem, id_pedido e id_atividade.
        """
        total_removidas = 0

        # 🔁 Remove ocupações dos níveis
        for idx in range(len(self.niveis_ocupacoes)):
            antes = len(self.niveis_ocupacoes[idx])
            self.niveis_ocupacoes[idx] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[idx]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
            ]
            total_removidas += antes - len(self.niveis_ocupacoes[idx])

        # 🧼 Remove registros de parâmetros
        self.registro_temperatura = [
            r for r in self.registro_temperatura
            if not (r[0] == id_ordem and r[1] == id_pedido and r[2] == id_atividade)
        ]
        self.registro_vaporizacao = [
            r for r in self.registro_vaporizacao
            if not (r[0] == id_ordem and r[1] == id_pedido and r[2] == id_atividade)
        ]
        self.registro_velocidade = [
            r for r in self.registro_velocidade
            if not (r[0] == id_ordem and r[1] == id_pedido and r[2] == id_atividade)
        ]

        # 🪵 Log
        if total_removidas > 0:
            logger.info(
                f"🔓 Liberadas {total_removidas} ocupações do Forno {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação do Forno {self.nome} foi encontrada para liberação "
                f"(Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem})."
            )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """
        🔓 Libera todas as ocupações e registros vinculados ao pedido e ordem informados.
        Remove todas as atividades associadas a esse par (id_ordem, id_pedido).
        """
        total_removidas = 0

        # 🔁 Remove ocupações por nível
        for idx in range(len(self.niveis_ocupacoes)):
            antes = len(self.niveis_ocupacoes[idx])
            self.niveis_ocupacoes[idx] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[idx]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
            ]
            total_removidas += antes - len(self.niveis_ocupacoes[idx])

        # 🧼 Remove registros de parâmetros
        self.registro_temperatura = [
            r for r in self.registro_temperatura
            if not (r[0] == id_ordem and r[1] == id_pedido)
        ]
        self.registro_vaporizacao = [
            r for r in self.registro_vaporizacao
            if not (r[0] == id_ordem and r[1] == id_pedido)
        ]
        self.registro_velocidade = [
            r for r in self.registro_velocidade
            if not (r[0] == id_ordem and r[1] == id_pedido)
        ]

        # 🪵 Log
        if total_removidas > 0:
            logger.info(
                f"🔓 Liberadas {total_removidas} ocupações do Forno {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação do Forno {self.nome} foi encontrada para liberação "
                f"(Pedido {id_pedido}, Ordem {id_ordem})."
            )

    def liberar_por_ordem(self, id_ordem: int):
        """
        🔓 Libera todas as ocupações e registros relacionados à ordem informada,
        incluindo todos os pedidos e atividades vinculados a ela.
        """
        total_removidas = 0

        # 🔁 Remove ocupações dos níveis
        for idx in range(len(self.niveis_ocupacoes)):
            antes = len(self.niveis_ocupacoes[idx])
            self.niveis_ocupacoes[idx] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[idx]
                if ocupacao[0] != id_ordem
            ]
            total_removidas += antes - len(self.niveis_ocupacoes[idx])

        # 🧼 Remove registros
        self.registro_temperatura = [r for r in self.registro_temperatura if r[0] != id_ordem]
        self.registro_vaporizacao = [r for r in self.registro_vaporizacao if r[0] != id_ordem]
        self.registro_velocidade = [r for r in self.registro_velocidade if r[0] != id_ordem]

        # 🪵 Log
        if total_removidas > 0:
            logger.info(
                f"🔓 Liberadas {total_removidas} ocupações do Forno {self.nome} para Ordem {id_ordem}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação do Forno {self.nome} foi encontrada para liberação (Ordem {id_ordem})."
            )