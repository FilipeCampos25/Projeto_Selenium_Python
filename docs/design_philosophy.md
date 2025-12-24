# Filosofia de Design

## Objetivos
- **Confiabilidade:** Garantir que as raspagens sejam previsíveis e que falhas sejam visíveis.
- **Manutenibilidade:** Tornar scrapers modulares, com funções pequenas e contratos claros.
- **Testabilidade:** Permitir testar lógica sem navegador real .
- **Observabilidade:** Logs estruturados, métricas e erros claros.
- **Reprodutibilidade:** Ambientes conteinerizados (docker-compose) para paridade dev/prod.

## Princípios
1. **Responsabilidade única:** Cada módulo de scraper trata um único portal e retorna um schema JSON definido.
2. **Separação de responsabilidades:** RPA, transformação/validação, persistência e orquestração são camadas separadas.
3. **Fail fast e reporting claro:** Validação deve expor erros acionáveis; evitar engolir exceções silenciosamente.
4. **Idempotência:** Persistência no BD deve ser idempotente ou usar chaves de deduplicação (ex.: fonte + id_fonte + data).
5. **Contratos observáveis:** Endpoints documentados e logs em formato estruturado (JSON).
6. **Config como dados:** Seletors de site, timeouts e parâmetros devem ficar em configs (YAML/ENV), não espalhados no código.

## Estratégia de testes
- Testes unitários para transformação e validação.
- Testes de integração com scrapers e Postgres efêmero (pytest + testcontainers ou perfil de teste docker-compose).
- Testes end-to-end com sessão Selenium gravada ou ambiente de homologação.

## Padrões de código
- Anotações de tipo em módulos críticos.
- Exceções explícitas (classes de erro de domínio).
- Injeção de dependência para sessão do DB (FastAPI `Depends`).
- Linters (flake8/pylint), formatador (black) e checagem de tipos (mypy).
