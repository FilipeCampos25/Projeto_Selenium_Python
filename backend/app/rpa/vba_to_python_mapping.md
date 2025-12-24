Mapeamento aproximado entre Subs/Functions do Módulo1.bas e os módulos Python gerados:
- A_Loga_Acessa_PGC -> pgc_scraper.login_pgc
- A1_Demandas_DFD_PCA -> pgc_scraper.collect_for_num
- A3_Cria_Contratacao -> services.pncp_service (create path in DB)
- A4_Atualiza_Contratacao -> services.pncp_service (update path)
- A5_DownloadChromeDriver -> (not needed; using selenium standalone)
- A6_DownloadPNCP -> pncp_scraper.download_pncp
- A7_busca_DFD_SEI -> pgc_scraper.collect_for_num (dfd fetch)
- le_imagem_dfd + OCR -> rpa.dfd_ocr.extract_text
