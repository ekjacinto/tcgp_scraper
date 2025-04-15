import requests
import csv
import re
from bs4 import BeautifulSoup

# Order for the sets
set_order = {
    'A1': 1,
    'A1a': 2,
    'A2': 3,
    'A2a': 4,
    'A2b' : 5,
    'P-A': 6,
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
        
        # Extract rarity symbols (from prints-current-details span)
        rarity_tag = soup.find('div', class_='prints-current-details')
        rarity_symbols = ''
        
        if rarity_tag:
            rarity_span = rarity_tag.find_all('span')
            if rarity_span:
                # Extract rarity from second span
                rarity_symbols = rarity_span[1].text.strip()  

                # Remove any "pack" related text ("· Charizard pack", "· Arceus pack")
                rarity_symbols = remove_pack_text(rarity_symbols)

        return [card_name, card_url, card_image_url, card_description, rarity_symbols]
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
sets = ['A2b', 'A2a', 'A2', 'A1a', 'A1', 'P-A']

csv_filename = "cards.csv"

# Open CSV file to write data
card_data_list = []
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    #  Header row
    writer.writerow(['Card Name', 'Card URL', 'Image URL', 'Description', 'Rarity Symbols'])
    
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
                card_data_list.append({
                    'name': card_data[0],
                    'url': card_data[1],
                    'image_url': card_data[2],
                    'description': card_data[3],
                    'rarity_symbols': card_data[4],
                    'set': card_set
                })
                print(f"Saved: {card_data[0]} from {card_set}")

    # Sort cards first by set order, then by card number
    card_data_list.sort(key=lambda card: (set_order.get(card['set'], float('inf')), extract_card_number(card['rarity_symbols'])))

    # Write sorted data to CSV
    for card in card_data_list:
        if 'Crown Rare' in card['rarity_symbols']:
            card['rarity_symbols'] = replace_crown_symbol(card['rarity_symbols'])
        writer.writerow([card['name'], card['url'], card['image_url'], card['description'], card['rarity_symbols']])

print(f"Scraping complete. Data saved to {csv_filename}")
