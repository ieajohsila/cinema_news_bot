"""
Startup script for the bot
Initializes default sources if needed and runs the main bot
"""

import os
from database import get_rss_sources, get_scrape_sources, add_rss_source, add_scrape_source
from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

def initialize_if_needed():
    """Add default sources if database is empty"""
    
    print("\n" + "="*70)
    print("Checking sources...")
    print("="*70)
    
    current_rss = get_rss_sources()
    current_scrape = get_scrape_sources()
    
    print(f"Current status:")
    print(f"   RSS sources: {len(current_rss)}")
    print(f"   Scrape sources: {len(current_scrape)}")
    
    # If no sources exist, add defaults
    if len(current_rss) == 0 and len(current_scrape) == 0:
        print("\nNo sources found. Adding default sources...")
        
        # Add RSS sources
        added_rss = 0
        for url in DEFAULT_RSS_SOURCES:
            try:
                add_rss_source(url)
                added_rss += 1
                print(f"   Added RSS: {url[:50]}...")
            except Exception as e:
                print(f"   Error adding {url}: {e}")
        
        # Add Scrape sources
        added_scrape = 0
        for url in DEFAULT_SCRAPE_SITES:
            try:
                add_scrape_source(url)
                added_scrape += 1
                print(f"   Added Scrape: {url[:50]}...")
            except Exception as e:
                print(f"   Error adding {url}: {e}")
        
        print(f"\nInitialization complete!")
        print(f"   {added_rss} RSS sources added")
        print(f"   {added_scrape} Scrape sources added")
    else:
        print("\nSources already configured.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    # Initialize sources
    initialize_if_needed()
    
    # Run the bot
    print("Starting bot...\n")
    
    # Import and run main
    from main import main
    main()
