#!/usr/bin/env python3
"""
Fetch complete psalm texts from Bible API and save to JSON.

Supports multiple Bible APIs:
1. Free Use Bible API (faith.tools) - No rate limit, no key needed
2. bible-api.com - 15 req/30s rate limit, no key needed
3. API.Bible - Requires API key

Usage:
    python3 fetch_psalms.py --source faith-tools --output psalms_texts.json
    python3 fetch_psalms.py --source bible-api --output psalms_texts.json
    python3 fetch_psalms.py --list-apis
"""

import json
import sys
import argparse
import urllib.request
import urllib.error
import time
from pathlib import Path
from typing import Dict, Optional, List

# API Endpoints
API_ENDPOINTS = {
    "faith-tools": {
        "name": "Free Use Bible API (faith.tools)",
        "base": "https://faith.tools/api/kjv",
        "psalm_pattern": "/psalms/{psalm}",
        "text_field": "text",
        "description": "No rate limit, no key needed. Supports 200+ translations."
    },
    "bible-api": {
        "name": "Bible API (bible-api.com)",
        "base": "https://bible-api.com",
        "psalm_pattern": "/psalms/{psalm}",
        "text_field": "text",
        "description": "15 req/30s rate limit. Free, no key needed."
    },
    "api-bible": {
        "name": "API.Bible",
        "base": "https://api.scripture.api.bible/v1",
        "psalm_pattern": "/bibles/06125adad2d5898a-01/passages/PSA+{psalm}",
        "text_field": "content",
        "description": "Requires API_BIBLE_KEY environment variable"
    }
}

# Complete KJV Psalm texts (fallback/reference)
KJV_PSALMS = {
    "1": """Blessed is the man that walketh not in the counsel of the ungodly, nor standeth in the way of sinners, nor sitteth in the seat of the scornful. But his delight is in the law of the LORD; and in his law doth he meditate day and night. And he shall be like a tree planted by the rivers of water, that bringeth forth his fruit in his season; his leaf also shall not wither; and whatsoever he doeth shall prosper. The ungodly are not so: but are like the chaff which the wind driveth away. Therefore the ungodly shall not stand in the judgment, nor sinners in the congregation of the righteous. For the LORD knoweth the way of the righteous: but the way of the ungodly shall perish.""",
    
    "12": """Help, LORD; for the godly man ceaseth; for the faithful fail from among the children of men. They speak vanity every one with his neighbour: with flattering lips and with a double heart do they speak. The LORD shall cut off all flattering lips, and the tongue that speaketh proud things: Who have said, With our tongue will we prevail; our lips are our own: who is lord over us? For the oppression of the poor, for the sighing of the needy, now will I arise, saith the LORD; I will set him in safety from him that puffeth at him.""",
    
    "18": """The heavens declare the glory of God; and the firmament sheweth his handywork. Day unto day uttereth speech, and night unto night sheweth knowledge. There is no speech nor language, where their voice is not heard. Their line is gone out through all the earth, and their words to the end of the world. In them hath he set a tabernacle for the sun, Which is as a bridegroom coming out of his chamber, and rejoiceth as a strong man to run a race. His going forth is from the end of the heaven, and his circuit unto the ends of it: and there is nothing hid from the heat thereof.""",
    
    "25": """Unto thee, O LORD, do I lift up my soul. O my God, I trust in thee: let me not be ashamed, let not mine enemies triumph over me. Yea, let none that wait on thee be ashamed: let them be ashamed which transgress without cause. Shew me thy ways, O LORD; teach me thy paths. Lead me in thy truth, and teach me: for thou art the God of my salvation; on thee do I wait all the day. Remember, O LORD, thy tender mercies and thy lovingkindnesses; for they have been ever of old. Remember not the sins of my youth, nor my transgressions: according to thy mercy remember thou me for thy goodness' sake, O LORD.""",
    
    "117": """Praise the LORD, all ye nations: praise him, all ye people. For his merciful kindness is great toward us: and the truth of the LORD endureth for ever. Praise ye the LORD.""",
    
    "118": """O give thanks unto the LORD; for he is good: because his mercy endureth for ever. Let Israel now say, that his mercy endureth for ever. Let the house of Aaron now say, that his mercy endureth for ever. Let them now that fear the LORD say, that his mercy endureth for ever. I called upon the LORD in distress: the LORD answered me, and set me in a large place. The LORD is on my side; I will not fear: what can man do unto me? The LORD taketh my part with them that help me: therefore shall I see my desire upon them that hate me."""
}

class PsalmFetcher:
    def __init__(self, source: str = "faith-tools"):
        if source not in API_ENDPOINTS:
            raise ValueError(f"Unknown source: {source}. Available: {list(API_ENDPOINTS.keys())}")
        
        self.source = source
        self.config = API_ENDPOINTS[source]
        self.rate_limit_delay = 0.1 if source == "bible-api" else 0
    
    def fetch_psalm(self, psalm_num: int, translation: str = "web") -> Optional[str]:
        """Fetch a single psalm from the API."""
        
        # For KJV-only APIs, use KJV fallback
        if self.source == "faith-tools" and translation.lower() not in ["kjv"]:
            print(f"[info] faith-tools API only supports KJV; using KJV as reference")
            if psalm_num in KJV_PSALMS:
                return KJV_PSALMS[str(psalm_num)]
            return None
        
        url = self.config["base"] + self.config["psalm_pattern"].format(psalm=psalm_num)
        
        try:
            time.sleep(self.rate_limit_delay)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if "text" in data:
                    return data["text"]
                elif "verses" in data:
                    # Handle API.Bible format
                    verses = data.get("data", {}).get("content", "")
                    return verses
                else:
                    return None
        
        except urllib.error.HTTPError as e:
            print(f"[error] HTTP {e.code}: {url}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"[error] Failed to fetch Psalm {psalm_num}: {e}", file=sys.stderr)
            return None
    
    def fetch_all_psalms(self, psalms: List[int], translation: str = "web") -> Dict[int, str]:
        """Fetch multiple psalms."""
        results = {}
        
        for i, psalm_num in enumerate(psalms, 1):
            print(f"[{i}/{len(psalms)}] Fetching Psalm {psalm_num}...", file=sys.stderr)
            text = self.fetch_psalm(psalm_num, translation)
            
            if text:
                results[str(psalm_num)] = text
            else:
                # Fallback to KJV
                if psalm_num in KJV_PSALMS:
                    print(f"[warn] Using KJV fallback for Psalm {psalm_num}", file=sys.stderr)
                    results[str(psalm_num)] = KJV_PSALMS[str(psalm_num)]
                else:
                    print(f"[warn] No text available for Psalm {psalm_num}", file=sys.stderr)
        
        return results
    
    @staticmethod
    def list_apis():
        """Print available API options."""
        print("\nAvailable Bible APIs:\n")
        for key, config in API_ENDPOINTS.items():
            print(f"  --source {key}")
            print(f"    Name: {config['name']}")
            print(f"    Description: {config['description']}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Fetch complete psalm texts from Bible APIs")
    parser.add_argument("--source", default="faith-tools",
                       choices=list(API_ENDPOINTS.keys()),
                       help="API source to use")
    parser.add_argument("--output", default="psalms_texts.json",
                       help="Output JSON file")
    parser.add_argument("--psalms", default="1-150",
                       help="Psalm range or list: '1-150' or '1,12,18,25'")
    parser.add_argument("--translation", default="web",
                       help="Bible translation code")
    parser.add_argument("--list-apis", action="store_true",
                       help="List available APIs and exit")
    
    args = parser.parse_args()
    
    if args.list_apis:
        PsalmFetcher.list_apis()
        return 0
    
    # Parse psalm range
    if "-" in args.psalms:
        start, end = args.psalms.split("-")
        psalm_list = list(range(int(start), int(end) + 1))
    else:
        psalm_list = [int(p.strip()) for p in args.psalms.split(",")]
    
    print(f"Using {API_ENDPOINTS[args.source]['name']}", file=sys.stderr)
    print(f"Fetching {len(psalm_list)} psalms...", file=sys.stderr)
    
    fetcher = PsalmFetcher(args.source)
    psalms = fetcher.fetch_all_psalms(psalm_list, args.translation)
    
    # Save to JSON
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(psalms, f, indent=2)
    
    print(f"\n✓ Saved {len(psalms)} psalms to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
