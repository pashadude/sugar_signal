# Sugar News Fetching & Sentiment Pipeline: Technical and User Documentation
## Quickstart: Running the Sugar Environment
> **Note on Python Environments:**  
> If you see an error like  
> `EnvironmentLocationNotFound: Not a conda environment: ... - it is a uv env`  
> this means your environment was created with [uv](https://github.com/astral-sh/uv) or `python -m venv`, not conda.  
> 
> To activate a `uv` or `venv` environment, use:
> 
> ```bash
> source sugarenv/bin/activate
> ```
> 
> Do **not** use `source activate sugarenv/bin` (that's for conda).
> 
> If you use [uv](https://github.com/astral-sh/uv), you can also run:
> 
> ```bash
> uv venv sugarenv
> source sugarenv/bin/activate
> ```
> 
> For conda environments, use:
> 
> ```bash
> conda activate sugarenv
> ```

1. **Install dependencies**  
   From the project root, install required Python packages (you may want to use a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**  
   - Copy or create a `.env` file in the project root (see `.env.example` if available).
   - At minimum, set:
     ```
     OPOINT_API_KEY=your_opoint_api_key
     CLICKHOUSE_HOST=your_clickhouse_host
     CLICKHOUSE_USERNAME=your_clickhouse_user
     CLICKHOUSE_PASSWORD=your_clickhouse_password
     CLICKHOUSE_DATABASE=news
     ```
   - You can also export these variables directly in your shell.

3. **Run the fetcher**  
   From the `backend/parsers` directory (or with full path), run:
   ```bash
   python sugar_news_fetcher.py --months-back 3 --max-articles 10000
   ```
   - Add `--dry-run` to preview what would be fetched.
   - Use `--max-workers N` to control parallelism.

4. **Check output and logs**  
   - Results are saved to ClickHouse if configured.
   - Console output will show progress, errors, and summary statistics.

5. **Troubleshooting**  
   - If you see "OPOINT_API_KEY environment variable not found", check your `.env` or shell exports.
   - For database errors, verify ClickHouse credentials and network access.


---

## Overview

This document describes the **sugar news fetching and triage pipeline** as implemented in [`sugar_news_fetcher.py`](../parsers/sugar_news_fetcher.py), and details all major connected modules, including Opoint API integration, normalization, filtering, and database storage. It is intended for both users and developers.

---

## 1. Main Entry Point: [`sugar_news_fetcher.py`](../parsers/sugar_news_fetcher.py)

### Purpose

- Orchestrates the fetching, normalization, triage, and storage of sugar-related news articles.
- Integrates with the Opoint API, applies advanced filtering, and saves results to the database.

### Key Steps

1. **Environment Setup**: Loads environment variables (e.g., `OPOINT_API_KEY`) using `dotenv`.
2. **Keyword Configuration**: Defines main, exclusion, and context keywords for sugar and related commodities.
3. **Fetching**: Uses [`OpointAPI`](../../api/opoint/opoint_api.py) to retrieve articles by topic and date.
4. **Filtering**: Applies main keyword and exclusion logic.
5. **Normalization**: Runs text through [`LanguageNormalizationPipeline`](../../text_filtering/language_normalization.py).
6. **Triage**: Applies [`triage_filter`](../../text_filtering/sugar_triage_filter.py) for quality, context, and pricing extraction.
7. **Trusted Source Filtering**: Uses [`filter_trusted_sources`](../parsers/source_filter.py) to keep only reliable news.
8. **Database Save**: Calls [`save_to_database`](../parsers/news_parser.py) to store results in ClickHouse.

### CLI Usage

```bash
python sugar_news_fetcher.py [--dry-run] [--max-workers N] [--months-back N] [--max-articles N]
```

- `--dry-run`: Show what would be fetched/processed, but do not execute.
- `--max-workers`: Number of parallel fetch jobs (default: 3).
- `--months-back`: How many months of news to fetch (default: 12).
- `--max-articles`: Max articles per request (default: 30000).

**Environment variable required:**  
- `OPOINT_API_KEY` (in `.env` or system environment)

---

## 2. Opoint API Integration: [`opoint_api.py`](../../api/opoint/opoint_api.py)

- **Class:** `OpointAPI`
- **Purpose:** Handles all communication with the Opoint news API.
- **Key Methods:**
  - `search_site_and_articles(...)`: Main entry for fetching articles by topic, keyword, date, etc.
  - `search_articles(...)`: Lower-level method for direct article queries.
- **Returns:** `pandas.DataFrame` with all relevant article fields (title, text, site, date, etc.).
- **Authentication:** Uses `OPOINT_API_KEY` from environment.

---

## 3. News Parsing and Database Storage: [`news_parser.py`](../parsers/news_parser.py)

- **Functions:**
  - `build_search_query(...)`: Constructs Opoint-compatible search queries.
  - `save_to_database(...)`: Saves filtered articles to ClickHouse (table: `sugar_opoint_news`).
  - `clean_html(...)`: Removes HTML tags from text.
  - `generate_article_id(...)`: Creates unique IDs for deduplication.
- **Database Config:**  
  - Uses settings from [`config.py`](../config.py) (`CLICKHOUSE_NATIVE_CONFIG`).
  - Requires ClickHouse credentials in `.env`.

---

## 4. Trusted Source Filtering: [`source_filter.py`](../parsers/source_filter.py)

- **Functions:**
  - `filter_trusted_sources(df)`: Removes articles from known low-quality or spam sources.
  - `is_trusted_source(name)`: Checks if a source is on the trusted list.
- **Customization:**  
  - Update `get_non_trusted_sources()` to add/remove sources.

---

## 5. Language Normalization: [`language_normalization.py`](../../text_filtering/language_normalization.py)

- **Class:** `LanguageNormalizationPipeline`
- **Purpose:** Standardizes, translates, and cleans text for robust downstream processing.
- **Features:**
  - Translation (M2M100, HuggingFace)
  - Typo correction (SymSpell/JamSpell)
  - Slang/synonym mapping (spaCy)
  - Punctuation and edge case handling

---

## 6. Triage Filtering: [`sugar_triage_filter.py`](sugar_triage_filter.py)

- **Function:** `triage_filter(text, ...)`
- **Purpose:** Applies quality, keyword, and context checks; extracts structured sugar pricing data.
- **Logic:**
  - Excludes non-sugar commodities and generic market news.
  - Passes only articles with main sugar keywords or strong context.
  - Extracts pricing tables, lists, and key-value lines relevant to sugar.

---

## 7. Configuration: [`config.py`](../config.py)

- **Purpose:** Loads environment variables and database credentials.
- **Variables:**
  - `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, `CLICKHOUSE_USERNAME`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_DATABASE`
  - `OPOINT_API_KEY`
- **.env file:** Place in the project root or as specified in `config.py`.

---

## 8. Data Flow Diagram

```
OpointAPI (opoint_api.py)
      |
      v
sugar_news_fetcher.py
      |
      v
LanguageNormalizationPipeline (language_normalization.py)
      |
      v
triage_filter (sugar_triage_filter.py)
      |
      v
filter_trusted_sources (source_filter.py)
      |
      v
save_to_database (news_parser.py)
      |
      v
ClickHouse (config.py)
```

---

## 9. References and Further Reading

- [`sugar_news_fetcher.py`](../parsers/sugar_news_fetcher.py)
- [`opoint_api.py`](../../api/opoint/opoint_api.py)
- [`news_parser.py`](../parsers/news_parser.py)
- [`source_filter.py`](../parsers/source_filter.py)
- [`language_normalization.py`](../../text_filtering/language_normalization.py)
- [`sugar_triage_filter.py`](sugar_triage_filter.py)
- [`config.py`](../config.py)

---

## 10. Troubleshooting

- **No articles fetched:** Check `OPOINT_API_KEY` and network access.
- **Database errors:** Verify ClickHouse credentials in `.env`.
- **Low article count:** Adjust keywords, topic IDs, or date range.
- **Unexpected exclusions:** Review trusted source list and triage filter logic.

---

## 11. Contribution & Onboarding

- Each module is independently testable and documented.
- New contributors should review the main pipeline and validation test files.
- Propose enhancements via pull request, including new tests for added logic or edge cases.

---

For further questions, see the referenced files or contact the maintainers.