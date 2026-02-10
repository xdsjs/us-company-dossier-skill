#!/usr/bin/env python3
"""
Demo script for us_company_dossier skill.
This script demonstrates how to build a company dossier and perform a simple retrieval query.
"""

import os
import sys
import json
from pathlib import Path

# Add the skill directory to the path
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

from us_company_dossier import build_dossier, search_documents


def demo_build_dossier():
    """Build a dossier for a sample company (TSLA)"""
    print("Building dossier for TSLA...")
    
    # Build the dossier
    result = build_dossier(
        ticker="TSLA",
        years=1,  # Use 1 year for demo to be faster
        include_ir=True,
        normalize_level="light"
    )
    
    print(f"Dossier built successfully!")
    print(f"Path: {result['dossier_path']}")
    print(f"Downloaded: {result['summary']['downloaded_count']} files")
    print(f"Parsed successfully: {result['summary']['parsed_success']}")
    print(f"Latest filing date: {result['summary']['latest_filed_at']}")
    
    return result['dossier_path']


def demo_search(dossier_path):
    """Perform a simple search on the built dossier"""
    print("\nSearching for information about 'competition' in TSLA filings...")
    
    # Search for competition-related information
    results = search_documents(
        dossier_path=dossier_path,
        query="competition"
    )
    
    if results:
        print(f"Found {len(results)} relevant chunks:")
        for i, result in enumerate(results[:3], 1):  # Show top 3 results
            print(f"\n{i}. Source: {result['source_url']}")
            print(f"   Section: {result.get('section_path', 'N/A')}")
            print(f"   Content preview: {result['content'][:200]}...")
    else:
        print("No results found.")


def main():
    """Run the full demo"""
    try:
        # Build the dossier
        dossier_path = demo_build_dossier()
        
        # Perform a search
        demo_search(dossier_path)
        
        print("\nDemo completed successfully!")
        print(f"Full dossier available at: {dossier_path}")
        
    except Exception as e:
        print(f"Error during demo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()