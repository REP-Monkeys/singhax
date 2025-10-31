# Tesseract OCR Setup Guide

This guide explains how to install and configure Tesseract OCR for the travel insurance application.

## System Requirements

Tesseract OCR requires system-level installation before Python packages can be used.

### macOS

```bash
# Install Tesseract and Poppler (for PDF support)
brew install tesseract poppler

# Verify installation
tesseract --version
```

### Linux (Ubuntu/Debian)

```bash
# Install Tesseract OCR and Poppler
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils libtesseract-dev

# Verify installation
tesseract --version
```

### Linux (CentOS/RHEL)

```bash
# Install Tesseract OCR and Poppler
sudo yum install -y tesseract poppler-utils

# Verify installation
tesseract --version
```

### Windows

1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and note the installation path (default: `C:\Program Files\Tesseract-OCR`)
3. Add Tesseract to your PATH environment variable
4. Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases
5. Extract and add to PATH

### Docker

Add to your Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*
```

## Language Data Files

Tesseract requires language data files for OCR processing.

### Default Installation

English (`eng`) is included by default with Tesseract.

### Additional Languages

Install additional language packs:

**macOS:**
```bash
brew install tesseract-lang
```

**Linux:**
```bash
# Download tessdata files
wget https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata
sudo mv chi_sim.traineddata /usr/share/tesseract-ocr/5/tessdata/

# Or install package (if available)
sudo apt-get install tesseract-ocr-<lang>
# Examples: tesseract-ocr-fra, tesseract-ocr-spa, tesseract-ocr-chi-sim
```

**Windows:**
Download `.traineddata` files from: https://github.com/tesseract-ocr/tessdata
Place them in: `C:\Program Files\Tesseract-OCR\tessdata`

## Python Dependencies

After system installation, install Python packages:

```bash
cd apps/backend
pip install pytesseract Pillow pdf2image
```

## Configuration

### Path Configuration (if needed)

If Tesseract is not in your PATH, configure it in Python:

```python
import pytesseract

# macOS (Homebrew default)
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

# Linux (typical)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Verification

Test the installation:

```bash
# System level
tesseract --version

# Python level
python -c "import pytesseract; print('✓ OCR ready')"
python -c "from PIL import Image; print('✓ Pillow ready')"
python -c "from pdf2image import convert_from_bytes; print('✓ PDF support ready')"
```

## Troubleshooting

### Tesseract not found

- Verify Tesseract is installed: `tesseract --version`
- Check PATH: `which tesseract` (macOS/Linux) or check Windows PATH
- Set `pytesseract.pytesseract.tesseract_cmd` if needed

### PDF conversion fails

- Verify Poppler is installed: `pdftoppm -h`
- Check PDF2Image can find Poppler
- For Windows, ensure Poppler binaries are in PATH

### Language data not found

- Verify language data files exist in tessdata directory
- Check file permissions
- Ensure correct language code (e.g., 'eng', 'chi_sim')

## Supported Formats

- **Images**: PNG, JPEG, TIFF, BMP
- **Documents**: PDF (converted to images)
- **Max file size**: 10MB (configurable)

## Performance Tips

- For better accuracy, preprocess images (grayscale, contrast enhancement)
- Use appropriate language codes for multilingual documents
- For large PDFs, process pages individually to manage memory

