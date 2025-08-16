import json
from enums.producao.politica_producao import PoliticaProducao
from utils.logs.logger_factory import setup_logger

logger = setup_logger("DebugConversaoEnum")

def debug_conversao_politica_producao(caminho_json: str):
    """
    🔍 Script para debugar a conversão de política de produção do JSON.
    """
    print("🔍 DEBUGGING CONVERSÃO DE POLÍTICA DE PRODUÇÃO")
    print("=" * 60)
    
    try:
        # 1. Carregar JSON bruto
        with open(caminho_json, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        print(f"📂 Arquivo carregado: {len(dados)} itens")
        
        # 2. Verificar item específico do creme de queijo
        creme_queijo = None
        for item in dados:
            if item.get("id_item") == 2010:
                creme_queijo = item
                break
        
        if not creme_queijo:
            print("❌ Item creme_de_queijo (ID 2010) não encontrado!")
            return
        
        print("\n🧀 ITEM CREME DE QUEIJO (ID 2010):")
        print("-" * 40)
        print(f"📝 Nome: {creme_queijo.get('nome')}")
        print(f"📝 Descrição: {creme_queijo.get('descricao')}")
        print(f"📝 Política (string do JSON): '{creme_queijo.get('politica_producao')}'")
        print(f"📝 Estoque atual: {creme_queijo.get('estoque_atual')}")
        print(f"📝 Tipo do valor: {type(creme_queijo.get('politica_producao'))}")
        
        # 3. Testar conversão para ENUM
        politica_string = creme_queijo.get('politica_producao')
        
        print(f"\n🔄 TESTANDO CONVERSÃO:")
        print("-" * 40)
        
        try:
            # Teste direto da conversão
            politica_enum = PoliticaProducao[politica_string]
            print(f"✅ Conversão bem-sucedida: {politica_string} → {politica_enum}")
            print(f"📊 Valor do ENUM: {politica_enum.value}")
            print(f"📊 Tipo do ENUM: {type(politica_enum)}")
            
            # Verificar se é realmente ESTOCADO
            if politica_enum == PoliticaProducao.ESTOCADO:
                print("✅ CONFIRMADO: Política é ESTOCADO")
            else:
                print(f"⚠️ ATENÇÃO: Política não é ESTOCADO, é {politica_enum.value}")
                
        except KeyError as e:
            print(f"❌ ERRO na conversão: {e}")
            print("💡 Possíveis valores válidos:")
            for politica in PoliticaProducao:
                print(f"   - {politica.name} (valor: {politica.value})")
        
        # 4. Verificar todos os valores de política no arquivo
        print(f"\n📊 TODAS AS POLÍTICAS NO ARQUIVO:")
        print("-" * 40)
        
        politicas_encontradas = {}
        for item in dados:
            politica = item.get('politica_producao')
            if politica in politicas_encontradas:
                politicas_encontradas[politica] += 1
            else:
                politicas_encontradas[politica] = 1
        
        for politica, count in politicas_encontradas.items():
            print(f"📈 '{politica}': {count} itens")
            
            # Testar se cada uma é válida
            try:
                enum_val = PoliticaProducao[politica]
                print(f"   ✅ Válida: {enum_val.value}")
            except KeyError:
                print(f"   ❌ INVÁLIDA: não existe no ENUM")
        
        # 5. Verificar valores possíveis do ENUM
        print(f"\n🎯 VALORES VÁLIDOS DO ENUM PoliticaProducao:")
        print("-" * 40)
        for politica in PoliticaProducao:
            print(f"📌 {politica.name} → valor: '{politica.value}'")
        
        # 6. Teste específico de verificação de estoque
        print(f"\n🧪 SIMULAÇÃO DE VERIFICAÇÃO DE ESTOQUE:")
        print("-" * 40)
        
        if creme_queijo:
            politica_string = creme_queijo.get('politica_producao')
            estoque_atual = creme_queijo.get('estoque_atual', 0)
            
            print(f"📦 Estoque atual: {estoque_atual}")
            print(f"🏷️ Política: {politica_string}")
            
            # Simular a lógica do código
            if politica_string == "SOB_DEMANDA":
                print("🔄 Resultado: SEMPRE PRODUZIR (política SOB_DEMANDA)")
            elif politica_string == "ESTOCADO":
                if estoque_atual >= 4600:  # Quantidade aproximada necessária
                    print("✅ Resultado: NÃO PRODUZIR (estoque suficiente)")
                else:
                    print("❌ Resultado: PRODUZIR (estoque insuficiente)")
            else:
                print(f"⚠️ Política desconhecida: {politica_string}")
    
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()

# Função para uso direto
if __name__ == "__main__":
    debug_conversao_politica_producao("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip/data/almoxarifado/itens_almoxarifado.json")