# Search & Exec (`search_exec.py`)

A fast, lightweight, zero-dependency CLI tool that searches the web for command-line solutions, parses the top search result for code snippets (`<code>` or `<pre>` blocks), and prompts you to execute them directly in your shell.

---

## Features

- **Zero External Dependencies:** Built using standard Python libraries (`urllib`, `re`, `subprocess`, `html.parser`).
- **Automated Scraping:** Queries DuckDuckGo in the background to find relevant technical posts, blogs, and documentation.
- **HTML Parsing:** Extracts code blocks (`<code>` / `<pre>`) automatically from the top result page.
- **Interactive Execution:** Preview each snippet safely before deciding to run it in your terminal.

---

## Prerequisites

- Python 3.6 or higher
- Linux, macOS, or WSL (Windows Subsystem for Linux)

---

## Installation

Clone the repository and make the script executable:

```bash
git clone [https://github.com/your-username/search-exec.git](https://github.com/your-username/search-exec.git)
cd search-exec
chmod +x search_exec.py
