# lovdata2

Tools for downloading and preparing the publicly available Lovdata datasets
(laws and central regulations).  
This project produces a clean, machine-readable dataset without Lovdata’s
editorial markup, suitable for research, indexing, and API use.

## Workflow

```bash
python3 scripts/download_raw.py
python3 scripts/prepare_xml.py
python3 scripts/build_dataset.py
