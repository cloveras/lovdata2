# Legal notice

This repository contains **tools** for working with the publicly available
Lovdata datasets (laws and central regulations).

The project:

- **does not** redistribute Lovdata’s own XML/HTML files,
- **does not** redistribute Lovdata’s consolidated or edited versions of laws,
- **does not** redistribute Lovdata’s editorial markup, structure or metadata.

Raw data downloaded from Lovdata is stored under `raw/` and is intended for
local use only. The `raw/` directory MUST NOT be committed to any public
repository or redistributed.

The processed dataset in `data/` contains:

- plain text extracted from Lovdata’s public tarballs,
- normalized whitespace,
- minimal structural metadata (IDs, titles, dates, ministries, section
  structure),
- links back to Lovdata as the authoritative source.

Laws and regulations themselves are not protected by copyright, but Lovdata’s
consolidation, markup and editorial contributions are. This project aims to
respect that distinction.

Nothing in this repository is legal advice. For authoritative versions, see:

- https://lovdata.no/