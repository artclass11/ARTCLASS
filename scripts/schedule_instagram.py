#!/usr/bin/env python3
from __future__ import annotations

import argparse

from app.services.instagram import schedule_instagram_post


def main() -> None:
    parser = argparse.ArgumentParser(description="Schedule a reel to Instagram")
    parser.add_argument("--file", required=True, help="Video file path")
    parser.add_argument("--caption", required=True, help="Post caption")
    parser.add_argument("--scheduled-at", default=None, help="Optional ISO scheduled time")
    parser.add_argument("--account-id", default=None, help="Optional Instagram account ID")
    args = parser.parse_args()

    result = schedule_instagram_post(
        file_path=args.file,
        caption=args.caption,
        scheduled_at=args.scheduled_at,
        account_id=args.account_id,
    )
    print(result)


if __name__ == "__main__":
    main()
