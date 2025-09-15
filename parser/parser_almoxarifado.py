import json
from typing import List, Optional, Dict
from datetime import datetime, date
from enums.producao.tipo_item import TipoItem
from enums.producao.politica_producao import PoliticaProducao
from enums.producao.unidade_medida import UnidadeMedida
from models.almoxarifado.item_almoxarifado import ItemAlmoxarifado
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from utils.logs.logger_factory import setup_logger

logger = setup_logger("ParserAlmoxarifado")


class ParserAlmoxarifado:
    """
    ✅ PARSER COMPLETO para carregar e gerenciar itens do almoxarifado.
    Combina funcionalidades de carregamento, verificação e criação do gestor.
    ✅ CORRIGIDO: Permite override de política de produção para testes.
    """
    
    def __init__(self, caminho_json: str):
        self.caminho_json = caminho_json
        self.itens_carregados: List[ItemAlmoxarifado] = []
        self.almoxarifado: Optional[Almoxarifado] = None
        self.gestor: Optional[GestorAlmoxarifado] = None
        self._overrides_politica: Dict[int, PoliticaProducao] = {}
        
    def carregar_itens_do_json(self) -> List[ItemAlmoxarifado]:
        """
        ✅ Carrega itens do JSON com validação completa.
        """
        logger.info(f"📂 Carregando itens do almoxarifado de: {self.caminho_json}")
        
        try:
            with open(self.caminho_json, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            logger.info(f"📊 Encontrados {len(dados)} itens no JSON")
            
            itens = []
            itens_com_problema = []
            
            for i, item_data in enumerate(dados):
                try:
                    item = self._criar_item_almoxarifado(item_data)
                    itens.append(item)
                    
                    logger.debug(
                        f"✅ Item {i+1}: {item.descricao} "
                        f"(ID: {item.id_item}, Política: {item.politica_producao.value}, "
                        f"Estoque: {item.estoque_atual})"
                    )
                    
                except Exception as e:
                    itens_com_problema.append((i+1, item_data.get('id_item', 'N/A'), str(e)))
                    logger.error(f"❌ Erro ao processar item {i+1}: {e}")
            
            # Relatório de carregamento
            logger.info(
                f"📋 Carregamento concluído: "
                f"✅ {len(itens)} itens carregados com sucesso, "
                f"❌ {len(itens_com_problema)} itens com problema"
            )
            
            if itens_com_problema:
                logger.warning("⚠️ Itens com problema:")
                for linha, id_item, erro in itens_com_problema:
                    logger.warning(f"   Linha {linha}, ID {id_item}: {erro}")
            
            self.itens_carregados = itens
            return itens
            
        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {self.caminho_json}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro inesperado no carregamento: {e}")
            raise
    
    def _criar_item_almoxarifado(self, item_data: dict) -> ItemAlmoxarifado:
        """
        ✅ Cria um item do almoxarifado a partir dos dados do JSON.
        """
        # Extrair ficha técnica se existir
        ficha_tecnica_id = None
        if "ficha_tecnica" in item_data and item_data["ficha_tecnica"]:
            ficha_tecnica_id = item_data["ficha_tecnica"].get("id_ficha_tecnica")

        # ✅ NOVA FUNCIONALIDADE: Aplicar override de política se existir
        id_item = item_data["id_item"]
        politica_original = PoliticaProducao[item_data["politica_producao"]]
        politica_final = self._overrides_politica.get(id_item, politica_original)
        
        if id_item in self._overrides_politica:
            logger.info(
                f"🔄 Override aplicado para item {id_item}: "
                f"{politica_original.value} → {politica_final.value}"
            )

        item = ItemAlmoxarifado(
            id_item=id_item,
            nome=item_data["nome"],
            descricao=item_data["descricao"],
            tipo_item=TipoItem[item_data["tipo_item"]],
            peso=item_data["peso"],
            unidade_medida=UnidadeMedida[item_data["unidade_medida"]],
            estoque_min=item_data["estoque_min"],
            estoque_max=item_data["estoque_max"],
            estoque_atual=item_data.get("estoque_atual", item_data["estoque_min"]),
            politica_producao=politica_final,  # ✅ Usar política com override
            ficha_tecnica=ficha_tecnica_id,
            consumo_diario_estimado=item_data.get("consumo_diario_estimado", 0),
            reabastecimento_previsto_em=item_data.get("reabastecimento_previsto_em"),
            reservas_futuras=item_data.get("reservas_futuras", [])
        )
        
        return item
    
    def criar_almoxarifado(self) -> Almoxarifado:
        """
        ✅ Cria instância do almoxarifado com os itens carregados.
        """
        if not self.itens_carregados:
            logger.warning("⚠️ Nenhum item carregado. Executando carregamento primeiro...")
            self.carregar_itens_do_json()
        
        self.almoxarifado = Almoxarifado()
        
        # Adicionar todos os itens ao almoxarifado
        for item in self.itens_carregados:
            self.almoxarifado.adicionar_item(item)
        
        logger.info(
            f"✅ Almoxarifado criado com {len(self.itens_carregados)} itens"
        )
        
        return self.almoxarifado
    
    def criar_gestor(self) -> GestorAlmoxarifado:
        """
        ✅ Cria instância do gestor do almoxarifado.
        """
        if not self.almoxarifado:
            logger.info("🔄 Almoxarifado não existe. Criando...")
            self.criar_almoxarifado()
        
        self.gestor = GestorAlmoxarifado(self.almoxarifado, self)
        
        logger.info("✅ Gestor do almoxarifado criado com sucesso")
        
        return self.gestor
    
    # =============================================================================
    #                    FUNCIONALIDADES PARA TESTES
    # =============================================================================
    
    def definir_politica_item(self, id_item: int, nova_politica: PoliticaProducao):
        """
        ✅ NOVO: Define override de política para um item específico.
        Útil para testes onde queremos simular diferentes políticas.
        """
        self._overrides_politica[id_item] = nova_politica
        
        logger.info(
            f"🔧 Override de política definido para item {id_item}: {nova_politica.value}"
        )
        
        # Se item já foi carregado, aplicar mudança
        if self.itens_carregados:
            for item in self.itens_carregados:
                if item.id_item == id_item:
                    politica_anterior = item.politica_producao
                    item.politica_producao = nova_politica
                    logger.info(
                        f"✅ Política do item {id_item} atualizada: "
                        f"{politica_anterior.value} → {nova_politica.value}"
                    )
                    break
    
    def definir_estoque_item(self, id_item: int, novo_estoque: float):
        """
        ✅ NOVO: Define estoque específico para um item.
        Útil para testes de diferentes cenários de estoque.
        """
        # Aplicar mudança nos itens carregados
        item_encontrado = False
        for item in self.itens_carregados:
            if item.id_item == id_item:
                estoque_anterior = item.estoque_atual
                item.estoque_atual = novo_estoque
                logger.info(
                    f"📦 Estoque do item {id_item} ({item.descricao}) atualizado: "
                    f"{estoque_anterior} → {novo_estoque}"
                )
                item_encontrado = True
                break
        
        if not item_encontrado:
            logger.warning(f"⚠️ Item {id_item} não encontrado para atualizar estoque")
    
    def simular_cenario_teste(
        self, 
        id_item: int, 
        politica: PoliticaProducao, 
        estoque: float
    ):
        """
        ✅ NOVO: Método conveniente para simular cenários de teste.
        """
        logger.info(
            f"🧪 Simulando cenário de teste para item {id_item}: "
            f"Política={politica.value}, Estoque={estoque}"
        )
        
        self.definir_politica_item(id_item, politica)
        self.definir_estoque_item(id_item, estoque)
    
    # =============================================================================
    #                         VALIDAÇÃO E VERIFICAÇÃO
    # =============================================================================
    
    def verificar_json_valido(self) -> List[str]:
        """
        ✅ Verifica se o JSON está bem formado e com campos obrigatórios.
        """
        erros = []
        
        try:
            with open(self.caminho_json, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            campos_obrigatorios = [
                "id_item", "nome", "descricao", "tipo_item", 
                "politica_producao", "peso", "unidade_medida",
                "estoque_min", "estoque_max"
            ]
            
            for i, item in enumerate(dados):
                for campo in campos_obrigatorios:
                    if campo not in item:
                        erros.append(f"Item {i+1}: Campo obrigatório '{campo}' ausente")
                
                # Validar enums
                try:
                    TipoItem[item.get("tipo_item", "")]
                except KeyError:
                    erros.append(f"Item {i+1}: tipo_item inválido: {item.get('tipo_item')}")
                
                try:
                    PoliticaProducao[item.get("politica_producao", "")]
                except KeyError:
                    erros.append(f"Item {i+1}: politica_producao inválida: {item.get('politica_producao')}")
                
                try:
                    UnidadeMedida[item.get("unidade_medida", "")]
                except KeyError:
                    erros.append(f"Item {i+1}: unidade_medida inválida: {item.get('unidade_medida')}")
            
        except Exception as e:
            erros.append(f"Erro ao ler arquivo: {e}")
        
        if erros:
            logger.error(f"❌ Encontrados {len(erros)} erros de validação:")
            for erro in erros:
                logger.error(f"   - {erro}")
        else:
            logger.info("✅ JSON válido - todos os campos obrigatórios presentes")
        
        return erros
    
    def gerar_relatorio_itens(self) -> Dict:
        """
        ✅ Gera relatório detalhado dos itens carregados.
        """
        if not self.itens_carregados:
            return {"erro": "Nenhum item carregado"}
        
        # Estatísticas gerais
        total_itens = len(self.itens_carregados)
        por_tipo = {}
        por_politica = {}
        itens_criticos = []
        
        for item in self.itens_carregados:
            # Contar por tipo
            tipo = item.tipo_item.value
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
            
            # Contar por política
            politica = item.politica_producao.value
            por_politica[politica] = por_politica.get(politica, 0) + 1
            
            # Identificar críticos
            if item.esta_abaixo_do_minimo():
                itens_criticos.append({
                    "id": item.id_item,
                    "nome": item.descricao,
                    "estoque_atual": item.estoque_atual,
                    "estoque_min": item.estoque_min
                })
        
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "arquivo_origem": self.caminho_json,
            "total_itens": total_itens,
            "distribuicao_por_tipo": por_tipo,
            "distribuicao_por_politica": por_politica,
            "itens_criticos": len(itens_criticos),
            "detalhes_itens_criticos": itens_criticos,
            "overrides_aplicados": len(self._overrides_politica),
            "detalhes_overrides": {
                str(id_item): politica.value 
                for id_item, politica in self._overrides_politica.items()
            }
        }
        
        logger.info(f"📊 Relatório gerado: {total_itens} itens, {len(itens_criticos)} críticos")
        
        return relatorio
    
    # =============================================================================
    #                            UTILITÁRIOS
    # =============================================================================
    
    def buscar_item_por_id(self, id_item: int) -> Optional[ItemAlmoxarifado]:
        """
        ✅ Busca um item específico por ID.
        """
        for item in self.itens_carregados:
            if item.id_item == id_item:
                return item
        return None
    
    def listar_itens_por_politica(self, politica: PoliticaProducao) -> List[ItemAlmoxarifado]:
        """
        ✅ Lista itens filtrados por política de produção.
        """
        return [
            item for item in self.itens_carregados 
            if item.politica_producao == politica
        ]
    
    def resetar_overrides(self):
        """
        ✅ Remove todos os overrides de política aplicados.
        """
        overrides_removidos = len(self._overrides_politica)
        self._overrides_politica.clear()
        
        logger.info(f"🔄 {overrides_removidos} overrides de política removidos")
    
    def salvar_itens_modificados(self, caminho_saida: Optional[str] = None):
        """
        ✅ Salva os itens modificados de volta para JSON.
        """
        if not self.itens_carregados:
            logger.warning("⚠️ Nenhum item para salvar")
            return
        
        caminho_final = caminho_saida or self.caminho_json
        
        dados_saida = []
        for item in self.itens_carregados:
            item_dict = {
                "id_item": item.id_item,
                "nome": item.nome,
                "descricao": item.descricao,
                "tipo_item": item.tipo_item.value,
                "politica_producao": item.politica_producao.value,
                "peso": item.peso,
                "unidade_medida": item.unidade_medida.value,
                "estoque_min": item.estoque_min,
                "estoque_max": item.estoque_max,
                "estoque_atual": item.estoque_atual,
                "consumo_diario_estimado": item.consumo_diario_estimado,
                "reabastecimento_previsto_em": item.reabastecimento_previsto_em.strftime('%Y-%m-%d') if item.reabastecimento_previsto_em else None,
                "reservas_futuras": [
                    {
                        "data": r["data"].strftime('%Y-%m-%d'),
                        "quantidade_reservada": r["quantidade"],
                        "id_ordem": r.get("id_ordem", 0),
                        "id_pedido": r.get("id_pedido", 0),
                        "id_atividade": r.get("id_atividade")
                    } for r in item.reservas_futuras
                ]
            }
            
            if item.ficha_tecnica_id:
                item_dict["ficha_tecnica"] = {"id_ficha_tecnica": item.ficha_tecnica_id}
            
            dados_saida.append(item_dict)
        
        with open(caminho_final, "w", encoding="utf-8") as f:
            json.dump(dados_saida, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 {len(dados_saida)} itens salvos em: {caminho_final}")
    
    def __repr__(self):
        status = f"{len(self.itens_carregados)} itens carregados" if self.itens_carregados else "vazio"
        overrides = f", {len(self._overrides_politica)} overrides" if self._overrides_politica else ""
        return f"<ParserAlmoxarifado: {status}{overrides}>"


# =============================================================================
#                    FUNÇÕES DE CONVENIÊNCIA (Compatibilidade)
# =============================================================================

def carregar_itens_almoxarifado(caminho_json: str) -> List[ItemAlmoxarifado]:
    """
    ✅ Função de compatibilidade com o código existente.
    """
    parser = ParserAlmoxarifado(caminho_json)
    return parser.carregar_itens_do_json()


def criar_gestor_almoxarifado_completo(caminho_json: str) -> GestorAlmoxarifado:
    """
    ✅ NOVA: Função conveniente para criar gestor completo em uma linha.
    """
    parser = ParserAlmoxarifado(caminho_json)
    parser.carregar_itens_do_json()
    return parser.criar_gestor()


def teste_cenario_creme_queijo(caminho_json: str, estoque_creme: float) -> GestorAlmoxarifado:
    """
    ✅ NOVA: Função específica para testar cenários com creme de queijo.
    """
    parser = ParserAlmoxarifado(caminho_json)
    parser.carregar_itens_do_json()
    
    # Configurar creme de queijo como ESTOCADO para teste
    parser.simular_cenario_teste(
        id_item=2010,  # creme_de_queijo
        politica=PoliticaProducao.ESTOCADO,
        estoque=estoque_creme
    )
    
    return parser.criar_gestor()