# 🛠️ Guia de Implementação de Parsers e Restauradores

## 📋 Checklist para Implementar um Novo Tipo

Para cada tipo de equipamento, siga estes passos:

### ☑️ Fase 1: Análise do Log
1. [ ] Abrir log detalhado em `logs/equipamentos_detalhados/`
2. [ ] Localizar seção do equipamento
3. [ ] Identificar formato das ocupações
4. [ ] Anotar campos específicos do tipo

### ☑️ Fase 2: Implementar Parser
1. [ ] Abrir arquivo stub em `utils/recuperacao/parsers/`
2. [ ] Implementar método `parse()`
3. [ ] Usar métodos herdados de `ParserBase`
4. [ ] Retornar `List[OcupacaoDTO]` com `detalhes` preenchidos

### ☑️ Fase 3: Implementar Restaurador
1. [ ] Abrir arquivo stub em `utils/recuperacao/restauradores/`
2. [ ] Implementar método `restaurar()`
3. [ ] Identificar estrutura interna do equipamento
4. [ ] Aplicar ocupações na estrutura correta

### ☑️ Fase 4: Testar
1. [ ] Executar `testar_recuperacao_basico.py`
2. [ ] Verificar ocupações extraídas
3. [ ] Validar formato dos dados
4. [ ] Testar restauração em objeto real

---

## 📝 Exemplo Completo: Câmara Refrigerada

### 1. Análise do Log

```
🔧 Câmara Refrigerada 1 (CamaraRefrigerada)
============================================================

📋 OCUPAÇÕES REGISTRADAS:
----------------------------------------
==============================================
📅 Agenda da Câmara Refrigerada 1
📊 Numeração dos níveis físicos: 1 a 25
📊 Numeração das caixas: 1 a 200
📏 Dimensões: 625 níveis de tela totais | 200 caixas totais
🌡️ Faixa de temperatura: 0°C a 4°C
==============================================
🔹 Nível 1, Tela 1:
   🗂️ Ordem 1 | Pedido 2 | Atividade 10723 | Item 1072 | 10.00 unidades | 05:36 → 06:36 | Temp: 4°C
```

**Campos identificados:**
- Nível/Tela ou Caixa
- IDs padrão (ordem, pedido, atividade, item)
- Quantidade (unidades)
- Horários (início → fim)
- Temperatura (°C)

### 2. Implementar Parser

```python
"""
Parser para Câmara Refrigerada
==============================
"""

from typing import List
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO


class ParserCamaraRefrigerada(ParserBase):
    """Parser especializado para Câmaras Refrigeradas"""

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        self.limpar_erros()
        ocupacoes = []

        linhas = log_content.split('\n')
        nivel_atual = None
        caixa_atual = None
        data_base = datetime.now()

        for linha in linhas:
            linha = linha.strip()

            # Detectar nível
            if '🔹 Nível' in linha:
                nivel_atual = self.extrair_numero_nivel(linha)
                caixa_atual = None
                continue

            # Detectar caixa
            if '📦 Caixa' in linha:
                caixa_atual = self.extrair_numero_caixa(linha)
                nivel_atual = None
                continue

            # Detectar ocupação
            if '🗂️' in linha:
                ocupacao = self._extrair_ocupacao_camara(
                    linha,
                    nivel_atual,
                    caixa_atual,
                    nome_equipamento,
                    data_base
                )
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_ocupacao_camara(
        self,
        linha: str,
        nivel: int,
        caixa: int,
        nome_equipamento: str,
        data_base: datetime
    ) -> OcupacaoDTO:
        """Extrai ocupação de câmara"""
        try:
            # IDs
            ids = self.extrair_ids_ocupacao(linha)
            if not ids:
                return None
            id_ordem, id_pedido, id_atividade, id_item = ids

            # Horários
            horarios = self.extrair_horarios(linha)
            if not horarios:
                return None
            inicio_str, fim_str = horarios

            inicio = self.converter_horario_para_datetime(inicio_str, data_base=data_base)
            fim = self.converter_horario_para_datetime(fim_str, data_base=data_base)
            fim = self.ajustar_data_se_atravessar_meia_noite(inicio, fim)

            # Temperatura
            temperatura = self.extrair_temperatura(linha)

            # Quantidade
            quantidade = self.extrair_quantidade_unidades(linha)

            return OcupacaoDTO(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                inicio=inicio,
                fim=fim,
                nome_equipamento=nome_equipamento,
                tipo_equipamento="CamaraRefrigerada",
                detalhes={
                    "nivel_numero": nivel,
                    "caixa_numero": caixa,
                    "temperatura": temperatura,
                    "quantidade": quantidade
                }
            )

        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de câmara: {e}")
            return None
```

### 3. Implementar Restaurador

```python
"""
Restaurador para Câmara Refrigerada
===================================
"""

from typing import List
from .restaurador_base import RestauradorBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO
from models.equipamentos.camara_refrigerada import CamaraRefrigerada


class RestauradorCamaraRefrigerada(RestauradorBase):
    """Restaurador especializado para Câmaras Refrigeradas"""

    def restaurar(self, ocupacoes: List[OcupacaoDTO], equipamento: CamaraRefrigerada) -> bool:
        self.limpar_erros()

        # Validações
        if not self.validar_tipo_equipamento(equipamento, CamaraRefrigerada):
            return False

        if not self.validar_ocupacoes_nao_vazias(ocupacoes):
            return False

        self.log_restauracao_inicio(equipamento, len(ocupacoes))

        total_restauradas = 0

        for ocupacao in ocupacoes:
            try:
                nivel_numero = ocupacao.obter_detalhe("nivel_numero")
                caixa_numero = ocupacao.obter_detalhe("caixa_numero")
                temperatura = ocupacao.obter_detalhe("temperatura")
                quantidade = ocupacao.obter_detalhe("quantidade")

                # Determinar se é nível ou caixa
                if nivel_numero is not None:
                    # Ocupação em nível
                    nivel_index = nivel_numero - 1

                    if not self.validar_indice_valido(
                        nivel_index,
                        equipamento.qtd_niveis_total,
                        "níveis de câmara"
                    ):
                        continue

                    # Tupla para nível: (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
                    tupla_ocupacao = (
                        ocupacao.id_ordem,
                        ocupacao.id_pedido,
                        ocupacao.id_atividade,
                        ocupacao.id_item,
                        quantidade if quantidade else 0.0,
                        ocupacao.inicio,
                        ocupacao.fim
                    )

                    equipamento.niveis_ocupacoes[nivel_index].append(tupla_ocupacao)

                elif caixa_numero is not None:
                    # Ocupação em caixa
                    caixa_index = caixa_numero - 1

                    if not self.validar_indice_valido(
                        caixa_index,
                        equipamento.qtd_caixas,
                        "caixas de câmara"
                    ):
                        continue

                    # Tupla para caixa: (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
                    tupla_ocupacao = (
                        ocupacao.id_ordem,
                        ocupacao.id_pedido,
                        ocupacao.id_atividade,
                        ocupacao.id_item,
                        quantidade if quantidade else 0.0,
                        ocupacao.inicio,
                        ocupacao.fim
                    )

                    equipamento.caixas_ocupacoes[caixa_index].append(tupla_ocupacao)

                # Adicionar intervalo de temperatura
                if temperatura is not None:
                    intervalo_temp = (temperatura, ocupacao.inicio, ocupacao.fim)
                    if intervalo_temp not in equipamento.intervalos_temperatura:
                        equipamento.intervalos_temperatura.append(intervalo_temp)

                total_restauradas += 1

            except Exception as e:
                erro = f"Erro ao restaurar ocupação {ocupacao}: {e}"
                self.adicionar_erro(erro)
                continue

        if total_restauradas > 0:
            self.log_restauracao_sucesso(equipamento, total_restauradas)
            return True
        else:
            self.log_restauracao_erro(equipamento, "Nenhuma ocupação foi restaurada")
            return False
```

### 4. Testar

```bash
python3 testar_recuperacao_basico.py
```

---

## 🎯 Prioridade de Implementação Sugerida

### Alta Prioridade (equipamentos mais usados):
1. **Câmara Refrigerada** - Níveis e caixas com temperatura
2. **Freezer** - Similar a câmara
3. **Masseira** - Ocupações simples com velocidade/mistura
4. **Fogão** - Bocas com chamas e pressões

### Média Prioridade:
5. **Balança** - Pesagens simples
6. **Armário Esqueleto** - Níveis/andares
7. **Armário Fermentador** - Níveis/andares
8. **Divisora de Massas** - Ocupações simples

### Baixa Prioridade:
9. **Batedeira Industrial** - Similar a masseira
10. **Batedeira Planetária** - Similar a masseira
11. **HotMix** - Janelas com capacidades
12. **Fritadeira** - Frações
13. **Modeladora de Pães** - Ocupações simples
14. **Modeladora de Salgados** - Ocupações simples
15. **Embaladora** - Múltiplas alocações
16. **Forno** - Similar a fogão (quando usado)

---

## 📚 Referências Úteis

### Métodos de ParserBase disponíveis:
- `extrair_ids_ocupacao(linha)` - Extrai ordem, pedido, atividade, item
- `extrair_horarios(linha)` - Extrai início e fim
- `extrair_quantidade_gramas(linha)` - Extrai quantidade em gramas
- `extrair_quantidade_unidades(linha)` - Extrai quantidade em unidades
- `extrair_numero_fracao(linha)` - Extrai número de fração
- `extrair_numero_boca(linha)` - Extrai número de boca
- `extrair_numero_nivel(linha)` - Extrai número de nível
- `extrair_numero_caixa(linha)` - Extrai número de caixa
- `extrair_temperatura(linha)` - Extrai temperatura
- `converter_horario_para_datetime()` - Converte string para datetime
- `ajustar_data_se_atravessar_meia_noite()` - Ajusta data se necessário

### Estruturas internas dos equipamentos:
Consultar arquivos em `models/equipamentos/` para ver:
- Atributos disponíveis
- Estruturas de ocupação
- Formato das tuplas

---

## ⚠️ Cuidados Importantes

1. **Índices**: Converter números de 1-indexed para 0-indexed
   ```python
   fracao_index = fracao_numero - 1  # Fração 1 = índice 0
   ```

2. **Validação**: Sempre validar índices antes de usar
   ```python
   if not self.validar_indice_valido(indice, tamanho_max, "estrutura"):
       continue
   ```

3. **Erros**: Adicionar erros descritivos
   ```python
   self.adicionar_erro(f"Contexto específico: {detalhe_erro}")
   ```

4. **Formato de tuplas**: Verificar formato exato no modelo do equipamento
   ```python
   # Exemplo: Bancada espera 6 elementos
   tupla = (id_ordem, id_pedido, id_atividade, id_item, inicio, fim)
   ```

5. **Testes**: Testar com log real antes de considerar completo

---

## 💡 Dicas

- **Copie o padrão**: Use `parser_bancada.py` e `restaurador_bancada.py` como base
- **Leia o log**: Entenda o formato antes de começar a programar
- **Teste incrementalmente**: Implemente, teste, ajuste, repita
- **Use print()**: Durante desenvolvimento, adicione prints para debug
- **Consulte o modelo**: Sempre verifique a estrutura interna do equipamento

---

## 📞 Suporte

Para dúvidas sobre:
- **Formato do log**: Consultar `logs/equipamentos_detalhados/`
- **Estrutura do equipamento**: Consultar `models/equipamentos/`
- **Exemplo funcional**: Consultar `parser_bancada.py` e `restaurador_bancada.py`
- **Documentação geral**: Consultar `RECUPERACAO_ESTADO.md`
