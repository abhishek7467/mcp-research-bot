# MCP Server for Daily Research + News Newspaper

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated **Model Context Protocol (MCP) Server** that discovers, scrapes, processes, and summarizes research papers and news articles to generate a beautiful daily newspaper in HTML, PDF, and JSON formats.

## 🌟 Features

- **Multi-Source Discovery**: Automatically discovers content from:
  - arXiv, PubMed, Crossref, bioRxiv (research papers)
  - Journal RSS feeds (Nature, Science, etc.)
  - News sources (MIT Tech Review, Ars Technica, Google News)

- **AI-Powered Summarization**: Uses **Google Gemini** and **OpenAI GPT-4** to generate:
  - Compelling headlines
  - TL;DR summaries
  - Key bullet points
  - Significance analysis
  - Limitations

- **Smart Processing**:
  - Deduplication across sources
  - Relevance scoring using embeddings
  - Recency and credibility weighting
  - Automatic section assignment

- **Beautiful Newspaper Output**:
  - Professional HTML design
  - PDF generation
  - JSON metadata export
  - Multiple sections (Top Research, News, Tools, etc.)

- **Legal & Ethical**:
  - Respects `robots.txt`
  - Rate limiting per domain
  - Fair use compliance
  - Metadata-only for paywalled content

## 📋 Requirements

- Python 3.8+
- OpenAI API key (for embeddings and GPT-4)
- Google Gemini API key (for summarization)
- Optional: PostgreSQL, Elasticsearch, wkhtmltopdf

## 🚀 Quick Start

### 1. Clone and Setup

```bash

git clone https://github.com/abhishek7467/mcp-research-bot.git

cd "mcp-research-bot"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

**Required API Keys:**
```env
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
CROSSREF_EMAIL=your-email@example.com
```

### 3. Configure Topics and Sources

Edit `config/config.yaml`:

```yaml
topics:
  - "machine learning"
  - "quantum computing"
  - "CRISPR gene editing"
```

### 4. Run Your First Generation

```bash
# Single run for today
python mcp_orchestrator.py --topics "machine learning" "AI" --max-items 50

# Backfill last 7 days
python mcp_orchestrator.py --backfill 7

# Run on schedule (daily at 2 AM UTC)
python mcp_orchestrator.py --schedule
```

## 📁 Project Structure

```
MCP Server for daily/
├── config/
│   └── config.yaml              # Main configuration
├── src/
│   ├── ai/
│   │   ├── summarizer.py        # Gemini/OpenAI summarizer
│   │   └── headline_generator.py # Headline generation
│   ├── discovery/
│   │   └── discovery_manager.py # API discovery (arXiv, PubMed, etc.)
│   ├── scrapers/
│   │   └── scraper_manager.py   # Web scraping with robots.txt
│   ├── extractors/
│   │   └── extractor_manager.py # Content extraction
│   ├── processors/
│   │   ├── deduplicator.py      # Deduplication logic
│   │   └── scorer.py            # Relevance scoring
│   ├── generators/
│   │   └── newspaper_generator.py # HTML/PDF generation
│   ├── storage/
│   │   └── database.py          # SQLite/PostgreSQL
│   └── utils/
│       ├── logger.py            # Logging setup
│       ├── config_loader.py     # Config management
│       └── notifier.py          # Slack/Email notifications
├── data/                        # Generated data
│   ├── newspapers/              # Daily newspapers
│   │   └── YYYY-MM-DD/
│   │       ├── newspaper.json
│   │       ├── newspaper.html
│   │       └── newspaper.pdf
│   ├── cache/                   # Cached data
│   └── mcp.db                   # SQLite database
├── logs/                        # Log files
├── mcp_orchestrator.py          # Main entry point
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

## 🎯 Usage Examples

### Basic Usage

```bash
# Single topic, today's date
python mcp_orchestrator.py --topics "protein folding"

# Multiple topics, specific date
python mcp_orchestrator.py --topics "NLP" "transformers" --date 2025-10-15

# Limit items processed
python mcp_orchestrator.py --topics "robotics" --max-items 30
```

### Advanced Usage

```bash
# Backfill last 5 days
python mcp_orchestrator.py --backfill 5 --topics "climate change"

# Run scheduled job (keeps running)
python mcp_orchestrator.py --schedule

# Custom config file
python mcp_orchestrator.py --config my_config.yaml --topics "blockchain"
```

### Programmatic Usage

```python
from mcp_orchestrator import MCPOrchestrator

# Initialize
orchestrator = MCPOrchestrator(config_path='config/config.yaml')

# Run pipeline
newspaper = orchestrator.run_pipeline(
    topics=['deep learning', 'computer vision'],
    date='2025-10-29',
    max_items=100
)

print(f"Generated: {newspaper['paths']['html']}")
```

## ⚙️ Configuration

### AI Model Selection

In `config/config.yaml`:

```yaml
ai_models:
  summarizer: "gemini"          # or "openai"
  headline_generator: "gemini"  # or "openai"
  embeddings: "openai"           # for relevance scoring
  gemini_model: "gemini-1.5-pro-latest"
  openai_chat_model: "gpt-4o"
  openai_embedding_model: "text-embedding-3-small"
```

### Scoring Weights

```yaml
scoring:
  weights:
    relevance: 0.35   # Semantic similarity to topics
    recency: 0.25     # How recent the publication
    credibility: 0.20 # Source reputation
    novelty: 0.20     # Uniqueness
  relevance_threshold: 0.6
```

### Rate Limiting

```yaml
crawling:
  rate_limit_per_second: 1.0
  max_crawl_per_source: 200
  respect_robots_txt: true
  timeout_seconds: 30
```

## 📊 Output Formats

### 1. JSON (`newspaper.json`)

```json
{
  "date": "2025-10-29",
  "title": "Daily Research Bulletin: Machine Learning",
  "sections": [
    {
      "id": "top_research",
      "title": "Top Research Picks",
      "items": [
        {
          "id": "arXiv:2501.01234",
          "headline": "Scaling GNNs to Trillion-edge Graphs",
          "tldr": "Introduces sparse attention for GNNs...",
          "bullets": ["...", "..."],
          "score": 0.92
        }
      ]
    }
  ]
}
```

### 2. HTML (`newspaper.html`)

Professional newspaper-style layout with:
- Header and date
- Table of contents
- Sections with articles
- Clickable links to sources
- Metadata footer

### 3. PDF (`newspaper.pdf`)

Print-ready PDF generated from HTML.

## 🔧 Advanced Features

### Database Options

**SQLite (default):**
```yaml
storage:
  database:
    type: "sqlite"
    path: "./data/mcp.db"
```

**PostgreSQL:**
```yaml
storage:
  database:
    type: "postgresql"
    host: "localhost"
    port: 5432
    database: "mcp_research"
    user: "mcp_user"
    password: "your_password"
```

### Notifications

**Slack:**
```yaml
notifications:
  enabled: true
  slack:
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK"
```

**Email:**
```yaml
notifications:
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    username: "your_email@gmail.com"
    password: "your_app_password"
```

### Scheduling

**Cron Expression:**
```yaml
schedule:
  enabled: true
  cron: "0 2 * * *"  # Daily at 2 AM UTC
  timezone: "UTC"
```

## 📝 Logging

Logs are written to:
- Console (colored, INFO level)
- `logs/mcp.log` (detailed, DEBUG level, rotated at 10MB)

```python
# Adjust log level in config/config.yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📜 License

MIT License - See LICENSE file for details

## ⚠️ Legal & Ethics

- **Robots.txt Compliance**: Always respects robots.txt directives
- **Rate Limiting**: Enforces polite crawling (1 req/sec default)
- **Fair Use**: Stores only metadata for paywalled content
- **Attribution**: All sources are properly cited and linked
- **DMCA Compliance**: Remove content upon valid takedown requests

## 🐛 Troubleshooting

### API Key Errors

```bash
# Verify keys are set
source .env
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY
```

### PDF Generation Issues

```bash
# Install wkhtmltopdf
sudo apt-get install wkhtmltopdf  # Ubuntu/Debian
brew install wkhtmltopdf          # macOS

# Or use weasyprint (pure Python)
# Set in config.yaml:
# output:
#   pdf_engine: "weasyprint"
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install --upgrade -r requirements.txt
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-research-bot/issues)
- **Email**: abhishek746781@gmail.com
- **Documentation**: See `docs/` folder

## 🙏 Acknowledgments

- OpenAI for GPT-4 and embeddings API
- Google for Gemini API
- arXiv, PubMed, Crossref for research APIs
- Open source community

---

**Made with ❤️ for researchers and knowledge seekers**
