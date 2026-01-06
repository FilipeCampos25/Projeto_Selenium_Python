# Filosofia de Design

## Objetivos
- **Fidelidade ao VBA**: Replicar exatamente a lógica, XPaths e padrões de espera do código VBA original para garantir compatibilidade.
- **Confiabilidade**: Scrapes previsíveis com tratamento robusto de erros e waits adequados.
- **Manutenibilidade**: Código modular, com separação clara de responsabilidades.
- **Observabilidade**: Logs estruturados em JSON para debugging e monitoramento.
- **Reprodutibilidade**: Ambientes conteinerizados para consistência entre dev e prod.

## Princípios
1. **Responsabilidade Única**: Cada scraper trata um portal específico e retorna JSON padronizado.
2. **Separação de Camadas**: RPA (scraping), API (orquestração), DB (persistência) isoladas.
3. **Fail Fast**: Erros expostos claramente; evitar exceções silenciosas.
4. **Configuração Externa**: XPaths, timeouts e credenciais em arquivos JSON ou env vars.
5. **Idempotência**: Persistência evita duplicatas via chaves únicas.
6. **Testabilidade**: Lógica isolável para testes unitários e integração.

## Padrões de Código
- Tipagem com type hints.
- Exceções customizadas para domínio.
- Injeção de dependências (FastAPI Depends).
- Linters: flake8, black, mypy.
- Logs: structured JSON logging.

## Estratégia de Testes
- Unitários para utilitários e validação.
- Integração com DB efêmero.
- E2E com Selenium em container.
