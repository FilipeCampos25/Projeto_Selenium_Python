# Mapeamento de Gaps e Diferenças: VBA vs Python

## Resumo Executivo

Após análise profunda de ambos os códigos, identificamos que o código Python atual possui **apenas 26% do tamanho do VBA** (2.622 linhas vs 9.900 linhas), mas está **modularizado em 14 arquivos** contra 1 arquivo monolítico do VBA. Apesar da modularização, existem **gaps críticos de implementação** que precisam ser corrigidos para replicar fielmente a lógica do VBA.

## Comparação Estrutural

| Aspecto               | VBA                 | Python Atual        | Status                |
|-----------------------|---------------------|---------------------|-----------------------|
| Total de Linhas       | 9.900               | 2.622               | ⚠️ Python muito menor |
| Arquivos              | 1 monolítico        | 14 modulares        | ✅ Melhor estrutura   |
| Funções Principais    | 59                  | ~40 (distribuídas)  | ⚠️ Faltam funções     |
| XPaths Únicos         | 48                  | ~20 (estimado)      | ❌ Faltam XPaths      |
| Espera por Spinner    | 117 chamadas        | Implementado        | ⚠️ Uso insuficiente   |
| Extração de Tabelas   | `.AsTable` nativo   | Manual com loops    | ⚠️ Diferente          |
| Paginação             | Lógica completa     | Parcial             | ❌ Incompleta         |
| Formatação DFD        | 8 dígitos com zeros | Não implementado    | ❌ Faltando           |
| Scroll antes de Click | 64 ocorrências      | Parcial             | ⚠️ Insuficiente       |
| Switch Window         | 3 ocorrências       | Não identificado    | ❌ Faltando           |
| Correção de Falhas    | Função dedicada     | Try/except genérico | ⚠️ Diferente          |

## Gaps Críticos Identificados

### 1. Fluxo de Login Incompleto

**VBA (Completo):**
```vba
' 1. Abre portal
driver.Get "http://www.comprasnet.gov.br/seguro/loginPortal.asp"
driver.Window.Maximize

' 2. Expande menu governo
Do While Not driver.IsElementPresent(By.XPath("//button[@class='br-button circle expand governo']"))
Loop
driver.FindElementByXPath("//button[@class='br-button circle expand governo']").Click

' 3. Scroll down
driver.ExecuteScript("window.scrollTo(0, document.body.scrollHeight);")

' 4. Aguarda botão de login
Do While Not driver.IsElementPresent(By.XPath("//button[@onclick='frmLoginGoverno_submit(); return false;']"))
Loop

' 5. Preenche credenciais
driver.FindElementById("txtLogin").SendKeys MyLogin
driver.FindElementById("txtSenha").SendKeys MyPass
driver.FindElementByXPath("//button[@onclick='frmLoginGoverno_submit(); return false;']").Click

' 6. Aguarda processamento
testa_spinner
Do While Not driver.IsElementPresent(By.XPath("//div[@class='texto']/div[2][text()=' Estamos processando a sua solicitação. ']"))
Loop

' 7. Aguarda menu PGC
Do While Not driver.IsElementPresent(By.XPath("//span[text()='Planejamento e Gerenciamento de Contratações']"))
Loop

' 8. Scroll e visualiza PGC
driver.FindElementByXPath("//span[text()='Planejamento e Gerenciamento de Contratações']").ScrollIntoView
driver.FindElementByXPath("//div/p[2][text()='PGC']").Click

' 9. Troca de janela
driver.SwitchToWindowByTitle "Compras.gov.br - Fase Interna"
```

**Python (Simplificado demais):**
```python
# Apenas login básico, sem todas as etapas de sincronização
el_user.send_keys(username)
el_pass.send_keys(password)
el_submit.click()
```

**Gap:** Faltam 7 etapas de sincronização e navegação.

### 2. Lógica de Paginação Incompleta

**VBA (Completa):**
```vba
' 1. Vai para última página para descobrir total
If driver.IsElementPresent(By.XPath("...p-paginator-last...")) Then
    driver.FindElementByXPath("...p-paginator-last...").Click
End If

' 2. Descobre número total de páginas
Set tabelas = driver.FindElementsByXPath("...span[@class='p-paginator-pages ng-star-inserted']/button")
For Each tabela1 In tabelas
    If tabela1.Text <> "" Then
       posM = tabela1.Text  ' Maior página
    End If
Next

' 3. Volta para primeira página
If driver.IsElementPresent(By.XPath("...p-paginator-first...")) Then
    driver.FindElementByXPath("...p-paginator-first...").Click
End If

' 4. Loop por todas as páginas
Do Until sai = True
    ' Navega para página específica
    For Each tabela1 In tabelas
        If CStr(tabela1.Text) = pos Then
            tabela1.Click
            Exit For
        End If
    Next
    
    ' Extrai dados
    Set tabela = driver.FindElementByXPath("...table").AsTable
    ' ... processa dados ...
    
    ' Verifica se é última página
    If (pos >= posM) Then
        sai = True
    End If
    pos = pos + 1
Loop
```

**Python (Incompleto):**
```python
# Tenta iterar páginas mas sem descobrir total primeiro
for page_index in range(2, page_count+1 if page_count>0 else 1000):
    # ... código ...
```

**Gap:** Não descobre total de páginas antes, não volta para primeira página, lógica de navegação diferente.

### 3. Extração de Tabela Diferente

**VBA (Nativo):**
```vba
Set tabela = driver.FindElementByXPath("...table").AsTable
Dim data(): data = tabela.data
For r = 1 To UBound(data, 1)
    If (data(r, 4) <> "DFD") Then
        Worksheets("PGC").Cells(linha, 2).Value = Right("000" & CStr(data(r, 4)), 8)
        Worksheets("PGC").Cells(linha, 3).Value = data(r, 6)
        ' ... etc ...
    End If
Next
```

**Python (Manual):**
```python
rows = table.find_elements(By.XPATH, ".//tbody/tr")
for index, row in enumerate(rows, start=1):
    cols = row.find_elements(By.XPATH, "./td")
    numero = cols[0].text.strip()
    titulo = cols[1].text.strip() if len(cols) > 1 else ""
    # ... etc ...
```

**Gap:** Índices de colunas diferentes, sem formatação de DFD, sem verificação de cabeçalho.

### 4. Função le_dfd() Não Implementada Corretamente

**VBA (Completo):**
```vba
Sub le_dfd()
    For i = 2 To Worksheets("PGC").Range("a1").End(xlDown).Row
        If (Worksheets("PGC").Cells(i, 2).Value <> "000...") Then
            ' Monta URL do DFD
            enderecoDfd = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/artefatos/view?identificador=110511" & Right("00000" & Replace(Worksheets("PGC").Cells(i, 2).Value, "/", ""), 10) & "&autoriza=e&tipo=DFD"
            
            ' Acessa DFD
            driver.Get enderecoDfd
            
            ' Aguarda carregamento
            Do While Not driver.IsElementPresent(By.XPath("//p[text()=' Detalhar Documento de Formalização da Demanda ']"))
            Loop
            
            ' Extrai data de conclusão
            caminho = "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[2]/div[1]/div[2]/p"
            Worksheets("PGC").Cells(i, 7).Value = CDate(driver.FindElementByXPath(caminho).Text)
            
            ' Extrai editor
            caminho = "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[2]/div[1]/div[4]/p"
            Worksheets("PGC").Cells(i, 8).Value = driver.FindElementByXPath(caminho).Text
            
            ' Extrai responsáveis (com tabela interna)
            caminho = "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[7]/button"
            If (Right(driver.FindElementByXPath(caminho).Text, 3) = "(0)") Then
                Worksheets("PGC").Cells(i, 9).Value = "Responsáveis não definidos"
            Else
                driver.FindElementByXPath(caminho).Click
                caminho = "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[8]/p-table/div/div/table"
                Set tabela = driver.FindElementByXPath(caminho).AsTable
                ' ... processa tabela de responsáveis ...
            End If
        End If
    Next
End Sub
```

**Python (Parcial em pgc_scraper_dfd.py):**
```python
# Existe arquivo mas implementação incompleta
```

**Gap:** Lógica de construção de URL, extração de múltiplos campos, processamento de tabela interna de responsáveis.

### 5. Espera por Spinner Não Usada Consistentemente

**VBA:**
- 117 chamadas para `testa_spinner`
- Após cada ação de navegação

**Python:**
- Função `wait_spinner` existe em `waiter.py`
- Mas não é chamada consistentemente após navegações

**Gap:** Falta chamada sistemática de `wait_spinner` após cada ação.

### 6. XPaths Específicos Faltando

**VBA usa XPaths muito específicos:**
```
//button[@class='br-button circle expand governo']
//button[@onclick='frmLoginGoverno_submit(); return false;']
//div[@class='texto']/div[2][text()=' Estamos processando a sua solicitação. ']
//span[text()='Planejamento e Gerenciamento de Contratações']
//div/p[2][text()='PGC']
//p-dropdown[@placeholder='Selecione PCA']
//li[starts-with(@aria-label,'PCA " + ano_ref + " -')]
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/button[@class='p-ripple p-element p-paginator-last p-paginator-element p-link ng-star-inserted']
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/span[@class='p-paginator-pages ng-star-inserted']/button
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/div[@class='p-datatable-wrapper']/table
//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/div/table/thead/tr/th[4]
//body/app-root/ng-http-loader/div[@id='spinner']
//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[2]/div[1]/div[2]/p
//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[2]/div[1]/div[4]/p
//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[7]/button
//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[8]/p-table/div/div/table
```

**Python usa XPaths genéricos:**
```
//table[contains(@class,'table')]
//button[contains(., 'Consultar')]
//div[contains(@class,'p-paginator')]//button
```

**Gap:** XPaths do Python são muito genéricos e não correspondem aos específicos do VBA.

### 7. Ordenação da Tabela Antes de Extrair

**VBA:**
```vba
' Ordena pela 4ª coluna (DFD)
driver.FindElementByXPath("...thead/tr/th[4]").ScrollIntoView
driver.FindElementByXPath("...thead/tr/th[4]").Click
testa_spinner
```

**Python:**
- Não implementado

**Gap:** Não ordena tabela antes de extrair dados.

### 8. Formatação de DFD com 8 Dígitos

**VBA:**
```vba
Worksheets("PGC").Cells(linha, 2).Value = Right("000" & CStr(data(r, 4)), 8)
```

**Python:**
```python
numero = cols[0].text.strip()  # Sem formatação
```

**Gap:** Não formata DFD com zeros à esquerda.

### 9. Correção de Falha da Última Página

**VBA:**
```vba
Sub corrige_falha_PGC()
    ' Lógica específica para corrigir falha conhecida
    ' na leitura da última página do sistema PGC
End Sub
```

**Python:**
- Não implementado

**Gap:** Não tem lógica de correção de falha conhecida.

### 10. Integração com PNCP e SEI

**VBA:**
- Funções: `Dados_PNCP()`, `le_andamento_PNCP()`, `A2_leitura_SEI()`, `NavegaProc_SEI()`
- Integração completa após coleta PGC

**Python:**
- Arquivos separados (`pncp_scraper.py`) mas sem integração no fluxo principal

**Gap:** Não executa integração PNCP/SEI após coleta PGC.

## Mapeamento Detalhado de Funções

| Função VBA | Arquivo Python | Status | Ação Necessária |
|------------|----------------|--------|-----------------|
| A_Loga_Acessa_PGC | pgc_scraper.py | ⚠️ Parcial | Implementar fluxo completo de 9 etapas |
| A1_Demandas_DFD_PCA | pgc_scraper.py + pgc_scraper_table.py | ⚠️ Parcial | Corrigir lógica de paginação e extração |
| testa_spinner | waiter.py | ✅ Implementado | Usar consistentemente |
| testa_spinner2 | waiter.py | ✅ Implementado | - |
| localiza_icones | - | ❌ Faltando | Implementar |
| le_dfd | pgc_scraper_dfd.py | ⚠️ Parcial | Completar extração de campos |
| corrige_falha_PGC | - | ❌ Faltando | Implementar |
| Dados_PNCP | pncp_scraper.py | ⚠️ Separado | Integrar no fluxo |
| le_andamento_PNCP | - | ❌ Faltando | Implementar |
| A2_leitura_SEI | - | ❌ Faltando | Implementar |
| NavegaProc_SEI | - | ❌ Faltando | Implementar |
| ajuste_pgc_anual_x_pgc | - | ❌ Faltando | Implementar |
| ajuste_pgc_anual_x_PNCP | - | ❌ Faltando | Implementar |
| A3_Cria_Contratacao | - | ❌ Faltando | Implementar |
| A4_Atualiza_Contratacao | - | ❌ Faltando | Implementar |
| nextPage | pgc_scraper_table.py | ⚠️ Diferente | Alinhar com VBA |
| ordena | - | ❌ Faltando | Implementar se necessário |

## Mapeamento de Índices de Colunas

### VBA (tabela HTML → Excel)

| Índice HTML | Campo | Coluna Excel | Valor |
|-------------|-------|--------------|-------|
| data(r, 4) | DFD | B | Formatado com 8 dígitos |
| data(r, 6) | Requisitante | C | Texto |
| data(r, 7) | Descrição | D | Texto |
| data(r, 8) | Valor | E | Currency |
| data(r, 9) | Situação | F | Texto |

### Python (tabela HTML → Banco)

| Índice HTML | Campo | Banco | Valor |
|-------------|-------|-------|-------|
| cols[0] | numero | ? | Sem formatação |
| cols[1] | titulo | ? | Texto |
| cols[2] | unidade | ? | Texto |
| cols[3] | situacao | ? | Texto |
| cols[4] | valor | ? | Texto (não convertido) |

**Gap:** Índices diferentes, campos diferentes, sem formatação.

## XPaths que Precisam Ser Adicionados ao Python

### Login e Navegação
```python
XPATHS_PGC = {
    # Login
    "login_url": "http://www.comprasnet.gov.br/seguro/loginPortal.asp",
    "btn_expand_governo": "//button[@class='br-button circle expand governo']",
    "btn_submit_login": "//button[@onclick='frmLoginGoverno_submit(); return false;']",
    "input_login": "txtLogin",  # ID
    "input_senha": "txtSenha",  # ID
    
    # Processamento
    "text_processando": "//div[@class='texto']/div[2][text()=' Estamos processando a sua solicitação. ']",
    
    # Menu PGC
    "span_pgc_title": "//span[text()='Planejamento e Gerenciamento de Contratações']",
    "div_pgc_access": "//div/p[2][text()='PGC']",
    "window_title": "Compras.gov.br - Fase Interna",
    
    # Spinner
    "spinner": "//body/app-root/ng-http-loader/div[@id='spinner']",
    
    # Seleção de PCA
    "dropdown_pca": "//p-dropdown[@placeholder='Selecione PCA']",
    "li_pca_ano": "//li[starts-with(@aria-label,'PCA {ano} -')]",
    "radio_minha_uasg": "minha-uasg",  # ID
    
    # Paginação
    "btn_last_page": "//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/button[@class='p-ripple p-element p-paginator-last p-paginator-element p-link ng-star-inserted']",
    "btn_first_page": "//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/button[@class='p-ripple p-element p-paginator-first p-paginator-element p-link ng-star-inserted']",
    "btn_next_page": "//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/button[@class='p-ripple p-element p-paginator-next p-paginator-element p-link']",
    "btns_pages": "//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/p-paginator/div/span[@class='p-paginator-pages ng-star-inserted']/button",
    "btn_current_page": "//button[@class='p-ripple p-element p-paginator-page p-paginator-element p-link ng-star-inserted p-highlight']",
    
    # Tabela
    "table_main": "//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/div[@class='p-datatable-wrapper']/table",
    "th_sort_dfd": "//div[@id='minhauasg']/app-artefato-list-resultado/div/div/div/p-table/div/div/table/thead/tr/th[4]",
    
    # DFD Detalhes
    "dfd_url_template": "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/artefatos/view?identificador=110511{dfd_id}&autoriza=e&tipo=DFD",
    "dfd_title": "//p[text()=' Detalhar Documento de Formalização da Demanda ']",
    "dfd_conclusao": "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[2]/div[1]/div[2]/p",
    "dfd_editor": "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[2]/div[1]/div[4]/p",
    "dfd_responsaveis_btn": "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[7]/button",
    "dfd_responsaveis_table": "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[8]/p-table/div/div/table",
    "dfd_justificativa": "//div[@class='conteudo-modal-rolante']/etp-fieldset/div/div[3]",
    
    # Botões
    "btn_fechar": "//span/button[text()='Fechar']",
}
```

## Padrões de Código que Precisam Ser Replicados

### 1. Padrão de Espera com Do While
**VBA:**
```vba
Do While Not driver.IsElementPresent(By.XPath("..."))
Loop
```

**Python equivalente:**
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WebDriverWait(driver, timeout).until(
    EC.presence_of_element_located((By.XPATH, "..."))
)
```

### 2. Padrão de Scroll antes de Click
**VBA:**
```vba
driver.FindElementByXPath("...").ScrollIntoView
driver.FindElementByXPath("...").Click
```

**Python equivalente:**
```python
element = driver.find_element(By.XPATH, "...")
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
element.click()
```

### 3. Padrão de Espera por Spinner
**VBA:**
```vba
testa_spinner
```

**Python equivalente:**
```python
from app.rpa.waiter import wait_spinner

wait_spinner(driver, "//body/app-root/ng-http-loader/div[@id='spinner']")
```

### 4. Padrão de Extração de Tabela
**VBA:**
```vba
Set tabela = driver.FindElementByXPath("...table").AsTable
Dim data(): data = tabela.data
For r = 1 To UBound(data, 1)
    ' Processa linha
Next
```

**Python equivalente:**
```python
table = driver.find_element(By.XPATH, "...table")
rows = table.find_elements(By.XPATH, ".//tbody/tr")
for row in rows:
    cols = row.find_elements(By.XPATH, "./td")
    # Processa colunas
```

### 5. Padrão de Formatação de DFD
**VBA:**
```vba
Right("000" & CStr(data(r, 4)), 8)
```

**Python equivalente:**
```python
dfd = str(data[3]).zfill(8)  # Preenche com zeros à esquerda até 8 caracteres
```

### 6. Padrão de Construção de URL de DFD
**VBA:**
```vba
enderecoDfd = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/artefatos/view?identificador=110511" & Right("00000" & Replace(Worksheets("PGC").Cells(i, 2).Value, "/", ""), 10) & "&autoriza=e&tipo=DFD"
```

**Python equivalente:**
```python
dfd_id = str(dfd_number).replace("/", "").zfill(10)
dfd_url = f"https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/artefatos/view?identificador=110511{dfd_id}&autoriza=e&tipo=DFD"
```

## Plano de Ação para Correção

### Prioridade 1 (Crítico)
1. ✅ Adicionar todos os XPaths específicos do VBA
2. ✅ Implementar fluxo completo de login (9 etapas)
3. ✅ Corrigir lógica de paginação (descobrir total, navegar corretamente)
4. ✅ Corrigir índices de colunas da tabela
5. ✅ Implementar formatação de DFD com 8 dígitos
6. ✅ Adicionar ordenação da tabela antes de extrair

### Prioridade 2 (Importante)
7. ✅ Implementar função `le_dfd()` completa
8. ✅ Adicionar scroll antes de cada click
9. ✅ Usar `wait_spinner` consistentemente
10. ✅ Implementar switch de janela

### Prioridade 3 (Desejável)
11. ⚠️ Implementar `corrige_falha_PGC()`
12. ⚠️ Integrar `Dados_PNCP()` no fluxo principal
13. ⚠️ Implementar funções de SEI (se necessário)
14. ⚠️ Implementar funções de criação/atualização de contratação (se necessário)

## Conclusão

O código Python atual está **estruturalmente melhor** (modular, tipado, com logging), mas está **funcionalmente incompleto** em relação ao VBA. Os principais gaps são:

1. **XPaths genéricos** em vez dos específicos do VBA
2. **Fluxo de login simplificado** sem todas as etapas de sincronização
3. **Lógica de paginação diferente** sem descobrir total de páginas primeiro
4. **Índices de colunas diferentes** na extração de tabelas
5. **Falta de formatação** de DFD com 8 dígitos
6. **Falta de ordenação** da tabela antes de extrair
7. **Função `le_dfd()` incompleta** sem extração de todos os campos
8. **Falta de integração** com PNCP e SEI no fluxo principal

Para replicar fielmente a lógica do VBA, precisamos **manter a estrutura modular do Python** mas **implementar exatamente a mesma lógica sequencial do VBA**, incluindo todos os XPaths específicos, todas as etapas de sincronização, e toda a lógica de negócio.
