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
    ✉️ Gestor responsável pela alocação de Embaladoras.
    Utiliza backward scheduling com validação por tipo de embalagem e capacidade.
    """

    def __init__(self, embaladoras: List[Embaladora]):
        self.embaladoras = embaladoras
        
    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
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
        para alguma chave que contenha 'divisora' no nome. Se houver, retorna esse valor.
        """
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "embaladora" in chave_normalizada:
                    capacidade_gramas = conteudo.get("capacidade_gramas")
                    if capacidade_gramas is not None:
                        logger.info(
                            f"📦 JSON da atividade {atividade.id_atividade} define capacidade_gramas = {capacidade_gramas}g para o equipamento '{chave}'"
                        )
                        return capacidade_gramas
            logger.info(f"ℹ️ Nenhuma capacidade_gramas definida no JSON da atividade {atividade.id_atividade}.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar capacidade_gramas no JSON da atividade: {e}")
            return None

    def _normalizar_nome(self, nome: str) -> str:
        return nome.strip().lower().replace(" ", "_")
    
    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: float
    ) -> Tuple[bool, Optional[Embaladora], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final = fim
        embaladoras_ordenadas = self._ordenar_por_fip(atividade)

        peso_json = self._obter_capacidade_explicita_do_json(atividade)
        if peso_json is not None:
            quantidade_final = peso_json
        else:
            quantidade_final = quantidade_gramas
            
        while horario_final - duracao >= inicio:
            horario_inicio = horario_final - duracao

            for embaladora in embaladoras_ordenadas:
                nome_eqp = self._normalizar_nome(embaladora.nome)
                config_emb = atividade.configuracoes_equipamentos.get(nome_eqp, {})
                tipos_embalagem_strs = config_emb.get("tipo_embalagem", [])

                try:
                    tipos_embalagem = [TipoEmbalagem[t.upper()] for t in tipos_embalagem_strs]
                except KeyError as e:
                    logger.warning(f"⚠️ Tipo de embalagem inválido para {embaladora.nome}: {e}")
                    continue

                if not embaladora.validar_capacidade(quantidade_final):
                    continue

                sucesso = embaladora.ocupar(
                    ordem_id=atividade.ordem_id,
                    pedido_id=atividade.pedido_id,
                    atividade_id=atividade.id_atividade,
                    quantidade=quantidade_final,
                    inicio=horario_inicio,
                    fim=horario_final,
                    lista_tipo_embalagem=tipos_embalagem
                )

                if sucesso:
                    atividade.equipamento_alocado = embaladora
                    atividade.equipamentos_selecionados = [embaladora]
                    atividade.inicio_planejado = horario_inicio
                    atividade.fim_planejado = horario_final
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {atividade.id_atividade} alocada na embaladora {embaladora.nome} "
                        f"de {horario_inicio.strftime('%H:%M')} até {horario_final.strftime('%H:%M')}."
                    )
                    return True, embaladora, horario_inicio, horario_final

            horario_final -= timedelta(minutes=1)

        logger.warning(
            f"❌ Falha ao alocar atividade {atividade.id_atividade} em qualquer embaladora entre "
            f"{inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None
    # ==========================================================
    # 🔓 Liberação
    # ==========================================================

    def liberar_por_atividade(self, ordem_id: int, pedido_id: int, atividade: "AtividadeModular"):
        for emb in self.embaladoras:
            emb.liberar_por_atividade(ordem_id, pedido_id, atividade.id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for emb in self.embaladoras:
            emb.liberar_por_pedido(atividade.ordem_id, atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for emb in self.embaladoras:
            emb.liberar_por_ordem(atividade.ordem_id)
    
    def liberar_ocupacoes_anteriores_a(self, horario_atual: datetime):
        for emb in self.embaladoras:
            emb.liberar_ocupacoes_finalizadas(horario_atual)

    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Embaladoras")
        logger.info("==============================================")
        for emb in self.embaladoras:
            emb.mostrar_agenda()
