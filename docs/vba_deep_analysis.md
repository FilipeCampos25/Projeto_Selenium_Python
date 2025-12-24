# Análise Profunda do Código VBA - Estrutura Lógica e Fluxo de Execução

## Resumo Executivo

O código VBA analisado possui **9.900 linhas** e implementa um sistema completo de automação web para coleta de dados de sistemas governamentais brasileiros, especificamente:

- **PGC** (Planejamento e Gerenciamento de Contratações)
- **PNCP** (Portal Nacional de Contratações Públicas)
- **SEI** (Sistema Eletrônico de Informações)

## Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| Total de Funções/Subs | 59 |
| XPaths Únicos | 48 |
| IDs de Elementos | 7 |
| Explicit Waits | 89 ocorrências |
| Do While Loops | 11 ocorrências |
| Do Until Loops | 31 ocorrências |
| Clicks | 91 ocorrências |
| Scrolls | 64 ocorrências |
| Execute Scripts | 10 ocorrências |
| Switch Window | 3 ocorrências |
| Chamadas testa_spinner | 117 ocorrências |
| Operações em Células Excel | 55 |
| Operações em Ranges Excel | 1.620 |

## Fluxo Principal de Execução

### 1. Função Principal: A1_Demandas_DFD_PCA()

Esta é a função orquestradora principal que executa o seguinte fluxo:

#### 1.1. Inicialização
```vba
Application.ScreenUpdating = False
Application.EnableEvents = False
```
**Propósito:** Desabilita atualização de tela e eventos do Excel para melhor performance.

#### 1.2. Login e Acesso ao Sistema
```vba
A_Loga_Acessa_PGC
```
**Propósito:** Realiza login no portal Comprasnet e navega até o módulo PGC.

#### 1.3. Seleção de Ano e Filtros
```vba
driver.FindElementByXPath("//p-dropdown[@placeholder='Selecione PCA']").Click
driver.FindElementByXPath("//li[starts-with(@aria-label,'PCA " + ano_ref + " -')]").Click
driver.FindElementById("minha-uasg").Click
```
**Propósito:** Seleciona o PCA do ano de referência (2025) e filtra por "minha UASG".

#### 1.4. Navegação de Paginação
```vba
' Vai para última página
driver.FindElementByXPath("...p-paginator-last...").Click

' Obtém número total de páginas
For Each tabela1 In tabelas
    If tabela1.Text <> "" Then
       posM = tabela1.Text
    End If
Next

' Volta para primeira página
driver.FindElementByXPath("...p-paginator-first...").Click
```
**Propósito:** Descobre quantas páginas existem no resultado.

#### 1.5. Ordenação da Tabela
```vba
driver.FindElementByXPath("...thead/tr/th[4]").Click
```
**Propósito:** Ordena a tabela pela 4ª coluna (provavelmente DFD).

#### 1.6. Preparação da Planilha Excel
```vba
Sheets("PGC").Range("A:U").Delete
Sheets("PGC").Range("A1") = "Pag"
Sheets("PGC").Range("B1") = "DFD"
Sheets("PGC").Range("C1") = "Requisitante"
Sheets("PGC").Range("D1") = "Descrição"
Sheets("PGC").Range("E1") = "Valor"
Sheets("PGC").Range("F1") = "Situação"
Sheets("PGC").Range("G1") = "Conclusão"
Sheets("PGC").Range("H1") = "Editor"
Sheets("PGC").Range("I1") = "Responsáveis"
Sheets("PGC").Range("J1") = "PTA"
Sheets("PGC").Range("K1") = "Justificativa"
```
**Propósito:** Limpa e prepara cabeçalhos da planilha PGC.

#### 1.7. Loop de Coleta de Dados (Paginação)
```vba
Do Until sai = True
    ' Navega para página específica
    For Each tabela1 In tabelas
        If CStr(tabela1.Text) = pos Then
            tabela1.Click
            Exit For
        End If
    Next
    
    ' Extrai tabela da página
    Set tabela = driver.FindElementByXPath("...table").AsTable
    
    ' Processa dados da tabela
    Dim data(): data = tabela.data
    For r = 1 To UBound(data, 1)
        If (data(r, 4) <> "DFD") Then
            ' Escreve na planilha
            Worksheets("PGC").Cells(linha, 1).Value = pos
            Worksheets("PGC").Cells(linha, 2).Value = Right("000" & CStr(data(r, 4)), 8)
            Worksheets("PGC").Cells(linha, 3).Value = data(r, 6)
            Worksheets("PGC").Cells(linha, 4).Value = data(r, 7)
            Worksheets("PGC").Cells(linha, 5).Value = valor
            Worksheets("PGC").Cells(linha, 6).Value = data(r, 9)
            linha = linha + 1
        End If
    Next
    
    ' Verifica se chegou na última página
    If (pos >= posM) Then
        sai = True
    End If
    pos = pos + 1
Loop
```
**Propósito:** Itera por todas as páginas, extrai dados da tabela e escreve no Excel.

#### 1.8. Correção de Falhas e Limpeza
```vba
corrige_falha_PGC
Worksheets("PGC").Range("A1:AZ" + Trim(str(pos))).Sort Key1:=Range("B1"), Header:=xlYes
Worksheets("PGC").Range("A1:O" + Trim(str(pos))).RemoveDuplicates Columns:=Array(2), Header:=xlYes
```
**Propósito:** Corrige falhas de leitura, ordena e remove duplicatas.

#### 1.9. Leitura Detalhada de DFDs
```vba
le_dfd
```
**Propósito:** Para cada DFD coletado, acessa detalhes individuais.

#### 1.10. Ajustes e Integração com PNCP
```vba
ajuste_pgc_anual_x_pgc
Dados_PNCP
```
**Propósito:** Ajusta dados e integra com PNCP.

#### 1.11. Finalização
```vba
Application.ScreenUpdating = True
Application.EnableEvents = True
```
**Propósito:** Reabilita atualização de tela e eventos.

### 2. Função de Login: A_Loga_Acessa_PGC()

Fluxo detalhado de autenticação:

#### 2.1. Coleta de Credenciais
```vba
MyLogin = Application.InputBox("Por Favor entre com o Login", "Login", Default:="59494964691", Type:=2)
MyPass = Application.InputBox("Por favor entre com a senha", "Senha", Default:="01etpdigital", Type:=2)
If MyLogin = "" Or MyPass = "" Then GoTo redo
```

#### 2.2. Inicialização do Driver
```vba
driver.Start "chrome"
driver.Get "http://www.comprasnet.gov.br/seguro/loginPortal.asp"
driver.Window.Maximize
```

#### 2.3. Expansão do Menu de Login Governo
```vba
Do While Not driver.IsElementPresent(By.XPath("//button[@class='br-button circle expand governo']"))
Loop
driver.FindElementByXPath("//button[@class='br-button circle expand governo']").Click
```

#### 2.4. Scroll e Preenchimento de Credenciais
```vba
driver.ExecuteScript("window.scrollTo(0, document.body.scrollHeight);")
Do While Not driver.IsElementPresent(By.XPath("//button[@onclick='frmLoginGoverno_submit(); return false;']"))
Loop
driver.FindElementById("txtLogin").SendKeys MyLogin
driver.FindElementById("txtSenha").SendKeys MyPass
driver.FindElementByXPath("//button[@onclick='frmLoginGoverno_submit(); return false;']").Click
```

#### 2.5. Espera por Processamento
```vba
testa_spinner
Do While Not driver.IsElementPresent(By.XPath("//div[@class='texto']/div[2][text()=' Estamos processando a sua solicitação. ']"))
Loop
```

#### 2.6. Navegação até PGC
```vba
Do While Not driver.IsElementPresent(By.XPath("//span[text()='Planejamento e Gerenciamento de Contratações']"))
Loop
driver.FindElementByXPath("//span[text()='Planejamento e Gerenciamento de Contratações']").ScrollIntoView
driver.FindElementByXPath("//div/p[2][text()='PGC']").Click
```

#### 2.7. Troca de Janela
```vba
driver.SwitchToWindowByTitle "Compras.gov.br - Fase Interna"
```

### 3. Função de Espera: testa_spinner()

Padrão crítico de sincronização:

```vba
Sub testa_spinner()
    Dim caminho As String
    Dim By As New By
    
    caminho = "//body/app-root/ng-http-loader/div[@id='spinner']"
    
    Do
        Application.Wait Now + (TimeValue("00:00:01") / 10)
    Loop While driver.FindElementByXPath(caminho, timeout:=1, Raise:=False).IsPresent
End Sub
```

**Lógica:** Aguarda enquanto o spinner de loading estiver presente, verificando a cada 0.1 segundo.

### 4. Função le_dfd()

Leitura detalhada de cada DFD:

```vba
Sub le_dfd()
    ' Para cada linha da planilha PGC
    For i = 2 To pos
        dfd = Worksheets("PGC").Cells(i, 2).Value
        
        ' Clica no DFD para abrir detalhes
        driver.FindElementByXPath("//td[text()='" + dfd + "']").Click
        testa_spinner
        
        ' Extrai informações adicionais
        ' - Conclusão
        ' - Editor
        ' - Responsáveis
        ' - PTA
        ' - Justificativa
        
        ' Fecha modal
        driver.FindElementByXPath("//span/button[text()='Fechar']").Click
    Next
End Sub
```

## Padrões de Código Identificados

### Padrão 1: Espera Explícita com Do While
```vba
Do While Not driver.IsElementPresent(By.XPath("..."))
Loop
```
**Uso:** Aguarda até que um elemento apareça na página.

### Padrão 2: Espera com Spinner
```vba
testa_spinner
```
**Uso:** Aguarda até que o spinner de loading desapareça (chamado 117 vezes).

### Padrão 3: Scroll para Elemento
```vba
driver.FindElementByXPath("...").ScrollIntoView
```
**Uso:** Garante que o elemento esteja visível antes de interagir.

### Padrão 4: Extração de Tabela
```vba
Set tabela = driver.FindElementByXPath("...table").AsTable
Dim data(): data = tabela.data
For r = 1 To UBound(data, 1)
    ' Processa linha
Next
```
**Uso:** Extrai dados de tabelas HTML para array VBA.

### Padrão 5: Navegação de Paginação
```vba
For Each tabela1 In tabelas
    If CStr(tabela1.Text) = pos Then
        tabela1.Click
        Exit For
    End If
Next
```
**Uso:** Navega para página específica em paginador.

### Padrão 6: Tratamento de Erro com GoTo
```vba
redo:
    ' código
    If condição Then GoTo redo
```
**Uso:** Retry em caso de falha.

### Padrão 7: Escrita Incremental no Excel
```vba
If (Worksheets("PGC").Range("A2").Value = "") Then
    linha = 2
Else
    linha = Worksheets("PGC").Range("A1").End(xlDown).Row + 1
End If
```
**Uso:** Encontra próxima linha vazia para escrita.

## Mapeamento de Dados Coletados

### Estrutura da Planilha PGC

| Coluna | Nome | Origem (índice tabela HTML) |
|--------|------|----------------------------|
| A | Pag | pos (número da página) |
| B | DFD | data(r, 4) |
| C | Requisitante | data(r, 6) |
| D | Descrição | data(r, 7) |
| E | Valor | data(r, 8) |
| F | Situação | data(r, 9) |
| G | Conclusão | Extraído em le_dfd() |
| H | Editor | Extraído em le_dfd() |
| I | Responsáveis | Extraído em le_dfd() |
| J | PTA | Extraído em le_dfd() |
| K | Justificativa | Extraído em le_dfd() |

## XPaths Críticos Identificados

### Login e Navegação Inicial
```
//button[@class='br-button circle expand governo']
//button[@onclick='frmLoginGoverno_submit(); return false;']
//span[text()='Planejamento e Gerenciamento de Contratações']
//div/p[2][text()='PGC']
```

### Seleção de Filtros
```
//p-dropdown[@placeholder='Selecione PCA']
//li[starts-with(@aria-label,'PCA " + ano_ref + " -')]
```

### Paginação
```
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/button[@class='p-ripple p-element p-paginator-last p-paginator-element p-link ng-star-inserted']
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/button[@class='p-ripple p-element p-paginator-first p-paginator-element p-link ng-star-inserted']
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/span[@class='p-paginator-pages ng-star-inserted']/button
```

### Tabela de Dados
```
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/div[@class='p-datatable-wrapper']/table
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/div/table/thead/tr/th[4]
```

### Spinner de Loading
```
//body/app-root/ng-http-loader/div[@id='spinner']
```

### IDs de Elementos
```
txtLogin
txtSenha
minha-uasg
spinner
```

## Lógica de Negócio Específica

### 1. Formatação de DFD
```vba
Right("000" & CStr(data(r, 4)), 8)
```
**Propósito:** Formata DFD com zeros à esquerda, garantindo 8 caracteres.

### 2. Tratamento de Valor Monetário
```vba
If (data(r, 8) = "") Then
    valor = 0
Else
    valor = CDbl(data(r, 8))
End If
```
**Propósito:** Converte valor para Double, tratando valores vazios.

### 3. Detecção de Última Página
```vba
For Each tabela1 In tabelas
    If tabela1.Text <> "" Then
       posM = tabela1.Text
    End If
Next
```
**Propósito:** Itera por botões de paginação para encontrar o número da última página.

### 4. Correção de Falha de Leitura
```vba
corrige_falha_PGC
```
**Propósito:** Função específica para corrigir falhas conhecidas na leitura da última página.

## Integrações com Outros Sistemas

### 1. PNCP (Portal Nacional de Contratações Públicas)
- Função: `Dados_PNCP()`
- Função: `le_andamento_PNCP()`
- Função: `A6_DownloadPNCP()`
- Função: `ajuste_pgc_anual_x_PNCP()`

### 2. SEI (Sistema Eletrônico de Informações)
- Função: `A2_leitura_SEI()`
- Função: `NavegaProc_SEI()`
- Função: `Calcula_SEI()`
- Função: `A7_busca_DFD_SEI()`

## Planilhas Excel Utilizadas

| Planilha | Propósito |
|----------|-----------|
| PGC | Dados principais de DFDs coletados |
| PNCP | Dados do Portal Nacional de Contratações |
| Analise | Análises e estatísticas |
| Analitico_PCA | Análise analítica do PCA |
| Estatisticas_PCA | Estatísticas do PCA |
| Historico_doctos | Histórico de documentos |
| Processos | Processos do SEI |
| Temp_SEI | Dados temporários do SEI |
| Desempenho | Métricas de desempenho |
| Retencao | Dados de retenção |

## Conclusões da Análise

### Características Principais do Código VBA

1. **Altamente Sequencial:** O código segue um fluxo linear e sequencial, sem paralelização.

2. **Dependente de Sincronização:** Uso intensivo de `testa_spinner()` (117 chamadas) indica que a sincronização é crítica.

3. **Navegação Complexa:** Múltiplos níveis de navegação (login → seleção de ano → filtros → paginação → detalhes).

4. **Extração de Tabelas:** Uso do método `.AsTable` do Selenium VBA para extrair dados de tabelas HTML.

5. **Escrita Incremental:** Dados são escritos linha por linha no Excel durante a coleta.

6. **Tratamento de Paginação:** Lógica sofisticada para descobrir total de páginas e navegar sequencialmente.

7. **Múltiplas Integrações:** Integra dados de 3 sistemas diferentes (PGC, PNCP, SEI).

8. **Formatação de Dados:** Aplica formatações específicas (DFD com 8 dígitos, valores monetários).

9. **Limpeza e Deduplicação:** Remove duplicatas e ordena dados após coleta.

10. **Correção de Falhas:** Implementa funções específicas para corrigir falhas conhecidas.

### Pontos Críticos para Replicação em Python

1. **Espera por Spinner:** Implementar wait customizado que aguarda desaparecimento do spinner.

2. **Extração de Tabelas:** Replicar lógica de `.AsTable` usando Selenium Python.

3. **Navegação de Paginação:** Implementar lógica de descoberta de total de páginas e navegação sequencial.

4. **Formatação de DFD:** Garantir formatação com 8 dígitos.

5. **Escrita de Dados:** Substituir escrita em Excel por escrita em banco de dados (PostgreSQL).

6. **XPaths Específicos:** Usar exatamente os mesmos XPaths do VBA.

7. **Fluxo de Login:** Replicar exatamente o mesmo fluxo de login multi-etapas.

8. **Scroll e Visualização:** Implementar ScrollIntoView antes de interações.

9. **Troca de Janelas:** Implementar `switch_to.window` corretamente.

10. **Tratamento de Erros:** Implementar retry logic similar ao GoTo do VBA.
