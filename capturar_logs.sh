#!/bin/bash
# Script para capturar logs do sistema de produção
# Salva tudo em arquivo com timestamp

# Criar nome do arquivo com timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs_sistema_${TIMESTAMP}.txt"

echo "🔍 Capturando logs do sistema de produção..."
echo "📝 Arquivo: $LOG_FILE"
echo "⏱️  Timestamp: $(date)"
echo ""

# Executar o sistema e capturar TODA a saída
echo "🚀 Iniciando sistema..."
echo "📋 Pressione Ctrl+C para parar a captura"
echo ""

# Capturar stdout e stderr
python3 main_menu.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "✅ Logs salvos em: $LOG_FILE"
echo "📊 Tamanho do arquivo: $(du -h "$LOG_FILE" | cut -f1)"
echo "📋 Linhas capturadas: $(wc -l < "$LOG_FILE")"

# Criar versão filtrada automaticamente
FILTERED_FILE="logs_filtrados_${TIMESTAMP}.txt"
echo ""
echo "🔍 Criando versão filtrada..."

# Filtrar apenas linhas importantes
grep -E "(🔄 Executando pedido|Fase [0-9]+|Pedidos atendidos|Taxa de atendimento|Executados|Falhas|Tempo máximo de espera|já possui.*do produto|já alocado no nível|ALOCAÇÃO FALHOU|Rollback concluído|Atividade atual|Atividade sucessora|Atraso detectado|Máximo permitido|Intervalo tentado|ERROR|WARNING)" "$LOG_FILE" > "$FILTERED_FILE"

echo "✅ Versão filtrada salva em: $FILTERED_FILE"
echo "📊 Linhas filtradas: $(wc -l < "$FILTERED_FILE")"

# Mostrar estatísticas rápidas
EXEC_COUNT=$(grep -c "🔄 Executando pedido" "$FILTERED_FILE" 2>/dev/null || echo "0")
FALHAS_COUNT=$(grep -c "ALOCAÇÃO FALHOU\|já possui.*do produto" "$FILTERED_FILE" 2>/dev/null || echo "0")

echo ""
echo "📊 ESTATÍSTICAS RÁPIDAS:"
echo "   🔄 Execuções de pedido: $EXEC_COUNT"
echo "   ❌ Falhas de alocação: $FALHAS_COUNT"

if [ "$EXEC_COUNT" -gt 1 ]; then
    echo "   ⚠️  ATENÇÃO: Múltiplas execuções detectadas!"
fi

echo ""
echo "📁 Arquivos gerados:"
echo "   📄 Completo: $LOG_FILE"
echo "   🔍 Filtrado: $FILTERED_FILE"