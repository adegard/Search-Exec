#!/usr/bin/env python3
import sys
import urllib.request
import urllib.parse
import html
import re
import subprocess
from html.parser import HTMLParser

class CodeExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.code_blocks = []
        self.in_code = False
        self.current_code = []

    def handle_starttag(self, tag, attrs):
        if tag in ['code', 'pre']:
            self.in_code = True

    def handle_endtag(self, tag):
        if tag in ['code', 'pre'] and self.in_code:
            self.in_code = False
            code_text = "".join(self.current_code).strip()
            # Clean up excessive internal whitespace/newlines but preserve structure
            if code_text and code_text not in self.code_blocks:
                self.code_blocks.append(code_text)
            self.current_code = []

    def handle_data(self, data):
        if self.in_code:
            self.current_code.append(data)

def search_duckduckgo(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        url, 
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
            hrefs = re.findall(r'href="([^"]+uddg=[^"]+)"', html_content)
            for href in hrefs:
                href = html.unescape(href)
                if href.startswith('//'):
                    href = 'https:' + href
                elif not href.startswith('http'):
                    continue
                parsed = urllib.parse.urlparse(href)
                qs = urllib.parse.parse_qs(parsed.query)
                if 'uddg' in qs:
                    return qs['uddg'][0]
    except Exception as e:
        print(f"Search error: {e}")
    return None

def fetch_page(url):
    req = urllib.request.Request(
        url, 
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://html.duckduckgo.com/"
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Failed to fetch page: {e}")
    return None

def score_code_block(code):
    """Score code blocks to prioritize real scripts/commands over single-word tokens."""
    score = 0
    lines = code.splitlines()
    
    # Penalize single-word or very short snippets (e.g. "apt", "ls")
    if len(code) < 10 or (len(lines) == 1 and ' ' not in code):
        return -100
        
    # Reward multi-line code blocks or scripts
    score += len(lines) * 5
    score += len(code) // 10
    
    # Reward typical shell command indicators / operators
    indicators = ['sudo', 'apt', 'dpkg', 'pacman', 'yum', 'rpm', 'grep', 'awk', 'sort', '|', '>', '$', '#']
    for ind in indicators:
        if ind in code:
            score += 3
            
    return score

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search_exec.py '<your search query>'")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    print(f"[*] Searching DuckDuckGo for: {query}...")
    
    target_url = search_duckduckgo(query)
    if not target_url:
        print("[-] No search results found.")
        sys.exit(1)
        
    print(f"[+] Opening top result: {target_url}")
    page_html = fetch_page(target_url)
    if not page_html:
        sys.exit(1)
        
    parser = CodeExtractor()
    parser.feed(page_html)
    
    if not parser.code_blocks:
        print("[-] No code blocks (<code>/<pre>) found on the target page.")
        sys.exit(1)
        
    # Filter and sort code blocks by score (best first)
    scored_blocks = [(block, score_code_block(block)) for block in parser.code_blocks]
    scored_blocks = [item for item in scored_blocks if item[1] > 0] # Drop garbage single words
    scored_blocks.sort(key=lambda x: x[1], reverse=True)
    
    if not scored_blocks:
        print("[-] No valid command/script code blocks found.")
        sys.exit(1)
        
    print(f"\n[+] Found {len(parser.code_blocks)} total blocks, filtered down to {len(scored_blocks)} best command snippet(s):\n")
    
    # Take the top best snippet automatically as the primary recommendation
    best_code, best_score = scored_blocks[0]
    
    print("--- [ Best Recommended Snippet ] ---")
    print(best_code)
    print("-" * 34)
    
    choice = input(f"\nExecute this snippet in CLI? [y/N]: ").strip().lower()
    if choice == 'y':
        print(f"[*] Running command...\n")
        try:
            subprocess.run(best_code, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[-] Command failed with exit code {e.returncode}")
    else:
        print("Skipped execution.")

if __name__ == "__main__":
    main()
