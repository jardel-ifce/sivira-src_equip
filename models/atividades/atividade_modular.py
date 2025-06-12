import os
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_item import TipoItem
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividade_base import Atividade
from parser.carregador_json_atividades import buscar_dados_por_id_atividade
from factory import fabrica_equipamentos
import unicodedata
from datetime import datetime, timedelta

logger = setup_logger('Atividade_Modular')


class AtividadeModular(Atividade):
    def __init__(self, id, id_atividade: int, tipo_item: TipoItem, quantidade_produto: int, *args, **kwargs):
        self.ordem_id = kwargs.get("ordem_id")

        dados_atividade = kwargs.get("dados")
        if not dados_atividade:
            dados_gerais, dados_atividade = buscar_dados_por_id_atividade(id_atividade, tipo_item)
            self.nome_atividade = dados_gerais.get("nome_atividade", f"Atividade {id_atividade}")
            self.nome_item = dados_gerais.get("nome_item", "item_desconhecido")
        else:
            self.nome_atividade = f"Atividade {id_atividade}"
            self.nome_item = "item_desconhecido"

        nomes_equipamentos = dados_atividade.get("equipamentos_elegiveis", [])
        equipamentos_elegiveis = [getattr(fabrica_equipamentos, nome) for nome in nomes_equipamentos]
        self.tipo_item = tipo_item

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

        self.configuracoes_equipamentos = dados_atividade.get("configuracoes_equipamentos", {})

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

    def tentar_alocar_e_iniciar(self, inicio_jornada: datetime, fim_jornada: datetime) -> bool:
        horario_final = fim_jornada

        while horario_final - self.duracao >= inicio_jornada:
            if self._tentar_alocar_na_janela(horario_final):
                return True
            horario_final -= timedelta(minutes=1)

        logger.error(f"❌ Não foi possível alocar a atividade {self.id_atividade} dentro da jornada.")
        return False

    def _tentar_alocar_na_janela(self, horario_final: datetime) -> bool:
        sucesso = True
        equipamentos_alocados = []
        horario_fim_etapa = horario_final

        print(f"🕒 Tentando alocar entre {horario_fim_etapa - self.duracao:%H:%M} e {horario_fim_etapa:%H:%M} (duração: {self.duracao})")

        for tipo_eqp, _ in reversed(list(self._quantidade_por_tipo_equipamento.items())):
            sucesso, resultado, horario_fim_etapa = self._tentar_alocar_tipo(tipo_eqp, horario_fim_etapa)

            if not sucesso:
                return False

            equipamentos_alocados.append(resultado)

        self._registrar_sucesso(equipamentos_alocados, horario_fim_etapa, horario_final)
        return True

    def _tentar_alocar_tipo(self, tipo_eqp, horario_fim_etapa):
        equipamentos = [eqp for eqp in self.equipamentos_elegiveis if eqp.tipo_equipamento == tipo_eqp]
        if not equipamentos:
            return False, None, horario_fim_etapa

        classe_gestor = MAPA_GESTOR.get(tipo_eqp)
        if not classe_gestor:
            return False, None, horario_fim_etapa

        gestor = classe_gestor(equipamentos)
        metodo_alocacao = self._resolver_metodo_alocacao(tipo_eqp)
        nome_normalizado = self._normalizar_nome(equipamentos[0].nome)
        config = self._carregar_configuracoes(nome_normalizado)

        inicio_previsto = self._calcular_inicio_previsto(horario_fim_etapa)
        print(f"🧮 Janela sugerida: início {inicio_previsto:%H:%M} — fim {horario_fim_etapa:%H:%M}")

        try:
            resultado = metodo_alocacao(
                gestor=gestor,
                inicio=inicio_previsto,
                fim=horario_fim_etapa,
                **config
            )
            if not resultado[0]:
                return False, None, horario_fim_etapa

            return True, resultado, min(horario_fim_etapa, resultado[2])

        except Exception as e:
            logger.error(f"❌ Erro ao alocar {tipo_eqp}: {e}")
            return False, None, horario_fim_etapa

    def _carregar_configuracoes(self, nome_normalizado):
        return self.configuracoes_equipamentos.get(nome_normalizado, {})

    def _calcular_inicio_previsto(self, horario_fim_etapa):
        inicio_previsto = horario_fim_etapa - self.duracao
        if self.duracao.total_seconds() > 0 and inicio_previsto == horario_fim_etapa:
            inicio_previsto -= timedelta(seconds=self.duracao.total_seconds())
        return inicio_previsto

    def _registrar_sucesso(self, equipamentos_alocados, inicio: datetime, fim: datetime, **kwargs):
        self.equipamento_alocado = [dados[1] for dados in equipamentos_alocados]
        self.inicio_real = inicio
        self.fim_real = fim
        self.alocada = True

        logger.info("✅ Atividade alocada com sucesso!")
        for _, equipamento, i, f in equipamentos_alocados:
            logger.info(f"🔧 {equipamento.nome} alocado de {i.strftime('%H:%M')} até {f.strftime('%H:%M')}")

        if self.ordem_id:
            os.makedirs("logs", exist_ok=True)
            caminho = f"logs/ordem_{self.ordem_id}.log"
            with open(caminho, "a", encoding="utf-8") as arq:
                for _, equipamento, inicio, fim in equipamentos_alocados:
                    linha = (
                        f"{self.ordem_id} | "
                        f"{self.id_atividade} | {self.nome_item} | {self.nome_atividade} | "
                        f"{equipamento.nome} | {inicio.strftime('%H:%M')} | {fim.strftime('%H:%M')}\n"
                    )
                    arq.write(linha)

    def _resolver_metodo_alocacao(self, tipo_equipamento):
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: self._alocar_camara,
            TipoEquipamento.BANCADAS: self._alocar_bancada,
            TipoEquipamento.FOGOES: self._alocar_fogao,
            TipoEquipamento.BATEDEIRAS: self._alocar_batedeira,
            TipoEquipamento.BALANCAS: self._alocar_balanca,
            TipoEquipamento.FORNOS: self._alocar_forno,
            TipoEquipamento.MISTURADORAS: self._alocar_misturadora,
            TipoEquipamento.MISTURADORAS_COM_COCCAO: self._alocar_misturadora_com_coccao,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: self._alocar_armario_fermentacao,
            TipoEquipamento.MODELADORAS: self._alocar_modeladora,
            TipoEquipamento.DIVISORAS_BOLEADORAS: self._alocar_divisora_boleadora,
        }.get(tipo_equipamento, lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError(f"❌ Nenhum método de alocação definido para {tipo_equipamento}")
        ))

    def _alocar_camara(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_bancada(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self)
    def _alocar_fogao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_batedeira(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_balanca(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_forno(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_misturadora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_misturadora_com_coccao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_armario_fermentacao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_modeladora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_divisora_boleadora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
