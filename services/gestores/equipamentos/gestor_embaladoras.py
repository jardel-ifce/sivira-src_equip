from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equipamentos.embaladora import Embaladora
from enums.equipamentos.tipo_embalagem import TipoEmbalagem
from utils.logs.logger_factory import setup_logger
import unicodedata

if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular

logger = setup_logger("GestorEmbaladoras")

class GestorEmbaladoras:
    """
    🏭 Gestor SIMPLIFICADO para controle de embaladoras.
    
    ✅ SEMPRE aceita alocações (sem validação de capacidade máxima)
    ✅ Ignora verificações de viabilidade
    ✅ Permite múltiplas alocações simultâneas
    ✅ Mantém apenas validação de capacidade mínima
    """

    def __init__(self, embaladoras: List[Embaladora]):
        self.embaladoras = embaladoras

    # ==========================================================
    # 🚀 SIMPLIFICADO: Sem verificações de viabilidade
    # ==========================================================
    def _verificar_viabilidade_quantidade(self, atividade: "AtividadeModular", quantidade_total: float,
                                        id_item: int, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        🟢 SIMPLIFICADO: Sempre retorna True (viável)
        """
        return True, "Sempre viável - sem restrições de capacidade máxima"

    # ==========================================================
    # 🔍 Métodos auxiliares
    # ==========================================================
    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """
        Extrai os IDs da atividade de forma consistente.
        Retorna: (id_ordem, id_pedido, id_atividade, id_item)
        """
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0) 
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item
        
    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Embaladora]:
        return sorted(
            self.embaladoras,
            key=lambda e: atividade.fips_equipamentos.get(e, 999)
        )
        
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _obter_capacidade_explicita_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        """
        🔍 Verifica se há um valor explícito de 'capacidade_gramas' no JSON da atividade
        """
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "embaladora" in chave_normalizada:
                    capacidade_gramas = conteudo.get("capacidade_gramas")
                    if capacidade_gramas is not None:
                        logger.info(
                            f"📦 JSON da atividade {atividade.id_atividade} define capacidade_gramas = {capacidade_gramas}g"
                        )
                        return capacidade_gramas
                        
            logger.debug(f"ℹ️ Nenhuma capacidade_gramas definida no JSON da atividade {atividade.id_atividade}.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar capacidade_gramas no JSON da atividade: {e}")
            return None

    def _normalizar_nome(self, nome: str) -> str:
        return nome.strip().lower().replace(" ", "_")

    # ==========================================================
    # 🎯 Alocação principal - SIMPLIFICADA
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        
        **kwargs
    ) -> Tuple[bool, Optional[List[Embaladora]], Optional[datetime], Optional[datetime]]:
        """
        🟢 VERSÃO SIMPLIFICADA: Sempre tenta alocar na primeira embaladora disponível.
        Sem verificações de capacidade máxima ou viabilidade.
        """

        # Extrai IDs da atividade
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)

        duracao = atividade.duracao
        horario_final = fim
        embaladoras_ordenadas = self._ordenar_por_fip(atividade)

        peso_json = self._obter_capacidade_explicita_do_json(atividade)
        
        # Determina quantidade final (JSON tem prioridade)
        if peso_json is not None:
            quantidade_final = peso_json
            logger.debug(
                f"📊 Usando capacidade_gramas do JSON para atividade {id_atividade}: "
                f"{quantidade_final}g (original: {quantidade_produto}g)"
            )
        else:
            quantidade_final = float(quantidade_produto)

        logger.info(f"🎯 Iniciando alocação SIMPLIFICADA: {quantidade_final}g do item {id_item}")

        # Tenta alocar no horário desejado
        while horario_final - duracao >= inicio:
            horario_inicio = horario_final - duracao

            # 🟢 SIMPLIFICADO: Tenta alocar na primeira embaladora
            for embaladora in embaladoras_ordenadas:
                # Obtém configuração de tipos de embalagem
                nome_eqp = self._normalizar_nome(embaladora.nome)
                config_emb = atividade.configuracoes_equipamentos.get(nome_eqp, {})
                tipos_embalagem_strs = config_emb.get("tipo_embalagem", [])

                try:
                    tipos_embalagem = [TipoEmbalagem[t.upper()] for t in tipos_embalagem_strs]
                    if not tipos_embalagem:
                        continue
                except KeyError as e:
                    logger.warning(f"⚠️ Tipo de embalagem inválido para {embaladora.nome}: {e}")
                    continue

                # Verifica apenas capacidade mínima
                if quantidade_final < embaladora.capacidade_gramas_min:
                    logger.debug(
                        f"❌ {embaladora.nome}: Quantidade {quantidade_final}g abaixo do mínimo "
                        f"({embaladora.capacidade_gramas_min}g)"
                    )
                    continue

                # 🟢 Tenta ocupar (sempre aceita se >= mínimo)
                sucesso = embaladora.ocupar(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade=quantidade_final,
                    lista_tipo_embalagem=tipos_embalagem,
                    inicio=horario_inicio,
                    fim=horario_final
                )

                if sucesso:
                    atividade.equipamento_alocado = embaladora
                    atividade.equipamentos_selecionados = [embaladora]
                    atividade.inicio_planejado = horario_inicio
                    atividade.fim_planejado = horario_final
                    atividade.alocada = True
                    
                    logger.info(
                        f"✅ Alocação bem-sucedida: {quantidade_final}g na {embaladora.nome} "
                        f"de {horario_inicio.strftime('%H:%M')} até {horario_final.strftime('%H:%M')}"
                    )
                    return True, [embaladora], horario_inicio, horario_final

            # Se não conseguiu alocar, tenta horário anterior
            horario_final -= timedelta(minutes=1)

        # Se chegou aqui, não conseguiu alocar
        logger.warning(
            f"❌ Não foi possível alocar {quantidade_final}g do item {id_item} "
            f"para atividade {id_atividade} na janela disponível"
        )
        return False, None, None, None

    # ==========================================================
    # 🔄 Alocação múltipla - SIMPLIFICADA
    # ==========================================================
    def alocar_multiplas_embaladoras(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_total: float,
        max_embaladoras: Optional[int] = None,
        **kwargs
    ) -> Tuple[bool, List[Tuple[Embaladora, float]], Optional[datetime], Optional[datetime]]:
        """
        🟢 SIMPLIFICADO: Distribui igualmente entre embaladoras disponíveis
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        duracao = atividade.duracao
        horario_final = fim
        
        embaladoras_ordenadas = self._ordenar_por_fip(atividade)
        
        # Limita número de embaladoras se especificado
        if max_embaladoras:
            embaladoras_ordenadas = embaladoras_ordenadas[:max_embaladoras]

        logger.info(f"🎯 Iniciando alocação múltipla SIMPLIFICADA: {quantidade_total}g do item {id_item}")

        while horario_final - duracao >= inicio:
            horario_inicio = horario_final - duracao
            
            # Filtra embaladoras que atendem capacidade mínima
            embaladoras_validas = []
            for embaladora in embaladoras_ordenadas:
                # Obtém configuração
                nome_eqp = self._normalizar_nome(embaladora.nome)
                config_emb = atividade.configuracoes_equipamentos.get(nome_eqp, {})
                tipos_embalagem_strs = config_emb.get("tipo_embalagem", [])

                try:
                    tipos_embalagem = [TipoEmbalagem[t.upper()] for t in tipos_embalagem_strs]
                    if tipos_embalagem:
                        embaladoras_validas.append((embaladora, tipos_embalagem))
                except KeyError:
                    continue

            if not embaladoras_validas:
                horario_final -= timedelta(minutes=1)
                continue

            # 🟢 Distribui igualmente entre embaladoras
            num_embaladoras = len(embaladoras_validas)
            quantidade_por_embaladora = quantidade_total / num_embaladoras
            
            # Ajusta para respeitar capacidade mínima
            todas_atendem_minimo = all(
                quantidade_por_embaladora >= emb.capacidade_gramas_min 
                for emb, _ in embaladoras_validas
            )
            
            if not todas_atendem_minimo:
                # Tenta usar menos embaladoras
                horario_final -= timedelta(minutes=1)
                continue

            # Tenta alocar em todas
            alocacoes_realizadas = []
            sucesso_total = True
            
            for i, (embaladora, tipos_embalagem) in enumerate(embaladoras_validas):
                # Última embaladora pega o resto (para evitar erros de arredondamento)
                if i == len(embaladoras_validas) - 1:
                    qtd_embaladora = quantidade_total - sum(qtd for _, qtd in alocacoes_realizadas)
                else:
                    qtd_embaladora = quantidade_por_embaladora
                
                sucesso = embaladora.ocupar(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade=qtd_embaladora,
                    lista_tipo_embalagem=tipos_embalagem,
                    inicio=horario_inicio,
                    fim=horario_final
                )
                
                if not sucesso:
                    # Rollback das alocações já feitas
                    for emb_rollback, _ in alocacoes_realizadas:
                        emb_rollback.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
                    sucesso_total = False
                    break
                
                alocacoes_realizadas.append((embaladora, qtd_embaladora))
            
            if sucesso_total:
                # Atualizar atividade
                atividade.equipamentos_selecionados = [emb for emb, _ in alocacoes_realizadas]
                atividade.equipamento_alocado = alocacoes_realizadas[0][0]
                atividade.alocada = True
                atividade.inicio_planejado = horario_inicio
                atividade.fim_planejado = horario_final
                
                logger.info(
                    f"✅ Alocação múltipla bem-sucedida em {len(alocacoes_realizadas)} embaladoras:"
                )
                for emb, qtd in alocacoes_realizadas:
                    logger.info(f"   🔹 {emb.nome}: {qtd:.2f}g")
                
                return True, alocacoes_realizadas, horario_inicio, horario_final
            
            horario_final -= timedelta(minutes=1)

        logger.warning(
            f"❌ Não foi possível alocar {quantidade_total}g do item {id_item} "
            f"em múltiplas embaladoras para atividade {id_atividade}"
        )
        return False, [], None, None

    # ==========================================================
    # 🔓 Liberação (métodos mantidos)
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for emb in self.embaladoras:
            emb.liberar_por_atividade(id_ordem, id_pedido, id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for emb in self.embaladoras:
            emb.liberar_por_pedido(id_ordem, id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for emb in self.embaladoras:
            emb.liberar_por_ordem(id_ordem)

    def liberar_por_item(self, id_item: int):
        """
        🔓 Libera todas as ocupações de um item específico em todas as embaladoras.
        """
        for embaladora in self.embaladoras:
            embaladora.liberar_por_item(id_item)
    
    def liberar_ocupacoes_anteriores_a(self, horario_atual: datetime):
        for emb in self.embaladoras:
            emb.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for embaladora in self.embaladoras:
            embaladora.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Embaladoras (VERSÃO SIMPLIFICADA)")
        logger.info("✅ Sem restrições de capacidade máxima")
        logger.info("✅ Aceita múltiplas alocações simultâneas")
        logger.info("==============================================")
        for emb in self.embaladoras:
            emb.mostrar_agenda()

    # ==========================================================
    # 📊 Status e Análise
    # ==========================================================
    def obter_status_embaladoras(self) -> dict:
        """
        Retorna o status atual de todas as embaladoras.
        """
        status = {}
        for embaladora in self.embaladoras:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'tipos_embalagem': [emb.name for emb in oc[5]],
                    'inicio': oc[6].strftime('%H:%M'),
                    'fim': oc[7].strftime('%H:%M')
                }
                for oc in embaladora.ocupacoes
            ]
            
            status[embaladora.nome] = {
                'capacidade_minima': embaladora.capacidade_gramas_min,
                'capacidade_maxima': 'ILIMITADA',
                'sempre_disponivel': True,
                'tipos_embalagem_suportados': [emb.name for emb in embaladora.lista_tipo_embalagem],
                'total_ocupacoes': len(embaladora.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def diagnosticar_sistema(self) -> dict:
        """
        🔧 Diagnóstico completo do sistema de embaladoras.
        """
        total_ocupacoes = sum(len(e.ocupacoes) for e in self.embaladoras)
        
        return {
            "total_embaladoras": len(self.embaladoras),
            "total_ocupacoes_ativas": total_ocupacoes,
            "configuracao": "SIMPLIFICADA",
            "restricoes_capacidade_maxima": False,
            "verificacoes_viabilidade": False,
            "sempre_disponivel": True,
            "aceita_multiplas_alocacoes": True,
            "versao": "3.0 - Totalmente Simplificada",
            "timestamp": datetime.now().isoformat()
        }