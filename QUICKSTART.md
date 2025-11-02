# Quick Start Guide - MCP Server

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd "/media/abhisekhkumar/532f0f5d-32d6-4a7c-9464-0aa27dbfb9b8/Tutorials/mcp_servers/MCP Server for daily"

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

### Step 2: Get API Keys

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

#### Google Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### Step 3: Configure `.env`

```bash
# Edit .env file
nano .env
```

Add your keys:
```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
GEMINI_API_KEY=your-actual-gemini-key-here
CROSSREF_EMAIL=your-email@example.com
```

### Step 4: Run Your First Generation

```bash
# Activate virtual environment
source venv/bin/activate

# Run with a simple topic
python mcp_orchestrator.py \
  --topics "machine learning" \
  --max-items 20
```

You should see:
```
================================================================================
MCP Orchestrator Starting...
================================================================================
INFO - Initializing components...
INFO - All components initialized successfully
INFO - Running pipeline for topics: ['machine learning']
...
================================================================================
PIPELINE COMPLETED SUCCESSFULLY
================================================================================
Duration: 45.23 seconds
Items processed: 18
Newspaper saved to: ./data/newspapers/2025-10-29/newspaper.html
```

### Step 5: View Your Newspaper

```bash
# Open the HTML newspaper in your browser
firefox ./data/newspapers/2025-10-29/newspaper.html

# Or view the JSON
cat ./data/newspapers/2025-10-29/newspaper.json | jq .
```

## 📝 Example Outputs

### Terminal Output

```
============================================================
STEP 1: DISCOVERY
============================================================
INFO - Discovering content from 2025-10-27 to 2025-10-29
INFO - Discovered 45 items from arXiv
INFO - Discovered 23 items from Crossref
INFO - Discovered 12 items from Google News
INFO - Total discovered: 80 items

============================================================
STEP 2: FETCH & SCRAPE
============================================================
Scraping: 100%|████████████████████| 80/80 [00:45<00:00,  1.78it/s]
INFO - Successfully scraped 78/80 items

============================================================
STEP 3: EXTRACT & PROCESS
============================================================
INFO - Extracted content from 78 items

============================================================
STEP 4: DEDUPLICATION
============================================================
INFO - Found 8 duplicates, 70 unique items remain

============================================================
STEP 5: SCORING & RANKING
============================================================
INFO - Scoring complete. Top score: 0.892

============================================================
STEP 6: SUMMARIZATION
============================================================
Summarizing: 100%|████████████████| 70/70 [02:15<00:00,  1.93s/it]
INFO - Completed summarization: 70 items

============================================================
STEP 7: HEADLINE GENERATION
============================================================
Headlines: 100%|█████████████████| 70/70 [00:32<00:00,  2.17it/s]

============================================================
STEP 8: NEWSPAPER GENERATION
============================================================
INFO - Generated JSON: ./data/newspapers/2025-10-29/newspaper.json
INFO - Generated HTML: ./data/newspapers/2025-10-29/newspaper.html
INFO - Generated PDF: ./data/newspapers/2025-10-29/newspaper.pdf
```

### Sample JSON Output

```json
{
  "date": "2025-10-29",
  "title": "Daily Research Bulletin: machine learning",
  "topics": ["machine learning"],
  "editorial": "Today's highlights in machine learning: Efficient Fine-Tuning of LLMs Using Low-Rank Adaptation (arXiv); Quantum Machine Learning Achieves Exponential Speedup (Nature); Meta Releases Llama 3.1 with 405B Parameters (MIT Technology Review).",
  "sections": [
    {
      "id": "top_research",
      "title": "Top Research Picks",
      "items": [
        {
          "id": "arXiv:2510.12345",
          "headline": "Efficient Fine-Tuning of LLMs Using Low-Rank Adaptation",
          "tldr": "This paper introduces LoRA-v2, achieving 3x faster fine-tuning with 40% less memory while maintaining accuracy on benchmark tasks.",
          "bullets": [
            "Proposes improved low-rank adaptation method for transformer models",
            "Reduces memory footprint by 40% compared to standard fine-tuning",
            "Achieves 3x speedup on NVIDIA A100 GPUs",
            "Maintains or improves accuracy on GLUE and SuperGLUE benchmarks",
            "Released open-source implementation with PyTorch"
          ],
          "significance": "This work addresses the critical challenge of fine-tuning large language models efficiently. The 40% memory reduction makes it possible to fine-tune larger models on commodity hardware, democratizing access to LLM customization.",
          "limitations": "Experiments limited to encoder-decoder models under 7B parameters. Effectiveness on very large models (>100B) remains to be validated.",
          "keywords": ["LoRA", "fine-tuning", "LLMs", "efficiency", "transformers"],
          "authors": ["J. Smith", "A. Chen", "M. Rodriguez"],
          "published_at": "2025-10-28",
          "source": "arXiv",
          "url": "https://arxiv.org/abs/2510.12345",
          "pdf_url": "https://arxiv.org/pdf/2510.12345.pdf",
          "score": 0.892
        }
      ]
    }
  ],
  "metadata": {
    "generated_at": "2025-10-29T14:32:15.123456",
    "sources_count": 8,
    "papers_count": 15,
    "news_count": 5,
    "total_items": 20
  }
}
```

## 🎨 Customization

### Change AI Models

Edit `config/config.yaml`:

```yaml
ai_models:
  summarizer: "gemini"       # Switch between "gemini" and "openai"
  headline_generator: "gemini"
  gemini_model: "gemini-1.5-flash"  # Faster, cheaper
  # or
  gemini_model: "gemini-1.5-pro-latest"  # Better quality
```

### Add Custom Topics

```yaml
topics:
  - "quantum computing"
  - "CRISPR gene editing"
  - "renewable energy"
  - "your custom topic"
```

### Adjust Scoring Weights

```yaml
scoring:
  weights:
    relevance: 0.40   # Increase for stricter topic matching
    recency: 0.30     # Increase to prefer newer papers
    credibility: 0.20
    novelty: 0.10
```

## 🔧 Common Issues

### "No module named 'google.generativeai'"

```bash
pip install google-generativeai
```

### "OpenAI API key not found"

Make sure `.env` is in the project root and has been loaded:
```bash
source .env
echo $OPENAI_API_KEY
```

### PDF generation fails

Install wkhtmltopdf:
```bash
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# macOS
brew install wkhtmltopdf

# Or use pure Python alternative
# In config.yaml:
output:
  pdf_engine: "weasyprint"
```

## 📅 Daily Scheduled Run

### Using cron

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/mcp && /path/to/venv/bin/python mcp_orchestrator.py --topics "AI" >> /path/to/logs/cron.log 2>&1
```

### Using the built-in scheduler

```bash
# Runs continuously with schedule from config.yaml
python mcp_orchestrator.py --schedule
```

## 🎯 Next Steps

1. **Explore the output**: Open `data/newspapers/YYYY-MM-DD/newspaper.html`
2. **Try different topics**: Run with topics relevant to your field
3. **Set up scheduling**: Automate daily runs
4. **Enable notifications**: Get Slack/email alerts
5. **Customize the newspaper**: Edit templates in `newspaper_generator.py`

## 💡 Pro Tips

- Start with `--max-items 20` for faster testing
- Use `gemini-1.5-flash` for faster/cheaper summarization
- Enable caching to avoid re-scraping same URLs
- Check `logs/mcp.log` for detailed debugging
- Use `--backfill 7` to generate newspapers for past week

Enjoy your automated research newspaper! 📰🚀
