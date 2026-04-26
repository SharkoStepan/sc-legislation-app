"""
Тонкая обёртка для чтения отфильтрованных новостей из SQLite.
Flask читает напрямую из БД — без зависимости от sc_kpm.
"""

import os
import re
import html
from pathlib import Path
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, func
from sqlalchemy.orm import declarative_base, sessionmaker


def _clean_html(text: str) -> str:
    if not text:
        return ''
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

Base = declarative_base()


class _FilteredNews(Base):
    __tablename__ = 'filtered_news'

    id               = Column(Integer, primary_key=True)
    title            = Column(String(500))
    link             = Column(String(500), unique=True)
    summary          = Column(Text)
    published_date   = Column(DateTime)
    feed_source      = Column(String(200))
    relevance_score  = Column(Integer, default=0)
    matched_keywords = Column(String(500))

    def to_dict(self):
        return {
            'id':              self.id,
            'title':           self.title or '',
            'link':            self.link or '',
            'summary':         _clean_html(self.summary),
            'published_date':  self.published_date.isoformat() if self.published_date else None,
            'feed_source':     self.feed_source or '',
            'relevance_score': self.relevance_score or 0,
        }


def _find_db_path() -> str:
    """Поиск БД в нескольких возможных расположениях."""
    candidates = [
        # app внутри ostis-legislation (нормальный случай)
        Path(__file__).resolve().parent / '../../../../databases/filtered_news.db',
        # app вынесен из папки
        Path.home() / 'ostis-legislation/databases/filtered_news.db',
        # env var override
    ]
    env = os.environ.get('NEWS_DB_PATH')
    if env:
        return env
    for p in candidates:
        resolved = p.resolve()
        if resolved.exists():
            return str(resolved)
    # вернуть первый вариант как дефолт (БД ещё не создана — вернётся пустой список)
    return str(candidates[1].resolve())


def _make_session():
    db_path = _find_db_path()
    engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
    Session = sessionmaker(bind=engine)
    return Session()


def get_news(limit: int = 50, source: str | None = None) -> list[dict]:
    """Вернуть список новостей, отсортированных по дате (новые первые)."""
    try:
        session = _make_session()
        try:
            q = session.query(_FilteredNews).order_by(_FilteredNews.published_date.desc())
            if source:
                q = q.filter(_FilteredNews.feed_source == source)
            if limit:
                q = q.limit(limit)
            return [n.to_dict() for n in q.all()]
        finally:
            session.close()
    except Exception as e:
        print(f"[news_reader] get_news error: {e}")
        return []


def get_news_sources() -> list[str]:
    """Список уникальных источников."""
    try:
        session = _make_session()
        try:
            rows = session.query(_FilteredNews.feed_source).distinct().all()
            return sorted([r[0] for r in rows if r[0]])
        finally:
            session.close()
    except Exception as e:
        print(f"[news_reader] get_news_sources error: {e}")
        return []


def get_news_count() -> int:
    """Общее количество новостей в БД."""
    try:
        session = _make_session()
        try:
            return session.query(func.count(_FilteredNews.id)).scalar() or 0
        finally:
            session.close()
    except Exception:
        return 0
