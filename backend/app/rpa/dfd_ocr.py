"""
dfd_ocr.py

Funções principais:
- extract_text(image_path, lang='por', preprocess=True, tesseract_config=None)
    -> retorna {"text": str, "conf": float_or_None, "pages": int}

- ocr_and_save(image_path, out_dir='/tmp/ocr', basename=None, **kwargs)
    -> salva arquivo .txt em out_dir e retorna {"text_path": ..., "text": ..., "conf": ...}

Notas:
- Requer: pytesseract, pillow (PIL)
- Para PDFs: tenta usar pdf2image (requer poppler instalado no sistema)
- No container Docker, garanta tesseract instalado (apt-get install -y tesseract-ocr tesseract-ocr-por)
"""

from PIL import Image, ImageFilter, ImageOps
import pytesseract
import os
import time
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Try to import pdf2image if available
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except Exception:
    PDF2IMAGE_AVAILABLE = False

# Default Tesseract config, keep page segmentation mode 3 (default) unless override
DEFAULT_TESSERACT_CONFIG = "--psm 3"

# ---------------------------------------------------------------------
# Helpers de pré-processamento
# ---------------------------------------------------------------------
def _load_image(path: str):
    """
    Função _load_image:
    Executa a lógica principal definida nesta função.
    """
    """Load PIL image from path (supports common images)."""
    img = Image.open(path)
    # convert to RGB for consistency (some images can be palette)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return img

def _preprocess_image(img: Image.Image, do_binarize: bool = True) -> Image.Image:
    """
    Função _preprocess_image:
    Executa a lógica principal definida nesta função.
    """
    """
    Pre-process the image for OCR:
    - convert to grayscale
    - apply a slight sharpen / median filter if needed
    - optionally binarize (adaptive simple threshold)
    """
    # convert to grayscale
    img = img.convert("L")

    # optional: reduce noise with median filter
    try:
        img = img.filter(ImageFilter.MedianFilter(size=3))
    except Exception:
        pass

    # automatic contrast normalization
    try:
        img = ImageOps.autocontrast(img)
    except Exception:
        pass

    if do_binarize:
        # simple global threshold using histogram mean; keep it simple to avoid requiring OpenCV
        try:
            # compute a threshold based on image histogram
            hist = img.histogram()
            pixels = sum(hist)
            # mean brightness
            mean_brightness = sum(i * hist[i] for i in range(256)) / (pixels or 1)
            # set threshold slightly below mean to keep darker text
            threshold = int(max(60, min(180, mean_brightness * 0.9)))
            img = img.point(lambda p: 255 if p > threshold else 0)
        except Exception:
            pass

    return img

# ---------------------------------------------------------------------
# Core: extract text from a single PIL image
# ---------------------------------------------------------------------
def _tesseract_ocr_image(img: Image.Image, lang: str = "por", tesseract_config: Optional[str] = None) -> Dict:
    """
    Função _tesseract_ocr_image:
    Executa a lógica principal definida nesta função.
    """
    """
    Runs pytesseract on a PIL image and returns a dict with:
    - text (str)
    - conf (float | None) average confidence across recognized words (-1 ignored)
    """
    cfg = tesseract_config or DEFAULT_TESSERACT_CONFIG
    # get full text
    text = pytesseract.image_to_string(img, lang=lang, config=cfg)

    # try to extract word confidences via image_to_data
    conf = None
    try:
        data = pytesseract.image_to_data(img, lang=lang, config=cfg, output_type=pytesseract.Output.DICT)
        confs = []
        for c in data.get("conf", []):
            try:
                cval = float(c)
                # tesseract uses -1 for non-confidence items
                if cval >= 0:
                    confs.append(cval)
            except Exception:
                continue
        if confs:
            conf = float(sum(confs) / len(confs))
    except Exception:
        conf = None

    return {"text": text, "conf": conf}

# ---------------------------------------------------------------------
# Public: extract_text (supports image file or PDF)
# ---------------------------------------------------------------------
def extract_text(path: str, lang: str = "por", preprocess: bool = True, tesseract_config: Optional[str] = None, pdf_dpi: int = 200) -> Dict:
    """
    Função extract_text:
    Executa a lógica principal definida nesta função.
    """
    """
    Extract text from an image or PDF file.

    Returns:
      {
        "text": "<full text concatenated>",
        "conf": <average confidence across pages or None>,
        "pages": <num_pages_processed>
      }

    If path is a PDF and pdf2image is not available, raises RuntimeError.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    _, ext = os.path.splitext(path.lower())
    texts = []
    confs = []
    pages = 0

    if ext == ".pdf":
        if not PDF2IMAGE_AVAILABLE:
            raise RuntimeError("pdf2image não instalado ou poppler ausente. Instale pdf2image e poppler para suporte a PDF.")
        # convert pages to images
        pil_pages = convert_from_path(path, dpi=pdf_dpi)
        for pimg in pil_pages:
            pages += 1
            if preprocess:
                try:
                    img_pre = _preprocess_image(pimg, do_binarize=True)
                except Exception:
                    img_pre = pimg.convert("L")
            else:
                img_pre = pimg
            res = _tesseract_ocr_image(img_pre, lang=lang, tesseract_config=tesseract_config)
            texts.append(res["text"])
            if res["conf"] is not None:
                confs.append(res["conf"])
    else:
        # assume image
        img = _load_image(path)
        pages = 1
        if preprocess:
            try:
                img_pre = _preprocess_image(img, do_binarize=True)
            except Exception:
                img_pre = img.convert("L")
        else:
            img_pre = img
        res = _tesseract_ocr_image(img_pre, lang=lang, tesseract_config=tesseract_config)
        texts.append(res["text"])
        if res["conf"] is not None:
            confs.append(res["conf"])

    full_text = "\n\n---PAGE_BREAK---\n\n".join(t.strip() for t in texts if t is not None)
    avg_conf = float(sum(confs) / len(confs)) if confs else None

    return {"text": full_text, "conf": avg_conf, "pages": pages}

# ---------------------------------------------------------------------
# Convenience: run OCR and save result to txt (returns metadata)
# ---------------------------------------------------------------------
def ocr_and_save(path: str, out_dir: str = "/tmp/ocr", basename: Optional[str] = None, **kwargs) -> Dict:
    """
    Função ocr_and_save:
    Executa a lógica principal definida nesta função.
    """
    """
    Runs extract_text and saves to out_dir/<basename>.txt (basename defaults to filename timestamp).
    Returns dict: {"text_path": ..., "text": ..., "conf": ..., "pages": ...}
    """
    os.makedirs(out_dir, exist_ok=True)
    if basename:
        name = basename
    else:
        # create a safe basename from filename + timestamp
        fname = os.path.basename(path)
        safe = os.path.splitext(fname)[0]
        name = f"{safe}_{int(time.time())}"

    txt_path = os.path.join(out_dir, f"{name}.txt")

    res = extract_text(path, **kwargs)
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(res["text"] or "")
    except Exception as e:
        logger.warning(f"Não foi possível salvar arquivo txt em {txt_path}: {e}")

    return {"text_path": txt_path, "text": res["text"], "conf": res["conf"], "pages": res["pages"]}

# ---------------------------------------------------------------------
# If run as script, simple CLI
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python dfd_ocr.py <image_or_pdf_path> [out_dir]")
        sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ocr"
    outmeta = ocr_and_save(src, out_dir=out)
    print("Saved:", outmeta.get("text_path"))
    print("Conf:", outmeta.get("conf"))
    print("Pages:", outmeta.get("pages"))

def perform_ocr_on_dfd(resource_url: str) -> Optional[str]:
    """
    Função perform_ocr_on_dfd:
    Executa a lógica principal definida nesta função.
    """
    """
    Placeholder: given a URL to an image/pdf (DFD), fetch and perform OCR.
    Currently returns a stub string so the rest of pipeline can run.
    Replace with Tesseract / external OCR as needed.
    """
    logger.info(f"perform_ocr_on_dfd called for {resource_url}")
    # Simple stub — in real impl: download file, run OCR, return text
    return f"[OCR STUB for {resource_url}]"