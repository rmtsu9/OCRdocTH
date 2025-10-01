# OCR Tax Invoice System - AI Agent Guidelines

## 🏗️ Architecture Overview

**Multi-layered OCR Pipeline:**
- `desktop_gui.py`: Tkinter GUI with login system, 4-panel dashboard (file selection, OCR settings, structured data display, validation summary)
- `OCR.py`: Orchestrates PDF→Image→OCR→Parser→LLM pipeline with engine selection (Tesseract/EasyOCR/PaddleOCR)
- `tax_invoice_parser.py`: Thai-specific regex patterns for 27 tax invoice fields (dates, amounts, tax IDs, company names)
- `llm_processor.py`: Optional AI post-processing with 7 features (mapping, normalization, validation, ensemble reasoning)
- `excel_exporter.py`: Timestamped Excel export with 3 sheets (data, summary, raw OCR text)

**Key Design Patterns:**
- **Graceful Degradation**: All AI/LLM features are optional with rule-based fallbacks
- **Path Handling**: Use `pathlib.Path` consistently, check `Path(__file__).parent` for relative paths
- **Thai Language Support**: Buddhist calendar dates (2568 = 2025), Thai month names, tax ID formats
- **Threading**: GUI operations use threading to prevent freezing during OCR processing

## 🔧 Development Workflows

**Building for Distribution:**
```bash
# Use the automated build system (recommended)
python build_exe.py
# OR
build_exe.bat

# Manual build (advanced users)
pyi-makespec --onedir --windowed --name="OCR_TaxInvoice" desktop_gui.py
# Edit OCR_TaxInvoice.spec to add data files and hidden imports
pyinstaller OCR_TaxInvoice.spec --clean --noconfirm
```

**Testing OCR Accuracy:**
```python
# Compare OCR engines with/without LLM
python test_llm_ocr.py

# Test specific invoice parsing
from tax_invoice_parser import ThaiTaxInvoiceParser
parser = ThaiTaxInvoiceParser()
result = parser.parse_ocr_text(ocr_text)
```

**Adding New Tax Invoice Fields:**
1. Add field name to `EXPECTED_FIELDS` in `tax_invoice_parser.py`
2. Create regex pattern in `_compile_patterns()`
3. Add extraction logic in appropriate method
4. Update validation colors in GUI

## 📋 Code Conventions

**File Structure Pattern:**
```
# Main components in root
Lib/           # External binaries (Tesseract, Poppler)
Model/         # AI models for OCR engines
Export/ref/    # Excel template files
dist/          # Build output (generated)
```

**Import Strategy:**
```python
# Optional imports with fallbacks
try:
    from llm_processor import LLMProcessor
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Standard library first, then third-party, then local
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
```

**Error Handling:**
```python
# Use logging extensively
logger = logging.getLogger(__name__)
try:
    # risky operation
except Exception as e:
    logger.error(f"Operation failed: {e}")
    # graceful fallback
```

**Thai Text Processing:**
- Use regex with Thai character classes `[ก-๙]`
- Handle Buddhist years: `int(thai_year) - 543`
- Support multiple phone formats: `0[2-9][\s\-]*\d{3}[\s\-]*\d{4}`

## 🔗 Integration Points

**External Dependencies:**
- **Tesseract OCR**: `Lib/Tesseract-OCR/` (bundled in .exe)
- **Poppler**: `Lib/poppler-25.07.0/` (for PDF processing)
- **AI Models**: `Model/` directory (EasyOCR/PaddleOCR models)
- **Credentials**: `credentials.json` (login system)

**API Integration:**
- OpenAI GPT-4o-mini (optional, with API key)
- Anthropic Claude (optional, with API key)
- Falls back to rule-based processing if APIs unavailable

**Data Flow:**
```
File Input → PDF2Image → OCR Engine → Thai Parser → LLM Post-process → Validation → Excel Export
     ↓           ↓           ↓          ↓              ↓              ↓           ↓
   GUI      pdf2image  Tesseract/  tax_invoice_  llm_processor  Color-coded  excel_exporter
   Select   convert    EasyOCR     parser.py     .py           UI feedback   .py
```

## 🎯 Common Tasks

**Adding OCR Engine:**
1. Add engine option to GUI dropdown in `desktop_gui.py`
2. Implement engine logic in `OCR.py` `process_image()`
3. Add engine-specific imports with try/except
4. Update `build_exe.py` hidden imports if needed

**Modifying Tax Fields:**
- Edit `EXPECTED_FIELDS` in `tax_invoice_parser.py`
- Add regex patterns in `_compile_patterns()`
- Implement extraction in `_extract_*()` methods
- Update GUI display in `create_structured_data_tab()`

**LLM Integration:**
- Use `LLMProcessor` class with provider/model parameters
- Handle API failures gracefully
- Test with `test_llm_ocr.py` before deployment

## ⚠️ Critical Notes

- **Path Resolution**: Always use `Path(__file__).parent` for relative paths in packaged .exe
- **Threading**: GUI operations must use threading to prevent UI freezing
- **Memory Management**: Large PDF files may need chunked processing
- **Character Encoding**: Use UTF-8 for all file operations, especially Thai text
- **Build Dependencies**: PyInstaller spec file must include all external binaries and models</content>
<parameter name="filePath">c:\Users\Administrator\Desktop\home\OCR\.github\copilot-instructions.md