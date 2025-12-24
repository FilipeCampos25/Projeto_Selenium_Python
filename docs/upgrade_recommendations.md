# Recomendações de Ajustes e Melhorias — Conversão VBA -> Python + Selenium

Resumo: este documento lista ajustes imediatos e melhorias arquiteturais para alinhar a versão Python com o comportamento do projeto VBA + SeleniumBasic (projeto antigo), com ênfase em: fidelidade funcional, robustez, observabilidade, e eliminação de mocks.

## Estado atual detectado
- Projeto Python já contém módulos correspondentes às rotinas do VBA (mapa em `rpa/vba_to_python_mapping.md`).
- Não foram encontrados artefatos de `MOCK` no código.
- Há documentação base (`docs/*.md`) e infraestrutura para execução com docker-compose (selenium standalone).

## Ajustes imediatos implementados (neste pacote)
- Adicionado este documento com recomendações e plano de ação.
- Atualização sugerida do README e `development.md` (ver abaixo) — **apenas documentação adicionada**.

## Melhoria funcional prioritária (entregas sugeridas)
1. **Cobertura completa de XPATHs**
   - Extrair XPATHs do `Módulo1.bas` e mapear para `backend/app/rpa/selectors.json` (ou similar).
   - Implementar testes end-to-end (headless + headful) para validar fluxos críticos.

2. **Remover entradas interativas ou documentar o fluxo**
   - O VBA pode depender de prompts do usuário; padronizar via variáveis de ambiente (PNCP_USERNAME, PNCP_PASSWORD, PNCP_YEAR) e argumento CLI.

3. **Robustez Selenium**
   - Adicionar retries com backoff para waits.
   - Normalizar uso de `WebDriverWait` e evitar `time.sleep` exceto em casos explícitos requeridos.

4. **Observabilidade**
   - Integrar logging estruturado (JSON) e métricas (Prometheus client) nos pontos de coleta.
   - Melhorar tratamento de exceções com error codes e mensagens amigáveis.

5. **Banco de dados**
   - Migrar a persistência para SQLAlchemy ORM/ Alembic migrations completas.
   - Criar repositório de testes para validar inserções (DB em container).

6. **Testes**
   - Unit tests para modules `pncp_scraper`, `pncp_item`, `pncp_table`.
   - E2E test usando Selenium Grid (docker-compose) com fixture de HTML simplificado.

7. **Segurança**
   - Nunca commitar credenciais. Use `.env` com `.env.template`.
   - Criptografar/ esconder segredos em runtime (Hashicorp Vault / AWS Secrets Manager) em producação.

## Como eu posso proceder agora (se quiser)
- Se desejar, eu posso:
  - 1) Preencher automaticamente XPATHs a partir do `Módulo1.bas` e injetar em `selectors.json`.
  - 2) Substituir qualquer parte que ainda use prompts interativos por configuração via CLI/env.
  - 3) Gerar `requirements.txt` e uma imagem Docker otimizada.

> Observação: para preencher XPATHs automaticamente preciso confirmar que os trechos relevantes do `Módulo1.bas` estão corretos e autorizados a serem convertidos (já existe `modulo1/modulo1/Módulo1.bas` no pacote).