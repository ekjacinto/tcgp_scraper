import requests
import json
import re
from bs4 import BeautifulSoup

# Order for sets
set_order = {
    'A1': 1,
    'A1a': 2,
    'A2': 3,
    'A2a': 4,
    'A2b' : 5,
    'A3': 6,
    'P-A': 7,
}

# Extract card data from single card page
def extract_card_data(card_url):
    response = requests.get(card_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract card name
        card_name_tag = soup.find('span', class_='card-text-name')
        card_name = card_name_tag.text.strip() if card_name_tag else 'Unknown Name'
        
        # Extract card image URL
        card_image_tag = soup.find('img', class_='card shadow resp-w')
        card_image_url = card_image_tag['src'] if card_image_tag else 'No Image URL'
        
        # Extract card description
        card_description_tag = soup.find('div', class_='card-text-flavor')
        card_description = card_description_tag.text.strip() if card_description_tag else 'No Description'
        
        # Extract rarity symbols and card number (from prints-current-details span)
        rarity_tag = soup.find('div', class_='prints-current-details')
        rarity_symbols = ''
        card_number = None
        
        if rarity_tag:
            rarity_span = rarity_tag.find_all('span')
            if rarity_span:
                # Extract rarity from second span
                rarity_text = rarity_span[1].text.strip()
                
                # Extract card number
                number_match = re.search(r'#(\d+)', rarity_text)
                if number_match:
                    card_number = int(number_match.group(1))
                
                # Remove card number and any "pack" related text
                rarity_symbols = re.sub(r'#\d+ · ', '', rarity_text)
                rarity_symbols = remove_pack_text(rarity_symbols)

        return [card_name, card_url, card_image_url, card_description, rarity_symbols, card_number]
    return None

def remove_pack_text(rarity_text):
    return re.sub(r' · \w+  pack', '', rarity_text).strip()

# Extract card number from rarity symbols (e.g., "#45 · ◊◊◊◊")
def extract_card_number(rarity_symbols):
    match = re.search(r'#(\d+)', rarity_symbols)
    return int(match.group(1)) if match else float('inf')  # Return a large number if no match

# Get all card URLs dynamically from a set's main page
def get_all_card_urls(set_code):
    base_url = f'https://pocket.limitlesstcg.com/cards/{set_code}/'
    response = requests.get(base_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all card links
        card_links = soup.select('a[href^="/cards/"]')
        
        # Construct full card URLs
        card_urls = [f"https://pocket.limitlesstcg.com{link['href']}" for link in card_links if 'href' in link.attrs]
        
        # Remove duplicates
        return list(set(card_urls))  
    return []

def replace_crown_symbol(rarity_text):
    return rarity_text.replace('Crown Rare', '♕')

# List of sets to scrape
sets = ['A3','A2b', 'A2a', 'A2', 'A1a', 'A1', 'P-A']

json_filename = "cards.json"

# List to store all card data
card_data_list = []

# Iterate over each set
for card_set in sets:
    print(f"Scraping set: {card_set}...")
    card_urls = get_all_card_urls(card_set)
    
    if not card_urls:
        print(f"No cards found for set {card_set}")
        continue

    for card_url in card_urls:
        card_data = extract_card_data(card_url)
        if card_data:
            card_info = {
                'name': card_data[0],
                'url': card_data[1],
                'image_url': card_data[2],
                'description': card_data[3],
                'rarity_symbols': 'Promo' if card_set == 'P-A' else card_data[4],
                'card_number': card_data[5],
                'set': card_set
            }
            if 'Crown Rare' in card_info['rarity_symbols'] and card_set != 'P-A':
                card_info['rarity_symbols'] = replace_crown_symbol(card_info['rarity_symbols'])
            card_data_list.append(card_info)
            print(f"Saved: {card_data[0]} from {card_set}")

# Sort cards first by set order, then by card number
card_data_list.sort(key=lambda card: (set_order.get(card['set'], float('inf')), card['card_number'] if card['card_number'] is not None else float('inf')))

# Write data to JSON file
with open(json_filename, 'w', encoding='utf-8') as file:
    json.dump(card_data_list, file, ensure_ascii=False, indent=2)

print(f"Scraping complete. Data saved to {json_filename}")
