# Dreamscape Memory - Whiteout Survival

Windows automation tools for recognizing words in *Whiteout Survival* with
OCR and clicking the corresponding locations on screen.

## Project files

- `main.py` - runs OCR, matches detected words against a map file, and clicks
  the configured coordinates.
- `collect_words_temp.py` - helps collect word labels and their screen
  coordinates.
- `maps/` - map files containing word labels and click coordinates.

## Requirements

- Windows
- Python 3.13 or newer
- Tesseract OCR
- The Python packages listed in `requirements.txt`

The scripts currently expect Tesseract at:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

If Tesseract is installed elsewhere, update `pytesseract.pytesseract.tesseract_cmd`
in both Python scripts.

## Installation

Create and activate a virtual environment, then install the Python
dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Running the main script

Select the map file in `main.py`:

```python
ACTIVE_WORDS_FILE = "maps/conquering_sword.txt"
```

Then run:

```powershell
python main.py
```

The script waits five seconds before starting. Press `F8` or `Ctrl+C` to stop
it.

## Collecting word coordinates

Run:

```powershell
python collect_words_temp.py
```

The collector writes captured labels and coordinates to `collect_words.txt`.
This file is treated as local working data and is ignored by Git. Copy useful
entries into an appropriate file in `maps/` when a map is ready.

## Notes

The scripts use fixed screen coordinates and an OCR region, so
`OCR_REGION` and map coordinates may need to be adjusted for a different
display setup.
