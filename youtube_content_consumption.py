"""YouTube public content-consumption proxy -> CSV.

Collects public YouTube search results plus public video statistics for a set of
content queries. This does not access a user's private watch history.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from dotenv import load_dotenv

BASE_URL = "https://www.googleapis.com/youtube/v3"
DEFAULT_QUERIES = [
    "data analytics",
    "artificial intelligence",
    "career development",
    "business intelligence",
    "machine learning",
    "data science",
    "entrepreneurship",
    "technology trends",
    "finance",
    "politics"
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public YouTube content-consumption proxies into CSV.")
    parser.add_argument(
        "--queries",
        nargs="+",
        default=DEFAULT_QUERIES,
        help="One or more YouTube search queries.",
    )
    parser.add_argument("--region", default="KE", help="ISO country code used to localize search results. Default: KE")
    parser.add_argument("--max-results", type=int, default=100, help="Results per query per page. Max 50.")
    parser.add_argument("--pages", type=int, default=5, help="Number of search-result pages per query. Keep small to preserve quota.")
    parser.add_argument(
        "--order",
        choices=["relevance", "viewCount", "date"],
        default="viewCount",
        help="Search ordering. 'viewCount' is useful as a consumption/popularity proxy.",
    )
    parser.add_argument("--output", default="data/youtube_content_consumption.csv")
    return parser.parse_args()


def get_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "YOUTUBE_API_KEY is missing. Add it to a .env file or your environment."
        )
    return api_key


def youtube_get(endpoint: str, api_key: str, params: dict) -> dict:
    params = {**params, "key": api_key}
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    if response.status_code != 200:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise RuntimeError(f"YouTube API error {response.status_code}: {detail}")
    return response.json()


def search_videos(api_key: str, query: str, region: str, order: str, max_results: int, pages: int) -> list[dict]:
    results: list[dict] = []
    page_token = None

    for page_number in range(1, pages + 1):
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "regionCode": region,
            "maxResults": max_results,
            "order": order,
            "safeSearch": "moderate",
        }
        if page_token:
            params["pageToken"] = page_token

        payload = youtube_get("search", api_key, params)
        for position, item in enumerate(payload.get("items", []), start=1):
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            snippet = item.get("snippet", {})
            results.append(
                {
                    "query": query,
                    "search_page": page_number,
                    "search_position": position,
                    "video_id": video_id,
                    "channel_id": snippet.get("channelId"),
                    "channel_title": snippet.get("channelTitle"),
                    "video_title": snippet.get("title"),
                    "published_at": snippet.get("publishedAt"),
                    "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                }
            )

        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    return results


def chunked(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def parse_iso8601_duration(value: str | None) -> int | None:
    if not value or not value.startswith("PT"):
        return None

    hours = minutes = seconds = 0
    number = ""
    for char in value[2:]:
        if char.isdigit():
            number += char
        else:
            if not number:
                continue
            amount = int(number)
            if char == "H":
                hours = amount
            elif char == "M":
                minutes = amount
            elif char == "S":
                seconds = amount
            number = ""
    return hours * 3600 + minutes * 60 + seconds


def fetch_video_details(api_key: str, video_ids: list[str]) -> dict[str, dict]:
    details: dict[str, dict] = {}
    for batch in chunked(video_ids, 50):
        payload = youtube_get(
            "videos",
            api_key,
            {
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(batch),
            },
        )
        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            details[item["id"]] = {
                "category_id": snippet.get("categoryId"),
                "duration_seconds": parse_iso8601_duration(content.get("duration")),
                "definition": content.get("definition"),
                "caption_available": content.get("caption"),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            }
    return details


def calculate_metrics(row: dict) -> dict:
    published = pd.to_datetime(row["published_at"], utc=True, errors="coerce")
    collected = pd.to_datetime(row["collected_at_utc"], utc=True, errors="coerce")

    if pd.notna(published) and pd.notna(collected):
        age_days = max((collected - published).total_seconds() / 86400, 0.25)
    else:
        age_days = None

    views = row["views"] or 0
    likes = row["likes"] or 0
    comments = row["comments"] or 0

    row["video_age_days"] = round(age_days, 2) if age_days is not None else None
    row["views_per_day_since_publish"] = round(views / age_days, 2) if age_days else None
    row["like_rate"] = round(likes / views, 6) if views else 0
    row["comment_rate"] = round(comments / views, 6) if views else 0
    row["engagement_rate"] = round((likes + comments) / views, 6) if views else 0
    row["video_url"] = f"https://www.youtube.com/watch?v={row['video_id']}"
    return row


def save_csv(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    new_df = pd.DataFrame(rows)

    if output.exists():
        old_df = pd.read_csv(output)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        # Keep each query + video + collection timestamp as a distinct snapshot.
        key_cols = ["query", "video_id", "collected_at_utc"]
        combined = combined.drop_duplicates(subset=key_cols, keep="last")
    else:
        combined = new_df

    combined.to_csv(output, index=False, quoting=csv.QUOTE_MINIMAL)


def main() -> int:
    args = parse_args()
    if not 1 <= args.max_results <= 100:
        raise ValueError("--max-results must be between 1 and 100.")
    if args.pages < 1:
        raise ValueError("--pages must be at least 1.")

    api_key = get_api_key()
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    print(f"Collecting YouTube public content data for region={args.region}, order={args.order}")
    print(f"Queries: {', '.join(args.queries)}")

    search_rows: list[dict] = []
    for query in args.queries:
        rows = search_videos(
            api_key=api_key,
            query=query,
            region=args.region,
            order=args.order,
            max_results=args.max_results,
            pages=args.pages,
        )
        search_rows.extend(rows)
        print(f"  {query!r}: {len(rows)} videos found")

    # Deduplicate video IDs for a single statistics request batch.
    video_ids = list(dict.fromkeys(row["video_id"] for row in search_rows))
    details = fetch_video_details(api_key, video_ids)
    print(f"Retrieved statistics for {len(details)} unique videos.")

    rows: list[dict] = []
    for row in search_rows:
        row["collected_at_utc"] = collected_at
        row.update(details.get(row["video_id"], {}))
        rows.append(calculate_metrics(row))

    save_csv(rows, Path(args.output))
    print(f"Saved {len(rows)} records to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
