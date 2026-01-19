"""
schemas.py
Define os contratos de dados (Pydantic models) para o projeto.
Implementação do Passo 5: Contrato de dados PNCP fiel ao VBA.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class PNCPItemSchema(BaseModel):
    """
    Representa exatamente o contrato de dados produzido pela coleta PNCP.
    Mapeado diretamente do inventário de campos do VBA (Colunas A a I).
    """
    col_a_contratacao: str = Field(..., description="ID da Contratação (Coluna A)")
    col_b_descricao: str = Field(..., description="Descrição do Objeto (Coluna B)")
    col_c_categoria: str = Field(..., description="Categoria da Contratação (Coluna C)")
    col_d_valor: float = Field(..., description="Valor da Contratação (Coluna D - CDbl)")
    col_e_inicio: Optional[date] = Field(None, description="Data de Início (Coluna E - CDate)")
    col_f_fim: Optional[date] = Field(None, description="Data de Fim (Coluna F - CDate)")
    col_g_status: str = Field(..., description="Status da Contratação (Coluna G)")
    col_h_status_tipo: str = Field(..., description="Tipo de Status (Coluna H)")
    col_i_dfd: str = Field(..., description="DFD Formatado (Coluna I - Format)")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "col_a_contratacao": "12345/2025",
                "col_b_descricao": "Aquisição de material de escritório",
                "col_c_categoria": "Bens",
                "col_d_valor": 1500.50,
                "col_e_inicio": "2025-01-01",
                "col_f_fim": "2025-12-31",
                "col_g_status": "APROVADA",
                "col_h_status_tipo": "APROVADA",
                "col_i_dfd": "123/2025"
            }
        }

class PNCPCollectionResponse(BaseModel):
    """Resposta final da coleta PNCP contendo a lista de itens coletados."""
    status: str
    total_itens: int
    itens: List[PNCPItemSchema]
    data_coleta: date
