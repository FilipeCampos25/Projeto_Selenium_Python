# Análise Estrutural do Código VBA

## Estrutura Geral

**Arquivo:** Módulo1.bas  
**Linhas totais:** 9900  
**Linguagem:** VBA (Visual Basic for Applications)  
**Framework:** Selenium WebDriver para automação web

## Constantes e Variáveis Globais

```vba
Global pos, posd As Integer
Const arquivo_excel As String = "PGC_2025.xlsm"
Const ano_ref As String = "2025"
Const ptaCap = "035/25"
Dim driver As New WebDriver
```

## Funções e Procedimentos Identificados (Total: 60)

### 1. Categoria: Autenticação e Acesso
- **A_Loga_Acessa_PGC()** (linha 16)
  - Login no portal Comprasnet
  - Acesso ao módulo PGC (Planejamento e Gerenciamento de Contratações)
  
### 2. Categoria: Leitura de DFDs (Documentos de Formalização de Demanda)
- **A1_Demandas_DFD_PCA()** (linha 177)
  - Leitura de demandas DFD do PCA
- **le_dfd()** (linha 690)
  - Leitura específica de DFD
- **le_imagem_dfd()** (linha 9611)
  - Leitura de imagem DFD

### 3. Categoria: Gerenciamento de Contratações
- **A3_Cria_Contratacao()** (linha 1442)
  - Criação de contratação
- **gera_contratacao()** (linha 1696)
  - Geração de contratação
- **A4_Atualiza_Contratacao()** (linha 1727)
  - Atualização de contratação
- **Atualiza_Contratacao1()** (linha 868)
  - Atualização alternativa de contratação

### 4. Categoria: Integração com PNCP (Portal Nacional de Contratações Públicas)
- **Dados_PNCP()** (linha 2161)
  - Coleta de dados do PNCP
- **le_andamento_PNCP()** (linha 7484)
  - Leitura de andamentos PNCP
- **A6_DownloadPNCP()** (linha 9137)
  - Download de dados PNCP

### 5. Categoria: Integração com SEI (Sistema Eletrônico de Informações)
- **A2_leitura_SEI()** (linha 2929)
  - Leitura de processos SEI
- **Seleciona_NUCONF()** (linha 3022)
  - Seleção de número de conferência
- **Ativa_2fa()** (linha 3045)
  - Ativação de autenticação de dois fatores
- **atualiza_SEI()** (linha 3057)
  - Atualização de dados SEI
- **Calcula_SEI()** (linha 3316)
  - Cálculos relacionados ao SEI
- **NavegaProc_SEI()** (linha 3953)
  - Navegação em processos SEI
- **busca_Sei()** (linha 4806)
  - Busca em SEI
- **montaDesempenho_SEI()** (linha 4820)
  - Montagem de desempenho SEI
- **montaRetenção_SEI()** (linha 4930)
  - Montagem de retenção SEI
- **registraDocto_SEI()** (linha 4990)
  - Registro de documento SEI
- **A7_busca_DFD_SEI()** (linha 9270)
  - Busca de DFD no SEI

### 6. Categoria: Análise e Estatísticas
- **analise()** (linha 5048)
  - Análise geral
- **cria_Analitico_PCA()** (linha 5527)
  - Criação de analítico PCA
- **cria_Analitico_PCA1()** (linha 7891)
  - Criação de analítico PCA (versão 1)
- **cria_estatisticas_PCA()** (linha 6286)
  - Criação de estatísticas PCA
- **cria_estatisticas_PCA1()** (linha 8315)
  - Criação de estatísticas PCA (versão 1)

### 7. Categoria: Ajustes e Correções
- **corrige_falha_PGC()** (linha 517)
  - Correção de falhas no PGC
- **ajuste_pgc_anual_x_pgc()** (linha 2658)
  - Ajuste entre PGC anual e PGC
- **ajuste_pgc_anual_x_PNCP()** (linha 2832)
  - Ajuste entre PGC anual e PNCP

### 8. Categoria: Utilitários de Navegação e Espera
- **testa_spinner()** (linha 813)
  - Teste de spinner (loading)
- **testa_spinner2()** (linha 791)
  - Teste de spinner alternativo
- **localiza_icones()** (linha 837)
  - Localização de ícones
- **nextPage()** (linha 1363)
  - Navegação para próxima página

### 9. Categoria: Manipulação de Excel
- **CopiarPlanilha()** (linha 6435)
  - Cópia de planilha
- **ExcluirPlanilha1()** (linha 6538)
  - Exclusão de planilha
- **Formata_Planilha_PCA()** (linha 6563)
  - Formatação de planilha PCA
- **Formata_Planilha_PCA1()** (linha 8455)
  - Formatação de planilha PCA (versão 1)
- **Formata_Planilha_PTA()** (linha 7083)
  - Formatação de planilha PTA
- **SetColWidth()** (linha 1392)
  - Definição de largura de coluna
- **AbaExiste()** (linha 8923)
  - Verificação de existência de aba
- **CopiarArrayParaPlanilha()** (linha 8932)
  - Cópia de array para planilha
- **CarregarArrayNoFinalDaPlanilha()** (linha 8971)
  - Carregamento de array no final da planilha

### 10. Categoria: Utilitários Gerais
- **ordena()** (linha 1408)
  - Ordenação de array
- **RemoverDuplicatasMatriz()** (linha 7679)
  - Remoção de duplicatas em matriz
- **DetectarDelimitador()** (linha 9245)
  - Detecção de delimitador em arquivo
- **ValidarData()** (linha 9764)
  - Validação de data
- **ExisteElemento()** (linha 9791)
  - Verificação de existência de elemento
- **SetZoom()** (linha 9831)
  - Definição de zoom

### 11. Categoria: Download e Configuração
- **A5_DownloadChromeDriver()** (linha 8993)
  - Download do ChromeDriver
- **A5_BaixarChromeDriverStable_Win64()** (linha 9048)
  - Download do ChromeDriver estável Win64

### 12. Categoria: Busca e Processamento
- **busca_aberto_PCA()** (linha 6105)
  - Busca de processos abertos PCA
- **busca_aberto_PCA1()** (linha 7722)
  - Busca de processos abertos PCA (versão 1)
- **buscaDoc_SEI()** (linha 3907)
  - Busca de documento SEI
- **varre_SEI()** (linha 3752)
  - Varredura SEI
- **limpa_processo_SEI()** (linha 3718)
  - Limpeza de processo SEI

### 13. Categoria: Registro e Log
- **registra()** (linha 3920)
  - Registro de informações
- **registra1()** (linha 3937)
  - Registro de informações (versão 1)

### 14. Categoria: Testes
- **teste()** (linha 2070)
  - Função de teste

## Padrões Identificados

### Padrão de Espera (Spinner/Loading)
```vba
Do While Not driver.IsElementPresent(By.XPath("..."))
Loop
```

### Padrão de Navegação
```vba
driver.FindElementByXPath("...").Click
driver.ExecuteScript("window.scrollTo(0, document.body.scrollHeight);")
```

### Padrão de Tratamento de Erros
```vba
redo:
    ' código
    If condição Then GoTo redo
```

### Padrão de Controle de Aplicação
```vba
Application.ScreenUpdating = False
Application.EnableEvents = False
Application.Wait Now + TimeValue("00:00:01")
```

## Fluxo Principal Identificado

1. **Login e Autenticação** → A_Loga_Acessa_PGC()
2. **Seleção de PCA/Ano** → Navegação no sistema
3. **Leitura de DFDs** → le_dfd(), A1_Demandas_DFD_PCA()
4. **Criação/Atualização de Contratações** → A3_Cria_Contratacao(), A4_Atualiza_Contratacao()
5. **Integração com PNCP** → Dados_PNCP(), le_andamento_PNCP()
6. **Integração com SEI** → A2_leitura_SEI(), NavegaProc_SEI()
7. **Análise e Estatísticas** → cria_Analitico_PCA(), cria_estatisticas_PCA()
8. **Exportação para Excel** → Múltiplas funções de formatação e cópia

## Próximos Passos

1. Análise detalhada de cada função principal
2. Mapeamento de XPaths e seletores
3. Identificação de lógica de negócio específica
4. Comparação com código Python atual
