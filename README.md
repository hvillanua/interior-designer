# Interior Design AI Assistant

AI-powered interior design assistant that analyzes room photos and provides personalized design recommendations.

## Features

- **Room Analysis**: Upload photos to get AI-powered analysis of your space
- **Design Recommendations**: Receive prioritized suggestions for furniture, lighting, decor, and more
- **AI Visualizations**: Generate edited room images showing proposed changes (via OpenRouter)
- **PDF Reports**: Professional reports with embedded images and recommendations
- **Multiple Interfaces**: Both CLI and Streamlit web UI

## Requirements

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) package manager
- [Claude Code](https://claude.ai/claude-code) CLI (authenticated)
- OpenRouter API key (for image generation, optional)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/interior-designer.git
cd interior-designer

# Install dependencies
make install
# or
uv sync
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

```bash
# Claude Code (uses existing auth, no key needed)
CLAUDE_MODEL=sonnet  # sonnet, opus, haiku

# OpenRouter API (for image generation only)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_IMAGE_MODEL=sourceful/riverflow-v2-fast-preview

# Output directory
OUTPUT_DIR=./output
```

## Usage

### Streamlit Web UI

```bash
make run
# or
uv run streamlit run src/interior_designer/app.py
```

Then open http://localhost:8501 in your browser.

### CLI

```bash
# Analyze a room photo
make cli ARGS="analyze room.jpg"

# With options
make cli ARGS="analyze room.jpg --style modern --budget medium --model sonnet"

# Skip image generation
make cli ARGS="analyze room.jpg --no-images"

# Output as markdown instead of PDF
make cli ARGS="analyze room.jpg --output-format md"

# Test PDF generation with mock data
make cli ARGS="test-pdf"

# List available models
make cli ARGS="models"
```

#### CLI Options

| Option | Description |
|--------|-------------|
| `--style, -s` | Preferred style (modern, rustic, minimalist, etc.) |
| `--budget, -b` | Budget level: low, medium, high |
| `--needs, -n` | Specific requirements |
| `--model, -m` | Claude model: sonnet (default), opus, haiku |
| `--output-format, -f` | Output format: pdf (default), md |
| `--no-images` | Skip AI image generation |

## Project Structure

```
interior-designer/
├── src/interior_designer/
│   ├── app.py              # Streamlit web interface
│   ├── cli.py              # Typer CLI interface
│   ├── config.py           # Configuration management
│   ├── pipeline.py         # Main analysis pipeline
│   ├── prompts.py          # LLM prompts
│   ├── models/
│   │   └── schemas.py      # Pydantic data models
│   ├── services/
│   │   ├── claude_code.py  # Claude Code subprocess wrapper
│   │   └── image_gen.py    # OpenRouter image generation
│   └── utils/
│       ├── image.py        # Image utilities
│       ├── markdown.py     # Markdown report generation
│       └── pdf.py          # PDF report generation
├── output/                 # Generated reports (gitignored)
├── pyproject.toml
├── Makefile
└── .env.example
```

## Output

Each analysis creates a session folder in `output/` containing:

- `report.pdf` - Professional PDF report with recommendations
- `report.md` - Markdown version of the report
- `analysis.json` - Raw analysis data
- `original/` - Uploaded images
- `generated/` - AI-generated visualizations (if enabled)

## Models

### Claude Models

| Model | Description |
|-------|-------------|
| `sonnet` | Balanced performance and cost (default) |
| `opus` | Most capable, best for complex analysis |
| `haiku` | Fastest, good for quick iterations |

### Image Generation Models

Configure in `.env` via `OPENROUTER_IMAGE_MODEL`:

| Model | Cost | Notes |
|-------|------|-------|
| `sourceful/riverflow-v2-fast-preview` | $0.03/image | Fast, good quality |
| `black-forest-labs/flux.2-pro` | $0.03/megapixel | High quality |
| `google/gemini-3-pro-image-preview` | $0.13-0.24/image | Google's model |

## Development

```bash
# Install dependencies
make install

# Run Streamlit
make run

# Run CLI
make cli ARGS="--help"

# Clean output files
make clean
```

## License

MIT
