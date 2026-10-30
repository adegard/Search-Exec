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
            if code_text and code_text not in self.code_blocks:
                self.code_blocks.append(code_text)
            self.current_code = []

    def handle_data(self, data):
        if self.in_code:
            self.current_code.append(data)

def search_duckduckgo_urls(query, max_results=3):
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
            urls = []
            for href in hrefs:
                href = html.unescape(href)
                if href.startswith('//'):
                    href = 'https:' + href
                elif not href.startswith('http'):
                    continue
                parsed = urllib.parse.urlparse(href)
                qs = urllib.parse.parse_qs(parsed.query)
                if 'uddg' in qs:
                    target = qs['uddg'][0]
                    if target not in urls:
                        urls.append(target)
                if len(urls) >= max_results:
                    break
            return urls
    except Exception as e:
        print(f"Search error: {e}")
    return []

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
        print(f"[-] Failed to fetch page ({e})")
    return None

def score_code_block(code):
    score = 0
    lines = code.splitlines()
    
    if len(code) < 5 or (len(lines) == 1 and ' ' not in code):
        return -100
        
    score += len(lines) * 5
    score += len(code) // 10
    
    indicators = ['sudo', 'apt', 'dpkg', 'pacman', 'yum', 'rpm', 'grep', 'awk', 'sort', '|', '>', '$', '#', 'for', 'echo', 'rm', 'find', 'opencode', 'uninstall']
    for ind in indicators:
        if ind in code:
            score += 3
            
    return score

def clean_command_for_execution(code):
    """Strips documentation syntax artifacts (like {{ }}, [opt1|opt2], etc.) to make commands executable."""
    # Remove template braces {{ ... }}
    code = re.sub(r'\{\{(.*?)\}\}', r'\1', code)
    # Handle option choices like [-f|--force] -> pick the first option (-f)
    code = re.sub(r'\[([^\]\|]+)\|[^\]]+\]', r'\1', code)
    # Strip remaining square brackets wrapping single options like [-f] -> -f
    code = re.sub(r'\[(-[^\]]+)\]', r'\1', code)
    return code.strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search_exec.py '<your search query>'")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    print(f"[*] Searching DuckDuckGo for: {query}...")
    
    target_urls = search_duckduckgo_urls(query, max_results=6)
    if not target_urls:
        print("[-] No search results found.")
        sys.exit(1)
        
    scored_blocks = []
    
    for url in target_urls:
        print(f"[+] Opening result: {url}")
        page_html = fetch_page(url)
        if not page_html:
            continue
            
        parser = CodeExtractor()
        parser.feed(page_html)
        
        if not parser.code_blocks:
            print("[-] No code blocks found on this page. Trying next result...")
            continue
            
        page_scored = [(block, score_code_block(block)) for block in parser.code_blocks]
        page_scored = [item for item in page_scored if item[1] > -50]
        
        if page_scored:
            scored_blocks = page_scored
            break
        else:
            print("[-] Code blocks found were too short. Trying next result...")

    scored_blocks.sort(key=lambda x: x[1], reverse=True)
    
    if not scored_blocks:
        print("[-] No valid command/script code blocks found across the top results.")
        sys.exit(1)
        
    top_snippets = scored_blocks[:3]
    print(f"\n[+] Top {len(top_snippets)} recommended snippet(s):\n")
    
    for idx, (code, score) in enumerate(top_snippets, 1):
        print(f"=== [ Snippet {idx} ] ===")
        print(code)
        print("=" * 22 + "\n")
        
    try:
        choice = input(f"Select a snippet to execute [1-{len(top_snippets)}] or press Enter to exit: ").strip()
        if not choice:
            print("Exited.")
            sys.exit(0)
            
        selected_idx = int(choice) - 1
        if 0 <= selected_idx < len(top_snippets):
            raw_code = top_snippets[selected_idx][0]
            clean_code = clean_command_for_execution(raw_code)
            
            print(f"\n[*] Executing cleaned command: {clean_code}\n")
            subprocess.run(clean_code, shell=True)
        else:
            print("[-] Invalid selection.")
    except ValueError:
        print("[-] Invalid input.")

if __name__ == "__main__":
    main()
