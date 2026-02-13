#!/usr/bin/env python3
"""
Demo script for US Company Dossier Skill (Simplified - Links Only)
Shows basic usage examples for building SEC filing metadata dossiers.
"""

import os
import sys
from pathlib import Path

# Add skill directory to path
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

from us_company_dossier import build_dossier, update_dossier, status, list_filings


def demo_basic_build():
    """Demo: Basic dossier build"""
    print("=" * 60)
    print("Demo 1: Basic Dossier Build")
    print("=" * 60)
    
    result = build_dossier(
        ticker="AAPL",
        years=3
    )
    
    if result["summary"]["status"] == "success":
        print(f"✓ Built dossier for {result['summary']['ticker']}")
        print(f"  Company: {result['summary']['company_name']}")
        print(f"  Total filings: {result['summary']['total_filings']}")
        print(f"  Manifest: {result['manifest_path']}")
    else:
        print(f"✗ Failed: {result['summary'].get('error')}")
    
    print()


def demo_custom_forms():
    """Demo: Custom form types"""
    print("=" * 60)
    print("Demo 2: Custom Form Types (only 10-K and 10-Q)")
    print("=" * 60)
    
    result = build_dossier(
        ticker="TSLA",
        years=2,
        forms=["10-K", "10-Q"],
        max_filings_per_form=10
    )
    
    if result["summary"]["status"] == "success":
        print(f"✓ Built dossier for {result['summary']['ticker']}")
        print(f"  Total filings: {result['summary']['total_filings']}")
    
    print()


def demo_status_check():
    """Demo: Check dossier status"""
    print("=" * 60)
    print("Demo 3: Check Dossier Status")
    print("=" * 60)
    
    result = status(ticker="AAPL")
    
    if result["exists"]:
        print(f"Dossier exists for {result['ticker']}")
        print(f"  Company: {result['company_name']}")
        print(f"  CIK: {result['cik']}")
        print(f"  Total filings: {result['total_filings']}")
        print(f"  Latest filing: {result['latest_filed_at']}")
    else:
        print(f"No dossier found for {result['ticker']}")
    
    print()


def demo_list_filings():
    """Demo: List filings with filters"""
    print("=" * 60)
    print("Demo 4: List Filings (10-K only)")
    print("=" * 60)
    
    filings = list_filings(ticker="AAPL", form="10-K")
    
    print(f"Found {len(filings)} 10-K filing(s)")
    for filing in filings[:3]:  # Show first 3
        print(f"  {filing['filed_at'][:10]} - {filing['description']}")
        print(f"    Viewer: {filing['viewer_url']}")
    
    print()


def demo_update():
    """Demo: Update existing dossier"""
    print("=" * 60)
    print("Demo 5: Update Existing Dossier")
    print("=" * 60)
    
    result = update_dossier(ticker="AAPL")
    
    if result["summary"]["status"] == "success":
        print(f"✓ Updated dossier for {result['summary']['ticker']}")
        print(f"  Total filings: {result['summary']['total_filings']}")
    
    print()


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("US Company Dossier Skill - Demo")
    print("Simplified Version - Links Only Mode")
    print("=" * 60 + "\n")
    
    # Check SEC_USER_AGENT is set
    if not os.getenv("SEC_USER_AGENT"):
        print("⚠️  Warning: SEC_USER_AGENT not set in environment")
        print("   Using default (you should set this in .env)")
        print()
    
    try:
        # Run demos
        demo_basic_build()
        demo_custom_forms()
        demo_status_check()
        demo_list_filings()
        demo_update()
        
        print("=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
