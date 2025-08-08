import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import os

def scrape_devam_project():
    """Scrape images and video URLs from devamproject.com"""
    
    base_url = "https://www.devamproject.com"
    
    try:
        # Make request with headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fetching content from {base_url}...")
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"Status code: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract image URLs
        print("\nExtracting images...")
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            if src:
                # Convert relative URLs to absolute URLs
                full_url = urljoin(base_url, src)
                
                # Get alt text and other attributes
                alt_text = img.get('alt', '')
                title = img.get('title', '')
                
                images.append({
                    'url': full_url,
                    'alt': alt_text,
                    'title': title,
                    'original_src': src
                })
        
        # Extract video URLs
        print("Extracting videos...")
        videos = []
        
        # Check for video tags
        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src')
            if src:
                full_url = urljoin(base_url, src)
                videos.append({
                    'url': full_url,
                    'type': 'video',
                    'original_src': src
                })
            
            # Check for source tags within video
            source_tags = video.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    videos.append({
                        'url': full_url,
                        'type': source.get('type', 'video'),
                        'original_src': src
                    })
        
        # Check for iframe videos (YouTube, Vimeo, etc.)
        iframe_tags = soup.find_all('iframe')
        for iframe in iframe_tags:
            src = iframe.get('src')
            if src and ('youtube' in src or 'vimeo' in src or 'video' in src.lower()):
                videos.append({
                    'url': src,
                    'type': 'iframe',
                    'original_src': src
                })
        
        # Results summary
        print(f"\nFound {len(images)} images and {len(videos)} videos")
        
        # Create data structure
        scraped_data = {
            'source_url': base_url,
            'scraped_at': response.headers.get('date', ''),
            'images': images,
            'videos': videos,
            'total_images': len(images),
            'total_videos': len(videos)
        }
        
        return scraped_data
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the webpage: {e}")
        return None

def save_data_to_json(data, filename='devam_scraped_data.json'):
    """Save scraped data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nData saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def display_results(data):
    """Display the scraped results"""
    if not data:
        return
    
    print(f"\n{'='*50}")
    print(f"SCRAPING RESULTS FROM {data['source_url']}")
    print(f"{'='*50}")
    
    print(f"\nIMAGES FOUND ({data['total_images']}):")
    print("-" * 30)
    for i, img in enumerate(data['images'][:10], 1):  # Show first 10
        print(f"{i}. {img['url']}")
        if img['alt']:
            print(f"   Alt: {img['alt']}")
        if img['title']:
            print(f"   Title: {img['title']}")
        print()
    
    if len(data['images']) > 10:
        print(f"... and {len(data['images']) - 10} more images")
    
    print(f"\nVIDEOS FOUND ({data['total_videos']}):")
    print("-" * 30)
    for i, video in enumerate(data['videos'], 1):
        print(f"{i}. {video['url']}")
        print(f"   Type: {video['type']}")
        print()

if __name__ == "__main__":
    print("Scraping devamproject.com for images and videos...")
    
    # Scrape the data
    data = scrape_devam_project()
    
    if data:
        # Display results
        display_results(data)
        
        # Save to JSON file
        save_data_to_json(data)
        
        print(f"\nScraping completed successfully!")
        print(f"You can find the detailed data in 'devam_scraped_data.json'")
    else:
        print("Scraping failed. Please check the website URL and try again.")
