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
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            logger.info(f"Criando novo arquivo Excel: {self.file_path}")
            wb = Workbook()
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
            # Colunas: A:Contratação, B:Descrição, C:Categoria, D:Valor, E:Início, F:Fim, G:Status, H:Status_Tipo, I:DFD
            ws_pncp = wb["PNCP"]
            headers_pncp = ["Contratação", "Descrição", "Categoria", "Valor", "Início", "Fim", "Status", "Status_Tipo", "DFD"]
            for col, header in enumerate(headers_pncp, 1):
                ws_pncp.cell(row=1, column=col, value=header)

            wb.save(self.file_path)

    def update_pgc_sheet(self, data: List[Dict[str, Any]]):
        """Atualiza a aba PGC seguindo a lógica do VBA."""
        try:
            wb = load_workbook(self.file_path)
            ws = wb["PGC"]
            for item in data:
                dfd = str(item.get("dfd", "")).strip()
                if not dfd: continue
                found_row = None
                for row in range(2, ws.max_row + 1):
                    if str(ws.cell(row=row, column=2).value).strip() == dfd:
                        found_row = row
                        break
                target_row = found_row if found_row else ws.max_row + 1
                ws.cell(row=target_row, column=1, value=item.get("pag", 1))
                ws.cell(row=target_row, column=2, value=dfd)
                ws.cell(row=target_row, column=3, value=item.get("requisitante"))
                ws.cell(row=target_row, column=4, value=item.get("descricao"))
                ws.cell(row=target_row, column=5, value=item.get("valor"))
                ws.cell(row=target_row, column=6, value=item.get("situacao"))
            wb.save(self.file_path)
            logger.info(f"Aba PGC atualizada.")
        except Exception as e:
            logger.error(f"Erro ao atualizar aba PGC: {e}")

    def update_pncp_sheet(self, data: List[Dict[str, Any]]):
        """
        Atualiza a aba PNCP seguindo fielmente o mapeamento de colunas do VBA (A a I).
        """
        try:
            wb = load_workbook(self.file_path)
            ws = wb["PNCP"]
            for entry in data:
                contratacao = str(entry.get("col_a_contratacao", "")).strip()
                if not contratacao: continue
                
                found_row = None
                for row in range(2, ws.max_row + 1):
                    if str(ws.cell(row=row, column=1).value).strip() == contratacao:
                        found_row = row
                        break
                
                target_row = found_row if found_row else ws.max_row + 1
                
                # Mapeamento fiel às colunas do VBA
                ws.cell(row=target_row, column=1, value=entry.get("col_a_contratacao"))
                ws.cell(row=target_row, column=2, value=entry.get("col_b_descricao"))
                ws.cell(row=target_row, column=3, value=entry.get("col_c_categoria"))
                ws.cell(row=target_row, column=4, value=entry.get("col_d_valor"))
                ws.cell(row=target_row, column=5, value=entry.get("col_e_inicio"))
                ws.cell(row=target_row, column=6, value=entry.get("col_f_fim"))
                ws.cell(row=target_row, column=7, value=entry.get("col_g_status"))
                ws.cell(row=target_row, column=8, value=entry.get("col_h_status_tipo"))
                ws.cell(row=target_row, column=9, value=entry.get("col_i_dfd"))

            wb.save(self.file_path)
            logger.info("Aba PNCP atualizada com sucesso (Mapeamento VBA).")
        except Exception as e:
            logger.error(f"Erro ao atualizar aba PNCP no Excel: {e}")

    def sync_to_geral(self):
        """Sincroniza dados entre PGC e Geral seguindo a lógica do VBA."""
        try:
            wb = load_workbook(self.file_path)
            if "PGC" not in wb.sheetnames or "Geral" not in wb.sheetnames:
                return
            ws_pgc = wb["PGC"]
            ws_geral = wb["Geral"]
            for r_pgc in range(2, ws_pgc.max_row + 1):
                dfd = ws_pgc.cell(row=r_pgc, column=2).value
                if not dfd: continue
                found_row_geral = None
                for r_geral in range(2, ws_geral.max_row + 1):
                    if ws_geral.cell(row=r_geral, column=7).value == dfd:
                        found_row_geral = r_geral
                        break
                target_row = found_row_geral if found_row_geral else ws_geral.max_row + 1
                ws_geral.cell(row=target_row, column=1, value=ws_pgc.cell(row=r_pgc, column=1).value)
                ws_geral.cell(row=target_row, column=6, value=str(dfd)[-4:] if dfd else "")
                ws_geral.cell(row=target_row, column=7, value=dfd)
                ws_geral.cell(row=target_row, column=8, value=ws_pgc.cell(row=r_pgc, column=3).value)
                ws_geral.cell(row=target_row, column=9, value=ws_pgc.cell(row=r_pgc, column=4).value)
                ws_geral.cell(row=target_row, column=10, value=ws_pgc.cell(row=r_pgc, column=5).value)
                ws_geral.cell(row=target_row, column=11, value=ws_pgc.cell(row=r_pgc, column=6).value)
            wb.save(self.file_path)
            logger.info("Sincronização com aba Geral concluída.")
        except Exception as e:
            logger.error(f"Erro na sincronização Geral: {e}")
