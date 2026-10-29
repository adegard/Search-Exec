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

def search_duckduckgo(query):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        url, 
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
            
            # Find all result hrefs containing uddg
            hrefs = re.findall(r'href="([^"]+uddg=[^"]+)"', html_content)
            for href in hrefs:
                # Clean HTML entities like &amp; -> &
                href = html.unescape(href)
                
                # Handle protocol-relative URLs
                if href.startswith('//'):
                    href = 'https:' + href
                elif not href.startswith('http'):
                    continue
                
                # Extract the actual destination URL from the uddg parameter
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
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Failed to fetch page: {e}")
    return None

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
        
    print(f"\n[+] Found {len(parser.code_blocks)} code block(s):\n")
    for i, code in enumerate(parser.code_blocks[:5], 1):
        print(f"--- [ Snippet {i} ] ---")
        print(code)
        print("-" * 25)
        
        choice = input(f"\nExecute Snippet {i} in CLI? [y/N]: ").strip().lower()
        if choice == 'y':
            print(f"[*] Running command...\n")
            try:
                subprocess.run(code, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"[-] Command failed with exit code {e.returncode}")
            break
        else:
            print("Skipping...\n")

if __name__ == "__main__":
    main()
