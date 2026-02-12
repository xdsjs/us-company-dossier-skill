#!/usr/bin/env python3
"""
CLI wrapper for us_company_dossier skill
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Add the skill directory to Python path
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

# Load .env from workspace (project root = clawd, or cwd)
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

# Import the optimized version
from us_company_dossier import build_dossier, update_dossier, status, list_artifacts


def main():
    parser = argparse.ArgumentParser(description="US Company Dossier Builder")
    parser.add_argument("--workspace", default=os.getenv("WORKSPACE_ROOT", os.getcwd()),
                       help="Workspace root directory")
    parser.add_argument("--dossier-root", default=os.getenv("DOSSIER_ROOT"),
                       help="Dossier output directory (overrides DOSSIER_ROOT env)")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Build company dossier")
    build_parser.add_argument("ticker", help="Company ticker symbol")
    build_parser.add_argument("--years", type=int, default=3, help="Number of years to fetch")
    build_parser.add_argument("--forms", nargs="+", default=["10-K", "10-Q", "8-K", "DEF 14A", "4"],
                             help="SEC forms to fetch")
    build_parser.add_argument("--include-ir", action="store_true", default=True,
                             help="Include IR materials")
    build_parser.add_argument("--max-filings-per-form", type=int, default=50,
                             help="Maximum filings per form")
    build_parser.add_argument("--force-rebuild", action="store_true", default=False,
                             help="Force rebuild even if cached")
    build_parser.add_argument("--normalize-level", choices=["none", "light", "deep"], 
                             default="light", help="Normalization level")
    build_parser.add_argument("--fetch-mode", choices=["http", "browser_fallback"], 
                             default="http", help="Fetch mode")
    build_parser.add_argument("--download-mode", choices=["full", "links_only"], 
                             default="links_only", help="Download mode: links_only (default) or full")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update company dossier")
    update_parser.add_argument("ticker", help="Company ticker symbol")
    update_parser.add_argument("--years", type=int, default=3, help="Number of years to fetch")
    update_parser.add_argument("--forms", nargs="+", default=["10-K", "10-Q", "8-K", "DEF 14A", "4"],
                              help="SEC forms to fetch")
    update_parser.add_argument("--include-ir", action="store_true", default=True,
                              help="Include IR materials")
    update_parser.add_argument("--max-filings-per-form", type=int, default=50,
                              help="Maximum filings per form")
    update_parser.add_argument("--normalize-level", choices=["none", "light", "deep"], 
                              default="light", help="Normalization level")
    update_parser.add_argument("--fetch-mode", choices=["http", "browser_fallback"], 
                              default="http", help="Fetch mode")
    update_parser.add_argument("--download-mode", choices=["full", "links_only"], 
                              default="links_only", help="Download mode: links_only (default) or full")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get dossier status")
    status_parser.add_argument("ticker", help="Company ticker symbol")
    
    # List artifacts command
    list_parser = subparsers.add_parser("list", help="List artifacts")
    list_parser.add_argument("ticker", help="Company ticker symbol")
    list_parser.add_argument("--form", help="Filter by form type")
    list_parser.add_argument("--type", help="Filter by artifact type")
    list_parser.add_argument("--since", help="Filter by date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # Set workspace root
    os.environ["WORKSPACE_ROOT"] = args.workspace
    if args.dossier_root:
        os.environ["DOSSIER_ROOT"] = args.dossier_root

    try:
        if args.command == "build":
            result = build_dossier(
                ticker=args.ticker,
                years=args.years,
                forms=args.forms,
                include_ir=args.include_ir,
                max_filings_per_form=args.max_filings_per_form,
                force_rebuild=args.force_rebuild,
                normalize_level=args.normalize_level,
                fetch_mode=args.fetch_mode,
                download_mode=args.download_mode,
                dossier_root=args.dossier_root
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == "update":
            result = update_dossier(
                ticker=args.ticker,
                years=args.years,
                forms=args.forms,
                include_ir=args.include_ir,
                max_filings_per_form=args.max_filings_per_form,
                normalize_level=args.normalize_level,
                fetch_mode=args.fetch_mode,
                download_mode=args.download_mode,
                dossier_root=args.dossier_root
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == "status":
            result = status(args.ticker, dossier_root=args.dossier_root)
            print(json.dumps(result, indent=2))
            
        elif args.command == "list":
            filters = {}
            if args.form:
                filters["form"] = args.form
            if args.type:
                filters["type"] = args.type
            if args.since:
                filters["since"] = args.since
                
            result = list_artifacts(args.ticker, filters, dossier_root=args.dossier_root)
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()