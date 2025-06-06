import os
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividade_base import Atividade
from parser.leitor_json_subprodutos import buscar_dados_por_id_atividade
from factory import fabrica_equipamentos
import unicodedata

logger = setup_logger('Atividade_Generica_Composta')


class AtividadeModular(Atividade):
    def __init__(self, id, id_atividade: int, quantidade_produto: int, *args, **kwargs):
        dados_atividade = buscar_dados_por_id_atividade(id_atividade)[1]
        nomes_equipamentos = dados_atividade.get("equipamentos_elegiveis", [])
        equipamentos_elegiveis = [getattr(fabrica_equipamentos, nome) for nome in nomes_equipamentos]

        super().__init__(
            id=id,
            id_atividade=id_atividade,
            tipos_profissionais_permitidos=[],
            quantidade_funcionarios=0,
            equipamentos_elegiveis=equipamentos_elegiveis,
            id_produto_gerado=None,
            quantidade_produto=quantidade_produto
        )

        self.fips_equipamentos = {
            getattr(fabrica_equipamentos, nome): fip
            for nome, fip in dados_atividade.get("fips_equipamentos", {}).items()
        }

        self.configuracoes_equipamentos = dados_atividade.get("configuracoes_equipamentos")

        self._quantidade_por_tipo_equipamento = {
            TipoEquipamento[nome]: qtd
            for nome, qtd in dados_atividade.get("tipo_equipamento", {}).items()
        }

        self.duracao = self._consultar_duracao_por_faixas(dados_atividade)
    
    def calcular_duracao(self):
        return super().calcular_duracao()

    def _consultar_duracao_por_faixas(self, dados_atividade) -> timedelta:
        faixas = dados_atividade.get("faixas", [])
        qtd = self.quantidade_produto

        for faixa in faixas:
            min_qtd = faixa.get("quantidade_min")
            max_qtd = faixa.get("quantidade_max")

            if min_qtd is None or max_qtd is None:
                raise ValueError(f"❌ Faixa de quantidade inválida ou incompleta: {faixa}")

            if min_qtd <= qtd <= max_qtd:
                h, m, s = map(int, faixa["duracao"].split(":"))
                return timedelta(hours=h, minutes=m, seconds=s)

        raise ValueError(f"❌ Nenhuma faixa compatível com a quantidade {qtd}g.")

    def _criar_gestores_por_tipo(self) -> dict[TipoEquipamento, object]:
        gestores_por_tipo = {}

        for tipo_equipamento, _ in self._quantidade_por_tipo_equipamento.items():
            if tipo_equipamento not in MAPA_GESTOR:
                raise ValueError(f"❌ Gestor não definido para o tipo de equipamento: {tipo_equipamento.name}")

            gestor_cls = MAPA_GESTOR[tipo_equipamento]

            equipamentos_filtrados = [
                equipamento for equipamento in self.equipamentos_elegiveis
                if equipamento.tipo_equipamento == tipo_equipamento
            ]

            if not equipamentos_filtrados:
                raise ValueError(f"⚠️ Nenhum equipamento do tipo {tipo_equipamento.name} associado à atividade.")

            gestores_por_tipo[tipo_equipamento] = gestor_cls(equipamentos_filtrados)

        return gestores_por_tipo

    def tentar_alocar_e_iniciar(self, inicio_jornada: datetime, fim_jornada: datetime) -> bool:
        horario_final = fim_jornada

        while horario_final - self.duracao >= inicio_jornada:
            horario_inicio = horario_final - self.duracao

            sucesso = True
            equipamentos_alocados = []
            ocupacoes_efetuadas = []
            horario_fim_etapa = horario_final  # ⏱️ Etapa final começa aqui

            # 🔁 Equipamentos em ordem reversa (último → primeiro)
            for tipo_eqp, _ in reversed(list(self._quantidade_por_tipo_equipamento.items())):
                equipamentos = [eqp for eqp in self.equipamentos_elegiveis if eqp.tipo_equipamento == tipo_eqp]

                if not equipamentos:
                    logger.warning(f"⚠️ Nenhum equipamento do tipo {tipo_eqp} disponível.")
                    sucesso = False
                    break

                classe_gestor = MAPA_GESTOR.get(tipo_eqp)
                if not classe_gestor:
                    logger.warning(f"⚠️ Nenhum gestor configurado para tipo {tipo_eqp}")
                    sucesso = False
                    break

                gestor = classe_gestor(equipamentos)
                metodo_alocacao = self._resolver_metodo_alocacao(tipo_eqp)

                equipamento_exemplo = equipamentos[0]
                nome_normalizado = self._normalizar_nome(equipamento_exemplo.nome)
                config = self.configuracoes_equipamentos.get(nome_normalizado, {})

                try:
                    resultado = metodo_alocacao(
                        gestor=gestor,
                        inicio=horario_fim_etapa - self.duracao,
                        fim=horario_fim_etapa,
                        **config
                    )

                    if not resultado[0]:
                        sucesso = False
                        break

                    equipamentos_alocados.append(resultado)
                    if hasattr(resultado[1], "ultimos_ids_ocupacao"):
                        for ocupacao_id in resultado[1].ultimos_ids_ocupacao:
                            ocupacoes_efetuadas.append((resultado[1], ocupacao_id))

                    # 🔁 Atualiza o fim da próxima etapa para o início desta
                    horario_fim_etapa = resultado[2]

                except Exception as e:
                    logger.error(f"❌ Erro ao alocar {tipo_eqp}: {e}")
                    sucesso = False
                    break

            if sucesso:
                self._registrar_sucesso(equipamentos_alocados, horario_fim_etapa, horario_final)
                return True

            # ↩️ Rollback de qualquer ocupação parcial
            for equipamento in [e[1] for e in equipamentos_alocados]:
                try:
                    if hasattr(equipamento, "liberar_por_atividade"):
                        equipamento.liberar_por_atividade(self.id)
                        logger.info(f"↩️ Rollback: desalocada atividade {self.id} em {equipamento.nome}")
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao desalocar atividade {self.id} de {equipamento.nome}: {e}")

            horario_final -= timedelta(minutes=1)

        logger.warning(f"⚠️ Falha na alocação da atividade {self.id_atividade}")
        return False



    def _registrar_sucesso(self, equipamentos_alocados, inicio: datetime, fim: datetime):
        self.equipamentos_selecionados = [dados[1] for dados in equipamentos_alocados]
        self.equipamento_alocado = self.equipamentos_selecionados
        self.inicio_real = inicio
        self.fim_real = fim
        self.alocada = True

        logger.info("✅ Atividade alocada com sucesso!")
        for sucesso, equipamento, i, f in equipamentos_alocados:
            if i and f:
                logger.info(f"🔧 {equipamento.nome} alocado de {i.strftime('%H:%M')} até {f.strftime('%H:%M')}")
            else:
                logger.info(f"🔧 {equipamento.nome} alocado (sem janela de tempo)")

    def _resolver_metodo_alocacao(self, tipo_equipamento):
        if tipo_equipamento == TipoEquipamento.REFRIGERACAO_CONGELAMENTO:
            return self._alocar_camara
        elif tipo_equipamento == TipoEquipamento.BANCADAS:
            return self._alocar_bancada
        elif tipo_equipamento == TipoEquipamento.FOGOES:
            return self._alocar_fogao
        elif tipo_equipamento == TipoEquipamento.BATEDEIRAS:
            return self._alocar_batedeira
        elif tipo_equipamento == TipoEquipamento.BALANCAS:
            return self._alocar_balanca
        elif tipo_equipamento == TipoEquipamento.FORNOS:
            return self._alocar_forno
        elif tipo_equipamento == TipoEquipamento.MISTURADORAS:
            return self._alocar_misturadora
        elif tipo_equipamento == TipoEquipamento.MISTURADORAS_COM_COCCAO:
            return self._alocar_misturadora_com_coccao
        elif tipo_equipamento == TipoEquipamento.ARMARIOS_PARA_FERMENTACAO:
            return self._alocar_armario_fermentacao
        else:
            raise ValueError(f"❌ Nenhum método de alocação definido para {tipo_equipamento}")

    def _alocar_camara(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_bancada(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self)

    def _alocar_fogao(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_batedeira(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_balanca(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_forno(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_misturadora(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_misturadora_com_coccao(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_armario_fermentacao(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def mostrar_agendas_dos_gestores(self):
        try:
            gestores = self._criar_gestores_por_tipo()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível criar os gestores para mostrar agenda: {e}")
            return
        for tipo, gestor in gestores.items():
            if hasattr(gestor, "mostrar_agenda"):
                gestor.mostrar_agenda()
            else:
                logger.warning(f"⚠️ Gestor de {tipo.name} não possui método 'mostrar_agenda'.")
    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
