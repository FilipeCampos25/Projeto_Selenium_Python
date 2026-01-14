import os
import logging
from typing import List, Dict, Any
from openpyxl import load_workbook, Workbook
from openpyxl.styles import NamedStyle
from datetime import datetime

logger = logging.getLogger(__name__)

class ExcelPersistence:
    """
    Gerencia a persistência de dados no arquivo Excel seguindo fielmente a lógica do VBA original.
    """
    def __init__(self, file_path: str = "PGC_2025.xlsm"):
        # No ambiente Linux/Docker, o arquivo pode não ter a extensão .xlsm funcional com macros,
        # mas manteremos o nome para compatibilidade. Se não existir, criamos um .xlsx.
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            logger.info(f"Criando novo arquivo Excel: {self.file_path}")
            wb = Workbook()
            # Criar as abas principais conforme o VBA
            if "Sheet" in wb.sheetnames:
                wb["Sheet"].title = "PGC"
            else:
                wb.create_sheet("PGC")
            
            wb.create_sheet("PNCP")
            wb.create_sheet("Geral")
            
            # Inicializar cabeçalhos da aba PGC (VBA linhas 333-343)
            ws_pgc = wb["PGC"]
            headers_pgc = ["Pag", "DFD", "Requisitante", "Descrição", "Valor", "Situação", "Conclusão", "Editor", "Responsáveis", "PTA", "Justificativa"]
            for col, header in enumerate(headers_pgc, 1):
                ws_pgc.cell(row=1, column=col, value=header)
            
            # Inicializar cabeçalhos da aba PNCP (VBA linhas 2157-2167)
            ws_pncp = wb["PNCP"]
            headers_pncp = ["Contratação", "Descrição", "Categoria", "Valor", "Início", "Fim", "Status", "PGC", "DFD", "Status", "Tipo"]
            for col, header in enumerate(headers_pncp, 1):
                ws_pncp.cell(row=1, column=col, value=header)

            wb.save(self.file_path)

    def update_pgc_sheet(self, data: List[Dict[str, Any]]):
        """
        Atualiza a aba PGC seguindo a lógica das linhas 408-438 e 618-669 do VBA.
        Lógica: Se o DFD não existe, insere. Se existe, atualiza (Idempotente).
        """
        try:
            wb = load_workbook(self.file_path)
            if "PGC" not in wb.sheetnames:
                wb.create_sheet("PGC")
            ws = wb["PGC"]

            # Mapeamento de colunas baseado no VBA
            # Col 1: Pag, 2: DFD, 3: Requisitante, 4: Descrição, 5: Valor, 6: Situação
            
            for item in data:
                dfd = str(item.get("dfd", "")).strip()
                if not dfd: continue

                # Procurar se o DFD já existe (VBA linha 633)
                found_row = None
                for row in range(2, ws.max_row + 1):
                    cell_value = str(ws.cell(row=row, column=2).value).strip()
                    if cell_value == dfd:
                        found_row = row
                        break
                
                if found_row:
                    # Atualiza (VBA linhas 2585-2622)
                    ws.cell(row=found_row, column=3, value=item.get("requisitante"))
                    ws.cell(row=found_row, column=4, value=item.get("descricao"))
                    ws.cell(row=found_row, column=5, value=item.get("valor"))
                    ws.cell(row=found_row, column=6, value=item.get("situacao"))
                else:
                    # Insere na próxima linha disponível (VBA linha 413/623)
                    new_row = ws.max_row + 1
                    ws.cell(row=new_row, column=1, value=item.get("pag", 1))
                    ws.cell(row=new_row, column=2, value=dfd)
                    ws.cell(row=new_row, column=3, value=item.get("requisitante"))
                    ws.cell(row=new_row, column=4, value=item.get("descricao"))
                    ws.cell(row=new_row, column=5, value=item.get("valor"))
                    ws.cell(row=new_row, column=6, value=item.get("situacao"))

            wb.save(self.file_path)
            logger.info(f"Aba PGC atualizada com {len(data)} itens.")
        except Exception as e:
            logger.error(f"Erro ao atualizar aba PGC no Excel: {e}")

    def update_pncp_sheet(self, data: List[Dict[str, Any]]):
        """
        Atualiza a aba PNCP seguindo a lógica das linhas 2249-2512 do VBA.
        """
        try:
            wb = load_workbook(self.file_path)
            if "PNCP" not in wb.sheetnames:
                wb.create_sheet("PNCP")
            ws = wb["PNCP"]

            for item in data:
                # O PNCP no Python pode vir como uma lista de resultados ou um dict
                # Se for o resultado bruto do scraper, precisamos extrair os itens
                items_to_process = []
                if isinstance(item, dict) and "raw" in item: # Formato do collect_page_data
                    items_to_process = [item]
                elif isinstance(item, list):
                    items_to_process = item
                else:
                    items_to_process = [item]

                for entry in items_to_process:
                    # Tenta identificar um ID único para o PNCP (Contratação ou DFD)
                    # No VBA, a chave parece ser a coluna I (DFD) ou A (Contratação)
                    contratacao = str(entry.get("contratacao", entry.get("index", ""))).strip()
                    
                    found_row = None
                    for row in range(2, ws.max_row + 1):
                        if str(ws.cell(row=row, column=1).value).strip() == contratacao:
                            found_row = row
                            break
                    
                    target_row = found_row if found_row else ws.max_row + 1
                    
                    # Mapeamento simplificado baseado no VBA
                    ws.cell(row=target_row, column=1, value=contratacao)
                    ws.cell(row=target_row, column=2, value=entry.get("descricao", entry.get("raw", "")))
                    ws.cell(row=target_row, column=4, value=entry.get("valor", 0))
                    ws.cell(row=target_row, column=7, value=entry.get("status", "COLETADO"))
                    ws.cell(row=target_row, column=9, value=entry.get("dfd", ""))

            wb.save(self.file_path)
            logger.info("Aba PNCP atualizada.")
        except Exception as e:
            logger.error(f"Erro ao atualizar aba PNCP no Excel: {e}")

    def sync_to_geral(self):
        """
        Sincroniza dados entre PGC e Geral seguindo a lógica das linhas 2561-2675 do VBA.
        """
        try:
            wb = load_workbook(self.file_path)
            if "PGC" not in wb.sheetnames or "Geral" not in wb.sheetnames:
                return
            
            ws_pgc = wb["PGC"]
            ws_geral = wb["Geral"]
            
            # Cabeçalhos Geral se estiver vazio
            if ws_geral.max_row == 1 and not ws_geral.cell(row=1, column=1).value:
                headers = ["Pag", "Unidade", "Ano", "Tipo", "Objeto", "DFD_Curto", "DFD", "Requisitante", "Descrição", "Valor", "Situação", "Conclusão", "Editor", "Responsáveis"]
                for col, h in enumerate(headers, 1):
                    ws_geral.cell(row=1, column=col, value=h)

            for r_pgc in range(2, ws_pgc.max_row + 1):
                dfd = ws_pgc.cell(row=r_pgc, column=2).value
                if not dfd: continue
                
                # Buscar no Geral (Coluna G é DFD no VBA 2573)
                found_row_geral = None
                for r_geral in range(2, ws_geral.max_row + 1):
                    if ws_geral.cell(row=r_geral, column=7).value == dfd:
                        found_row_geral = r_geral
                        break
                
                target_row = found_row_geral if found_row_geral else ws_geral.max_row + 1
                
                # Atualiza/Insere (VBA 2581-2665)
                ws_geral.cell(row=target_row, column=1, value=ws_pgc.cell(row=r_pgc, column=1).value) # Pag
                ws_geral.cell(row=target_row, column=6, value=str(dfd)[-4:] if dfd else "") # DFD Curto
                ws_geral.cell(row=target_row, column=7, value=dfd)
                ws_geral.cell(row=target_row, column=8, value=ws_pgc.cell(row=r_pgc, column=3).value) # Requisitante
                ws_geral.cell(row=target_row, column=9, value=ws_pgc.cell(row=r_pgc, column=4).value) # Descrição
                ws_geral.cell(row=target_row, column=10, value=ws_pgc.cell(row=r_pgc, column=5).value) # Valor
                ws_geral.cell(row=target_row, column=11, value=ws_pgc.cell(row=r_pgc, column=6).value) # Situação
                ws_geral.cell(row=target_row, column=12, value=ws_pgc.cell(row=r_pgc, column=7).value) # Conclusão
                ws_geral.cell(row=target_row, column=13, value=ws_pgc.cell(row=r_pgc, column=8).value) # Editor
                ws_geral.cell(row=target_row, column=14, value=ws_pgc.cell(row=r_pgc, column=9).value) # Responsáveis

            wb.save(self.file_path)
            logger.info("Sincronização com aba Geral concluída.")
        except Exception as e:
            logger.error(f"Erro na sincronização Geral: {e}")
