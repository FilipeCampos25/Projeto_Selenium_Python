#!/bin/bash
set -euo pipefail
DB_URL=${DATABASE_URL:-"postgresql://postgres:postgres@localhost:5432/projeto"}
echo "Running DB tests against $DB_URL"

# Test 1: basic select
psql $DB_URL -c "SELECT count(*) FROM PTA;" 

# Test 2: insert and update PCA to trigger history
psql $DB_URL -c "INSERT INTO PCA (id_pca, descricao, valor, status) VALUES ('999/2025','TST',1000,'Preparação') ON CONFLICT DO NOTHING;"
psql $DB_URL -c "UPDATE PCA SET descricao = 'TST_UPDATED' WHERE id_pca = '999/2025';"
psql $DB_URL -c "DELETE FROM PCA WHERE id_pca = '999/2025';"

# Show PCA_Historico
psql $DB_URL -c "SELECT * FROM PCA_Historico ORDER BY data_op DESC LIMIT 5;"

echo "DB tests finished."
