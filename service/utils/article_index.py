"""
Article index: parses SCS knowledge-base files at import time and provides
a fast in-memory search over article titles and content.
"""

import os
import re
from html import unescape

def _find_base_dir() -> str:
    """
    Find the ostis-legislation root directory that contains knowledge-base/.
    Tries, in order:
      1. OSTIS_KB_DIR environment variable
      2. 3 levels up from this file (works when app is inside ostis-legislation)
      3. ~/ostis-legislation (common install location)
    """
    _SCS_REL = os.path.join(
        'knowledge-base', 'legal', 'belarus', 'sections',
        'section_dict_education_legislation_belarus', 'acts',
        'by_act_hk1100243.scs',
    )
    # 1. Env var
    env = os.environ.get('OSTIS_KB_DIR')
    if env and os.path.isfile(os.path.join(env, _SCS_REL)):
        return env

    # 2. Relative to this file (app inside ostis-legislation)
    rel = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..'))
    if os.path.isfile(os.path.join(rel, _SCS_REL)):
        return rel

    # 3. Common install: ~/ostis-legislation
    home_based = os.path.expanduser('~/ostis-legislation')
    if os.path.isfile(os.path.join(home_based, _SCS_REL)):
        return home_based

    # Fallback: return rel and let _build_index() report the real path
    return rel

_BASE_DIR = _find_base_dir()
_SCS_PATH = os.path.join(
    _BASE_DIR,
    'knowledge-base', 'legal', 'belarus', 'sections',
    'section_dict_education_legislation_belarus', 'acts',
    'by_act_hk1100243.scs',
)
_HTML_DIR = os.path.join(os.path.dirname(_SCS_PATH), 'text')

# [{id, title, html_path}, ...]
_ARTICLES: list[dict] = []

_RE_ARTICLE = re.compile(
    r'nrel_article:\s+(by_act_hk1100243_article_\d+)\s*\(\*'
)
_RE_TITLE = re.compile(
    r'nrel_main_idtf:\s*\[([^\]]+)\]\s*\(\*\s*<-\s*lang_ru'
)
_RE_HTML_TAG = re.compile(r'<[^>]+>')


def _strip_html(html: str) -> str:
    return unescape(_RE_HTML_TAG.sub('', html))


def _build_index():
    """Parse the SCS file once and populate _ARTICLES."""
    if _ARTICLES:
        return
    if not os.path.isfile(_SCS_PATH):
        print(f"[article_index] SCS file not found: {_SCS_PATH}")
        return

    with open(_SCS_PATH, encoding='utf-8') as f:
        text = f.read()

    # Split by article blocks
    parts = _RE_ARTICLE.split(text)
    # parts[0] = preamble, then alternating: article_id, block_content
    for i in range(1, len(parts) - 1, 2):
        article_id = parts[i].strip()
        block = parts[i + 1]
        m = _RE_TITLE.search(block)
        if not m:
            continue
        title = m.group(1).strip()
        html_file = os.path.join(_HTML_DIR, f'{article_id}.html')
        _ARTICLES.append({
            'id': article_id,
            'title': title,
            'html_path': html_file,
        })

    print(f"[article_index] Loaded {len(_ARTICLES)} articles")


def _read_content(html_path: str, max_chars: int = 500) -> str:
    """Read HTML file and return plain-text preview."""
    if not os.path.isfile(html_path):
        return ''
    try:
        with open(html_path, encoding='utf-8') as f:
            raw = f.read()
        plain = _strip_html(raw).strip()
        if len(plain) > max_chars:
            return plain[:max_chars] + '...'
        return plain
    except Exception:
        return ''


def get_all_titles() -> list[str]:
    """Return all article titles (for autocomplete)."""
    _build_index()
    return [a['title'] for a in _ARTICLES]


def get_article(article_id: str) -> dict | None:
    """Return full article by ID: {id, title, content}."""
    _build_index()
    for a in _ARTICLES:
        if a['id'] == article_id:
            content = ''
            if os.path.isfile(a['html_path']):
                try:
                    with open(a['html_path'], encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    pass
            return {'id': a['id'], 'title': a['title'], 'content': content}
    return None


def search_articles(query: str, limit: int = 20) -> list[dict]:
    """
    Search articles by query string.
    Returns list of {id, title, content} dicts.
    """
    _build_index()
    if not query or not query.strip():
        return []

    q = query.strip().lower()
    results = []

    # 1. Try exact article number match: "Статья 15" or just "15"
    num_match = re.search(r'(\d+)', q)
    if num_match:
        num = num_match.group(1)
        target_id = f'by_act_hk1100243_article_{num}'
        for a in _ARTICLES:
            if a['id'] == target_id:
                results.append({
                    'id': a['id'],
                    'title': a['title'],
                    'content': _read_content(a['html_path']),
                })
                break

    # 2. Substring match on title
    for a in _ARTICLES:
        if a['id'] in {r['id'] for r in results}:
            continue
        if q in a['title'].lower():
            results.append({
                'id': a['id'],
                'title': a['title'],
                'content': _read_content(a['html_path']),
            })
        if len(results) >= limit:
            break

    # 3. If still no results, search in content
    if not results:
        for a in _ARTICLES:
            content = _read_content(a['html_path'], max_chars=2000)
            if q in content.lower():
                results.append({
                    'id': a['id'],
                    'title': a['title'],
                    'content': _read_content(a['html_path']),
                })
                if len(results) >= limit:
                    break

    return results
