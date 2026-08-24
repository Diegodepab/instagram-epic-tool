# CircleScope — Instagram Network Analyzer

CircleScope turns an official Instagram data export into an understandable relationship map. It calculates followers, followed accounts, mutual relationships, people who only follow you, and people who do not follow you back.

The primary export-analysis flow never asks for an Instagram password, does not scrape Instagram, and makes no external API calls. Uploaded ZIP files are processed temporarily and are not retained by the application. A separate, visibly experimental lab can be enabled by an operator for bounded access to an owned or expressly authorized account.

> [!WARNING]
> The laboratory is informational, educational, and defensive. Use it only with accounts you own or have explicit permission to assess, at your own risk. Unofficial automation may violate Instagram's terms even when the underlying activity is otherwise lawful. Public visibility is not consent for mass collection. Read the [full disclaimer](DISCLAIMER.md).

The interface includes a fictional demo, exact relationship metrics, a performance-aware interactive graph, multiple authorized ZIP merging, relationship provenance and dates when Meta provides them, complete paginated lists, search, category filters, and CSV export.

## Start with Docker

Requirements: Docker Engine with Docker Compose.

```bash
git clone https://github.com/Diegodepab/instagram-epic-tool.git
cd instagram-epic-tool
docker compose up --build -d
```

Open `http://localhost:8080`. Stop the application with:

```bash
docker compose down
```

See [User Guide](docs/USER_GUIDE.md) for obtaining and importing an Instagram export, and [Deployment Guide](docs/DEPLOYMENT.md) for development and production instructions.

## Repository Layout

```text
.
├── src/
│   ├── backend/             # FastAPI, parser, analysis and temporary sessions
│   └── frontend/            # React, TypeScript and interactive graph
├── tests/                   # Backend unit tests
├── docs/                    # User, deployment, security and architecture docs
├── lab/                     # Isolated third-party sources and risk experiments
├── compose.yaml             # One-command local deployment
└── .github/workflows/       # CI and automated releases
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/backend/requirements.txt
pip install ./lab/instagrapi
PYTHONPATH=src uvicorn backend.main:app --reload
```

In another terminal:

```bash
cd src/frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Experimental Lab

The risk screen integrates both repositories under `lab/` with different trust boundaries:

- `instagrapi` is installed from the vendored source during the backend image build. Its own-account connector is disabled by default. Enable it locally with `ENABLE_INSTAGRAPI_LAB=true docker compose up --build`; credentials live only for the duration of one request and are never dumped to disk.
- `Instagram-` is integrated only through a defensive static analyzer. The application reads its Python syntax and hashes files, but never imports or executes its brute-force code and never grants it network access.

See [Lab Risk Assessment](docs/LAB_RISK_ASSESSMENT.md) for limits and promotion criteria. Do not enable the experimental connector on a public deployment.

## Verification

```bash
PYTHONPATH=src python -m unittest discover -s tests -v

cd src/frontend
npm run lint
npm run build
```

## Documentation

- [User Guide](docs/USER_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Security and Privacy](docs/SECURITY.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Project Governance](docs/PROJECT_GOVERNANCE.md)
- [Lab Risk Assessment](docs/LAB_RISK_ASSESSMENT.md)
- [Disclaimer](DISCLAIMER.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [Contributing](CONTRIBUTING.md)

## Data Scope

An Instagram export describes the direct relationships of the account that generated it. It does not contain the full follower lists of other profiles. Additional exports can be merged only when their owners provided them with consent; those profiles become genuinely expandable through their imported connections.

## License

MIT — see [LICENSE](LICENSE).
