"""
Initial setup script
This file adds default sources to the database
"""

from database import add_rss_source, add_scrape_source, get_rss_sources, get_scrape_sources
from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

def initialize_sources():
    """Add default sources to database"""
    print("\n" + "="*60)
    print("Initial setup of sources...")
    print("="*60 + "\n")
    
    # Check current sources
    current_rss = get_rss_sources()
    current_scrape = get_scrape_sources()
    
    print(f"Current status:")
    print(f"   RSS: {len(current_rss)} sources")
    print(f"   Scrape: {len(current_scrape)} sources\n")
    
    # Add RSS
    added_rss = 0
    for url in DEFAULT_RSS_SOURCES:
        if url not in current_rss:
            add_rss_source(url)
            added_rss += 1
            print(f"Added RSS: {url}")
    
    # Add Scrape
    added_scrape = 0
    for url in DEFAULT_SCRAPE_SITES:
        if url not in current_scrape:
            add_scrape_source(url)
            added_scrape += 1
            print(f"Added Scrape: {url}")
    
    print("\n" + "="*60)
    print(f"Setup complete!")
    print(f"   {added_rss} new RSS sources added")
    print(f"   {added_scrape} new Scrape sources added")
    print("="*60 + "\n")


if __name__ == "__main__":
    initialize_sources()
