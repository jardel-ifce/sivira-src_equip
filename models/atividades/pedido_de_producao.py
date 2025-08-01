from typing import List, Optional, Dict, Union
from datetime import datetime
import os
from factory.fabrica_funcionarios import funcionarios_disponiveis
from models.funcionarios.funcionario import Funcionario
from models.atividades.atividade_modular import AtividadeModular
from parser.carregador_json_atividades import buscar_atividades_por_id_item, buscar_dados_por_id_produto_ou_subproduto
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from parser.carregador_json_tipos_profissionais import buscar_tipos_profissionais_por_id_item
from services.rollback.rollback import rollback_equipamentos, rollback_funcionarios
from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
from enums.producao.tipo_item import TipoItem
from utils.logs.logger_factory import setup_logger
from utils.logs.gerenciador_logs import registrar_erro_execucao_pedido, apagar_logs_por_pedido_e_ordem, salvar_erro_em_log
from datetime import timedelta
from services.gestor_comandas.gestor_comandas import gerar_comanda_reserva as gerar_comanda_reserva_modulo


logger = setup_logger("PedidoDeProducao")


class PedidoDeProducao:
    def __init__(
        self,
        id_ordem: int,
        id_pedido: int,
        id_produto: int,
        tipo_item: TipoItem,
        quantidade: int,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        todos_funcionarios: Optional[List[Funcionario]] = None
    ):
        # 🔢 Identificação
        self.id_ordem = id_ordem
        self.id_pedido = id_pedido
        self.id_produto = id_produto
        self.tipo_item = tipo_item
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
        self.equipamentos_alocados_no_pedido = []

    def montar_estrutura(self):
        _, dados_ficha = buscar_ficha_tecnica_por_id(self.id_produto, tipo_item=self.tipo_item)
        self.ficha_tecnica_modular = FichaTecnicaModular(
            dados_ficha_tecnica=dados_ficha,
            quantidade_requerida=self.quantidade
        )
        # ✅ CORREÇÃO: Usar todos os funcionários ou filtro abrangente
        self.funcionarios_elegiveis = self._filtrar_funcionarios_abrangente()
        
    def _filtrar_funcionarios_abrangente(self) -> List[Funcionario]:
        """Filtra funcionários considerando produto principal E subprodutos"""
        if not self.ficha_tecnica_modular:
            return self.todos_funcionarios
            
        tipos_necessarios = set()
        
        # Produto principal
        tipos_necessarios.update(buscar_tipos_profissionais_por_id_item(self.id_produto))
        
        # Subprodutos
        estimativas = self.ficha_tecnica_modular.calcular_quantidade_itens()
        for item_dict, _ in estimativas:
            if item_dict.get("tipo_item") == "SUBPRODUTO":
                sub_id = item_dict.get("id_ficha_tecnica") 
                if sub_id:
                    tipos_necessarios.update(
                        buscar_tipos_profissionais_por_id_item(sub_id)
                    )
        
        return [f for f in self.todos_funcionarios if f.tipo_profissional in tipos_necessarios]

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
            logger.info(f"🔄 Criando atividades para ID {ficha_modular.id_item} ({ficha_modular.tipo_item.name})")
            atividades = buscar_atividades_por_id_item(ficha_modular.id_item, ficha_modular.tipo_item)

            for dados_gerais, dados_atividade in atividades:
                atividade = AtividadeModular(
                    id_ordem=self.id_ordem,
                    id=len(self.atividades_modulares) + 1,
                    id_atividade=dados_atividade["id_atividade"],
                    tipo_item=ficha_modular.tipo_item,
                    quantidade=ficha_modular.quantidade_requerida,
                    id_pedido=self.id_pedido,
                    id_produto=self.id_produto,
                    funcionarios_elegiveis=self.funcionarios_elegiveis,
                    peso_unitario=ficha_modular.peso_unitario,
                )
                self.atividades_modulares.append(atividade)

            logger.info(f"✅ Total de atividades adicionadas: {len(atividades)}")

        except Exception as e:
            logger.warning(f"⚠️ Nenhuma atividade criada para ID {ficha_modular.id_item}: {e}")

        estimativas = ficha_modular.calcular_quantidade_itens()
        for item_dict, quantidade in estimativas:
            tipo = item_dict.get("tipo_item")
            id_ficha = item_dict.get("id_ficha_tecnica")

            if tipo == "SUBPRODUTO" and id_ficha:
                _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha, TipoItem.SUBPRODUTO)
                ficha_sub = FichaTecnicaModular(dados_ficha_sub, quantidade)
                self._criar_atividades_recursivas(ficha_sub)

    def executar_atividades_em_ordem(self):
        logger.info(f"🚀 Iniciando execução do pedido {self.id_pedido} com {len(self.atividades_modulares)} atividades")
        current_fim = self.fim_jornada
        inicio_prox_atividade = self.fim_jornada
        atividade_sucessora = None

        atividades_produto = sorted(
            [a for a in self.atividades_modulares if a.tipo_item == TipoItem.PRODUTO],
            key=lambda a: a.id_atividade,
            reverse=True
        )

        for at in atividades_produto:
            try:


                ok, inicio_atividade_atual, fim_atividade_atual, _, self.equipamentos_alocados = at.tentar_alocar_e_iniciar_equipamentos(
                    self.inicio_jornada, current_fim
                )
                print("📦 DEBUG - equipamentos retornados na alocação:")
                print(f"   - {self.equipamentos_alocados}")

                if atividade_sucessora:
                    tempo_max_espera = atividade_sucessora.tempo_maximo_de_espera
                    atraso = inicio_prox_atividade - fim_atividade_atual

                    print(f"[⏱️] Comparando com tempo máximo da atividade sucessora {atividade_sucessora.id_atividade}: {tempo_max_espera}")
                    print(f"Fim da atividade atual: {fim_atividade_atual.strftime('%H:%M:%S')}")
                    print(f"Início da próxima (já alocada): {inicio_prox_atividade.strftime('%H:%M:%S')}")
                    print(f"Tempo de atraso: {atraso}")

                    if atraso > tempo_max_espera:
                        raise RuntimeError(
                            f"Falha ao alocar atividade {at.id_atividade} {at.nome_atividade} - "
                            f"Excedeu o tempo máximo de espera para a próxima atividade {atividade_sucessora.nome_atividade} "
                            f"em: {atraso - tempo_max_espera}"
                        )

                inicio_prox_atividade = inicio_atividade_atual
                atividade_sucessora = at
                if not ok:
                    raise RuntimeError(f"Falha ao alocar atividade {at.nome_atividade} PRODUTO {at.id_atividade}")
                self.equipamentos_alocados_no_pedido.extend(self.equipamentos_alocados)
                current_fim = at.inicio_real

            except Exception as e:
                logger.warning(f"⚠️ Atividade PRODUTO {at.id_atividade} falhou: {e}")
                registrar_erro_execucao_pedido(self.id_ordem, self.id_pedido, e)
                apagar_logs_por_pedido_e_ordem(self.id_ordem, self.id_pedido)
                self._rollback_pedido()
                return

        atividades_sub = [a for a in self.atividades_modulares if a.tipo_item == TipoItem.SUBPRODUTO]
        atividade_sucessora = None
        inicio_prox_atividade = self.fim_jornada

        for at in atividades_sub:
            try:
                ok, inicio_atividade_atual, fim_atividade_atual, _, self.equipamentos_alocados = at.tentar_alocar_e_iniciar_equipamentos(
                    self.inicio_jornada, current_fim
                )

                if atividade_sucessora:
                    tempo_max_espera = atividade_sucessora.tempo_maximo_de_espera
                    atraso = inicio_prox_atividade - fim_atividade_atual

                    print(f"[⏱️] Comparando com tempo máximo da atividade sucessora {atividade_sucessora.id_atividade}: {tempo_max_espera}")
                    print(f"Fim da atividade atual: {fim_atividade_atual.strftime('%H:%M:%S')}")
                    print(f"Início da próxima (já alocada): {inicio_prox_atividade.strftime('%H:%M:%S')}")
                    print(f"Tempo de atraso: {atraso}")

                    if atraso > tempo_max_espera:
                        raise RuntimeError(
                            f"Falha ao alocar atividade SUBPRODUTO {at.id_atividade} - "
                            f"Excedeu o tempo máximo de espera para a próxima atividade {atividade_sucessora.nome_atividade} "
                            f"em: {atraso - tempo_max_espera}"
                        )

                inicio_prox_atividade = inicio_atividade_atual
                atividade_sucessora = at
                if not ok:
                    raise RuntimeError(f"Falha ao alocar atividade SUBPRODUTO {at.id_atividade}")
                current_fim = at.inicio_real

            except Exception as e:
                logger.warning(f"⚠️ Atividade SUBPRODUTO {at.id_atividade} falhou: {e}")
                salvar_erro_em_log(self.id_ordem, self.id_pedido, e)
                apagar_logs_por_pedido_e_ordem(self.id_ordem, self.id_pedido)
                self._rollback_pedido()
                return

        logger.info(f"✅ Concluída execução do pedido {self.id_pedido}")

    def _filtrar_funcionarios_por_item(self, id_item: int) -> List[Funcionario]:
        tipos_necessarios = buscar_tipos_profissionais_por_id_item(id_item)
        return [f for f in self.todos_funcionarios if f.tipo_profissional in tipos_necessarios]

    def rollback_pedido(self):
        rollback_funcionarios(funcionarios_alocados=self.funcionarios_elegiveis, id_ordem=self.id_ordem, id_pedido=self.id_pedido)
        rollback_equipamentos(equipamentos_alocados= self.equipamentos_alocados, id_ordem=self.id_ordem, id_pedido=self.id_pedido)
        
    def _rollback_pedido(self):
        logger.info(f"🔁 [PedidoDeProducao] Executando rollback do pedido {self.id_pedido} da ordem {self.id_ordem}")

        # Libera equipamentos de TODAS as atividades que foram alocados
        for atividade in self.atividades_modulares:
            rollback_equipamentos(
                equipamentos_alocados=atividade.equipamentos_selecionados,
                id_ordem=self.id_ordem,
                id_pedido=self.id_pedido
            )

        rollback_funcionarios(
            funcionarios_alocados=self.funcionarios_elegiveis,
            id_ordem=self.id_ordem,
            id_pedido=self.id_pedido
        )

        apagar_logs_por_pedido_e_ordem(self.id_ordem, self.id_pedido)


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
            raise RuntimeError(f"Pedido {self.id_pedido} não pode ser montada. Itens com estoque insuficiente.")

    def gerar_comanda_de_reserva(self, data_execucao: datetime, gestor_almoxarifado):
        """
        Gera a comanda de reserva baseada na ficha técnica e políticas de produção.
        A lógica completa está delegada ao módulo externo.
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada.")

        gerar_comanda_reserva_modulo(
            id_ordem=self.id_ordem,
            id_pedido=self.id_pedido,
            ficha=self.ficha_tecnica_modular,
            gestor=gestor_almoxarifado,
            data_execucao=data_execucao
        )
    
    