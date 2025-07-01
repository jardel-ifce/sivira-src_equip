from typing import List, Optional, Dict, Union
from datetime import datetime
import os
from factory.fabrica_funcionarios import funcionarios_disponiveis
from models.funcionarios.funcionario import Funcionario
from models.atividades.atividade_modular import AtividadeModular
from parser.carregador_json_atividades import buscar_atividades_por_id_item
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from parser.carregador_json_tipos_profissionais import buscar_tipos_profissionais_por_id_item
from services.rollback import rollback_equipamentos, rollback_funcionarios
from models.ficha_tecnica_modular import FichaTecnicaModular
from enums.tipo_item import TipoItem
from utils.logger_factory import setup_logger
from utils.gerenciador_logs import registrar_erro_execucao_pedido, apagar_logs_por_pedido_e_ordem
from datetime import timedelta
from modules.modulo_comandas import gerar_comanda_reserva as gerar_comanda_reserva_modulo


logger = setup_logger("PedidoDeProducao")


class PedidoDeProducao:
    def __init__(
        self,
        ordem_id: int,
        pedido_id: int,
        id_produto: int,
        quantidade: int,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        todos_funcionarios: Optional[List[Funcionario]] = None
    ):
        # 🔢 Identificação
        self.ordem_id = ordem_id
        self.pedido_id = pedido_id
        self.id_produto = id_produto
        self.quantidade = quantidade

        # ⏱️ Janela de produção
        self.inicio_jornada = inicio_jornada
        self.fim_jornada = fim_jornada

        # 👷 Funcionários
        self.todos_funcionarios = todos_funcionarios or []
        self.funcionarios_elegiveis: List[Funcionario] = []

        # 🧱 Estrutura técnica
        self.ficha_tecnica_modular = None
        self.atividades_modulares = []

        # 🛠️ Equipamentos
        self.equipamentos_alocados = []  

    def montar_estrutura(self):
        _, dados_ficha = buscar_ficha_tecnica_por_id(self.id_produto, TipoItem.PRODUTO)
        self.ficha_tecnica_modular = FichaTecnicaModular(
            dados_ficha_tecnica=dados_ficha,
            quantidade_requerida=self.quantidade
        )
        self.funcionarios_elegiveis = self._filtrar_funcionarios_por_item(self.id_produto)


    def criar_atividades_modulares_necessarias(self):
        """
        🛠️ Cria atividades com base na ficha técnica modular.
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada.")

        self.atividades_modulares = []
        self._criar_atividades_recursivas(self.ficha_tecnica_modular)

    def _criar_atividades_recursivas(self, ficha_modular: FichaTecnicaModular):
        try:
            atividades = buscar_atividades_por_id_item(ficha_modular.id_item, ficha_modular.tipo_item)
            for dados_gerais, dados_atividade in atividades:
                atividade = AtividadeModular(
                    ordem_id=self.ordem_id,
                    id=len(self.atividades_modulares) + 1,
                    id_atividade=dados_atividade["id_atividade"],
                    tipo_item=ficha_modular.tipo_item,
                    quantidade_produto=ficha_modular.quantidade_requerida,
                    pedido_id=self.pedido_id,
                    id_produto=self.id_produto,
                    funcionarios_elegiveis=self.funcionarios_elegiveis
                )
                self.atividades_modulares.append(atividade)
        except Exception:
            pass  # Insumo puro

        estimativas = ficha_modular.calcular_quantidade_itens()
        for item_dict, quantidade in estimativas:
            tipo = item_dict.get("tipo_item")
            id_ficha = item_dict.get("id_ficha_tecnica")

            if tipo == "SUBPRODUTO" and id_ficha:
                _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha, TipoItem.SUBPRODUTO)
                ficha_sub = FichaTecnicaModular(dados_ficha_sub, quantidade)
                self._criar_atividades_recursivas(ficha_sub)

    def executar_atividades_em_ordem(self):
        logger.info(f"🚀 Iniciando execução do pedido {self.pedido_id} com {len(self.atividades_modulares)} atividades")
        current_fim = self.fim_jornada
        inicio_prox_atividade = self.fim_jornada

        try:
            atividades_produto = sorted(
                [a for a in self.atividades_modulares if a.tipo_item == TipoItem.PRODUTO],
                key=lambda a: a.id_atividade,
                reverse=True
            )

            for at in atividades_produto:
                ok, inicio_atividade_atual, fim_atividade_atual, tempo_max_espera_atual, self.equipamentos_alocados = at.tentar_alocar_e_iniciar_equipamentos(self.inicio_jornada, current_fim)
                print(f"Inicio da prox atividade: {inicio_prox_atividade}")
                print(f"Fim da atividade atual: {fim_atividade_atual}")
                print(f"Tempo máximo de espera atual: {tempo_max_espera_atual}")
                print(f"Tempo de atraso: {inicio_prox_atividade - fim_atividade_atual}")
                      
                      
                if inicio_prox_atividade - fim_atividade_atual > tempo_max_espera_atual:
                    tempo_atraso = inicio_prox_atividade - fim_atividade_atual
                    raise RuntimeError(f"Falha ao alocar atividade {at.id_atividade} {at.nome_atividade} - Excedeu o tempo máximo de espera em: {tempo_atraso}")

                inicio_prox_atividade = inicio_atividade_atual
                if not ok:
                    raise RuntimeError(f"Falha ao alocar atividade {at.nome_atividade} PRODUTO {at.id_atividade}")
                current_fim = at.inicio_real

            atividades_sub = [a for a in self.atividades_modulares if a.tipo_item == TipoItem.SUBPRODUTO]

            for at in atividades_sub:
                ok, inicio_atividade_atual, fim_atividade_atual, tempo_max_espera_atual, self.equipamentos_alocados = at.tentar_alocar_e_iniciar_equipamentos(self.inicio_jornada, current_fim)
                print(f"Inicio da prox atividade: {inicio_prox_atividade}")
                print(f"Fim da atividade atual: {fim_atividade_atual}")
                print(f"Tempo máximo de espera atual: {tempo_max_espera_atual}")
                print(f"Tempo de atraso: {inicio_prox_atividade - fim_atividade_atual}")
                if inicio_prox_atividade - fim_atividade_atual > tempo_max_espera_atual:
                    tempo_atraso = inicio_prox_atividade - fim_atividade_atual
                    raise RuntimeError(f"Falha ao alocar atividade SUBPRODUTO {at.id_atividade} - Excedeu o tempo máximo de espera: {tempo_atraso}")

                inicio_prox_atividade = inicio_atividade_atual
                if not ok:
                    raise RuntimeError(f"Falha ao alocar atividade SUBPRODUTO {at.id_atividade}")

            #logger.info("pedido finalizada com sucesso.")

        except Exception as e:
                registrar_erro_execucao_pedido(self.ordem_id,self.pedido_id, e)
                apagar_logs_por_pedido_e_ordem(self.ordem_id, self.pedido_id)
                self.rollback_pedido()

    def _filtrar_funcionarios_por_item(self, id_item: int) -> List[Funcionario]:
        tipos_necessarios = buscar_tipos_profissionais_por_id_item(id_item)
        return [f for f in self.todos_funcionarios if f.tipo_profissional in tipos_necessarios]

    def rollback_pedido(self):
        rollback_funcionarios(funcionarios_alocados=self.funcionarios_elegiveis, ordem_id=self.ordem_id, pedido_id=self.pedido_id)
        rollback_equipamentos(equipamentos_alocados= self.equipamentos_alocados, ordem_id=self.ordem_id, pedido_id=self.pedido_id)
        
    def exibir_historico_de_funcionarios(self):
        for funcionario in funcionarios_disponiveis:
            funcionario.mostrar_agenda()

    def mostrar_estrutura(self):
            if self.ficha_tecnica_modular:
                self.ficha_tecnica_modular.mostrar_estrutura()


    # =============================================================================
    #                   Métodos de Controle de Almoxarifado
    # =============================================================================
    def verificar_disponibilidade_estoque(self, gestor_almoxarifado, data_execucao: datetime):
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada.")

        itens_insuficientes = []

        estimativas = self.ficha_tecnica_modular.calcular_quantidade_itens()
       # descricao = self.ficha_tecnica_modular.descricao
       # politica = self.ficha_tecnica_modular.politica_producao


        for item_dict, quantidade in estimativas:
            id_item = item_dict["id_item"]
            tipo_item = item_dict["tipo_item"]
            nome_item = item_dict["descricao"]
            politica = item_dict.get("politica_producao", "ESTOCADO")  # Fallback padrão


            logger.info(
                f"🧪 Verificando item '{nome_item}' (ID {id_item}) | Tipo: {tipo_item} "
                f"| Política de Produção: {politica} | Quantidade Necessária: {quantidade}"
            )

            if tipo_item in {"SUBPRODUTO", "PRODUTO"} and politica == "SOB_DEMANDA":
                continue

            if politica == "ESTOCADO":
                disponibilidade = gestor_almoxarifado.verificar_disponibilidade_projetada_para_data(
                    id_item=id_item,
                    data=data_execucao.date()
                )

                if disponibilidade < quantidade:
                    itens_insuficientes.append({
                        "id": id_item,
                        "descricao": nome_item,
                        "quantidade_necessaria": quantidade,
                        "disponivel": disponibilidade
                    })

        if itens_insuficientes:
            for item in itens_insuficientes:
                logger.error(
                    f"❌ Estoque insuficiente para o item '{item['descricao']}' (ID {item['id']}): "
                    f"Necessário {item['quantidade_necessaria']}, Disponível {item['disponivel']}"
                )
            raise RuntimeError(f"Pedido {self.pedido_id} não pode ser montada. Itens com estoque insuficiente.")

    def gerar_comanda_de_reserva(self, data_execucao: datetime, gestor_almoxarifado):
        """
        Gera a comanda de reserva baseada na ficha técnica e políticas de produção.
        A lógica completa está delegada ao módulo externo.
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada.")

        gerar_comanda_reserva_modulo(
            ordem_id=self.ordem_id,
            pedido_id=self.pedido_id,
            ficha=self.ficha_tecnica_modular,
            gestor=gestor_almoxarifado,
            data_execucao=data_execucao
        )
    
    