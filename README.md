# lovdata2

This project is a rapid prototype showing how the Lovdata API might look if redesigned
according to modern REST best practices.
It is not the official Lovdata API — see the real version here:
https://api.lovdata.no/swagger

The goal is to illustrate how Norwegian laws and regulations could be exposed through a
clean, predictable, developer-friendly REST interface.

The repository also includes tools for downloading and processing Lovdata’s publicly
available datasets. These scripts generate a simplified, machine-readable dataset without
Lovdata’s editorial markup, suitable for research, indexing, or experimentation with
alternative API designs.

## API documentation

ReDoc version of the OpenAPI specification:

https://cloveras.github.io/lovdata2/api.html

## Workflow

```bash
python3 scripts/download_raw.py
python3 scripts/prepare_xml.py
python3 scripts/build_dataset.py
