#!/usr/bin/env python3
"""
CLI for US Company Dossier Skill (Simplified)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# Add the skill directory to Python path
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

# Load .env from workspace
def _load_dotenv():
    for base in [skill_dir.parent.parent, Path(os.getcwd())]:
        env_path = base / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
                if m and not line.strip().startswith("#"):
                    key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val
            break

_load_dotenv()

from us_company_dossier import build_dossier, update_dossier, status, list_filings


def main():
    parser = argparse.ArgumentParser(
        description="US Company Dossier Builder - Generate SEC filing metadata with online links"
    )
    parser.add_argument("--workspace", default=os.getenv("WORKSPACE_ROOT", os.getcwd()),
                       help="Workspace root directory")
    parser.add_argument("--dossier-root", default=os.getenv("DOSSIER_ROOT"),
                       help="Dossier output directory")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Build company dossier")
    build_parser.add_argument("ticker", help="Company ticker symbol (e.g., AAPL, TSLA)")
    build_parser.add_argument("--years", type=int, default=3, 
                             help="Number of years of history to fetch (default: 3)")
    build_parser.add_argument("--forms", nargs="+", 
                             default=["10-K", "10-Q", "8-K", "DEF 14A", "4"],
                             help="SEC forms to fetch (default: 10-K 10-Q 8-K 'DEF 14A' 4)")
    build_parser.add_argument("--max-filings-per-form", type=int, default=50,
                             help="Maximum filings per form type (default: 50)")
    build_parser.add_argument("--force-rebuild", action="store_true",
                             help="Force full rebuild (ignore existing data)")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update existing dossier")
    update_parser.add_argument("ticker", help="Company ticker symbol")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check dossier status")
    status_parser.add_argument("ticker", help="Company ticker symbol")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List filings")
    list_parser.add_argument("ticker", help="Company ticker symbol")
    list_parser.add_argument("--form", help="Filter by form type (e.g., 10-K)")
    list_parser.add_argument("--since", help="Filter by date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # Common kwargs
    common_kwargs = {
        "workspace_root": args.workspace,
        "dossier_root": args.dossier_root
    }
    
    try:
        if args.command == "build":
            result = build_dossier(
                ticker=args.ticker,
                years=args.years,
                forms=args.forms,
                max_filings_per_form=args.max_filings_per_form,
                force_rebuild=args.force_rebuild,
                **common_kwargs
            )
            
            if result["summary"]["status"] == "success":
                print(f"✓ Dossier built successfully")
                print(f"  Ticker: {result['summary']['ticker']}")
                print(f"  Company: {result['summary']['company_name']}")
                print(f"  CIK: {result['summary']['cik']}")
                print(f"  Total filings: {result['summary']['total_filings']}")
                print(f"  Latest filing: {result['summary']['latest_filed_at']}")
                print(f"  Manifest: {result['manifest_path']}")
            else:
                print(f"✗ Failed to build dossier: {result['summary'].get('error')}")
                sys.exit(1)
        
        elif args.command == "update":
            result = update_dossier(ticker=args.ticker, **common_kwargs)
            
            if result["summary"]["status"] == "success":
                print(f"✓ Dossier updated successfully")
                print(f"  Total filings: {result['summary']['total_filings']}")
                print(f"  Latest filing: {result['summary']['latest_filed_at']}")
            else:
                print(f"✗ Failed to update dossier: {result['summary'].get('error')}")
                sys.exit(1)
        
        elif args.command == "status":
            result = status(ticker=args.ticker, **common_kwargs)
            
            if result["exists"]:
                print(f"Dossier Status for {result['ticker']}")
                print(f"  Company: {result['company_name']}")
                print(f"  CIK: {result['cik']}")
                print(f"  Total filings: {result['total_filings']}")
                print(f"  Latest filing: {result['latest_filed_at']}")
                print(f"  Last updated: {result['last_updated']}")
                print(f"  Manifest: {result['manifest_path']}")
            else:
                print(f"No dossier found for {result['ticker']}")
                sys.exit(1)
        
        elif args.command == "list":
            filings = list_filings(
                ticker=args.ticker,
                form=args.form,
                since=args.since,
                **common_kwargs
            )
            
            if not filings:
                print(f"No filings found for {args.ticker}")
                sys.exit(0)
            
            print(f"Found {len(filings)} filing(s) for {args.ticker}")
            print()
            
            for filing in sorted(filings, key=lambda f: f["filed_at"], reverse=True):
                print(f"{filing['form']:8} | {filing['filed_at'][:10]} | {filing['description'] or filing['primary_document']}")
                print(f"         | Viewer: {filing['viewer_url']}")
                print(f"         | Direct: {filing['url']}")
                print()
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
