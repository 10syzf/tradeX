from __future__ import annotations

from functools import lru_cache
from typing import Any

import akshare as ak


class MarketDataService:
    def search_stocks(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        normalized = query.strip()
        if not normalized:
            return []

        table = _load_stock_table()
        candidates: list[dict[str, Any]] = []

        if normalized.isdigit():
            exact_code = table[table['code'].str.contains(normalized, na=False)]
            candidates.extend(exact_code.head(limit).to_dict('records'))
        else:
            exact_name = table[table['name'].str.contains(normalized, na=False)]
            candidates.extend(exact_name.head(limit).to_dict('records'))

        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        for row in candidates:
            code = str(row['code'])
            if code in seen:
                continue
            seen.add(code)
            results.append({
                'symbol': code,
                'name': str(row['name']).replace(' ', ''),
                'market': _infer_market(code),
            })
            if len(results) >= limit:
                break
        return results

    def match_stock_from_text(self, text: str) -> dict[str, Any] | None:
        normalized = text.replace(' ', '')
        table = _load_stock_table()

        direct_code = next((part for part in normalized.split() if part.isdigit() and len(part) == 6), None)
        if direct_code:
            matches = self.search_stocks(direct_code, limit=1)
            return matches[0] if matches else None

        names = table['name'].tolist()
        best_match = ''
        for name in names:
            if name and name in normalized and len(name) > len(best_match):
                best_match = name

        if not best_match:
            return None

        matches = self.search_stocks(best_match, limit=1)
        return matches[0] if matches else None

    def get_quote(self, symbol: str) -> dict[str, Any]:
        info_df = ak.stock_individual_info_em(symbol=symbol)
        bid_df = ak.stock_bid_ask_em(symbol=symbol)

        info_map = _frame_to_map(info_df)
        bid_map = _frame_to_map(bid_df)

        return {
            'symbol': symbol,
            'name': str(info_map.get('股票简称', '')),
            'market': _infer_market(symbol),
            'industry': str(info_map.get('行业', '')),
            'latest_price': _to_float(info_map.get('最新')),
            'open_price': _to_float(bid_map.get('open')),
            'high_price': _to_float(bid_map.get('high')),
            'low_price': _to_float(bid_map.get('low')),
            'last_close': _to_float(bid_map.get('pre_close')),
            'volume': _to_float(bid_map.get('volume')),
            'turnover': _to_float(bid_map.get('deal')),
            'change_percent': _safe_change_percent(info_map, bid_map),
            'total_market_value': _to_float(info_map.get('总市值')),
            'circulating_market_value': _to_float(info_map.get('流通市值')),
        }

    def get_history(self, symbol: str, start_date: str, end_date: str, limit: int = 60) -> list[dict[str, Any]]:
        hist_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq',
        )
        if hist_df.empty:
            return []

        rows = hist_df.tail(limit).to_dict('records')
        return [
            {
                'date': str(row['日期']),
                'open': _to_float(row['开盘']),
                'close': _to_float(row['收盘']),
                'high': _to_float(row['最高']),
                'low': _to_float(row['最低']),
                'volume': _to_float(row['成交量']),
                'turnover': _to_float(row['成交额']),
                'change_percent': _to_float(row['涨跌幅']),
            }
            for row in rows
        ]

    def get_news(self, symbol: str, limit: int = 5) -> list[dict[str, Any]]:
        news_df = ak.stock_news_em(symbol=symbol)
        if news_df.empty:
            return []
        rows = news_df.head(limit).to_dict('records')
        return [
            {
                'title': str(row['新闻标题']),
                'content': str(row['新闻内容']),
                'published_at': str(row['发布时间']),
                'source': str(row['文章来源']),
                'url': str(row['新闻链接']),
            }
            for row in rows
        ]


@lru_cache(maxsize=1)
def _load_stock_table():
    table = ak.stock_info_a_code_name()
    table['code'] = table['code'].astype(str).str.zfill(6)
    table['name'] = table['name'].astype(str).str.replace(' ', '')
    return table


def _frame_to_map(df) -> dict[str, Any]:
    return {str(row['item']): row['value'] for row in df.to_dict('records')}


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, '', '-'):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _infer_market(symbol: str) -> str:
    if symbol.startswith(('600', '601', '603', '605', '688', '900')):
        return 'SH'
    if symbol.startswith(('000', '001', '002', '003', '300', '301', '200')):
        return 'SZ'
    if symbol.startswith(('430', '831', '832', '833', '834', '835', '836', '837', '838', '839', '870', '871', '872', '873', '874', '875', '876', '877', '878', '879')):
        return 'BJ'
    return 'UNKNOWN'


def _safe_change_percent(info_map: dict[str, Any], bid_map: dict[str, Any]) -> float | None:
    latest = _to_float(info_map.get('最新'))
    pre_close = _to_float(bid_map.get('pre_close'))
    if latest is None or pre_close in (None, 0):
        return None
    return round((latest - pre_close) / pre_close * 100, 2)
