import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
cred = credentials.Certificate('service-key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Read the cards from JSON file
print("Reading cards.json...")
with open('cards.json', 'r', encoding='utf-8') as file:
    cards = json.load(file)

# Upload to Firestore
print("Uploading to Firestore...")
for card in cards:
    # Create a document reference with padded card number
    card_number = card['card_number'] if card['card_number'] is not None else 'unknown'
    if card_number != 'unknown':
        # Pad the card number with leading zeros to 3 digits
        padded_number = f"{card_number:03d}"
        doc_id = f"{card['set']}_{padded_number}"
    else:
        doc_id = f"{card['set']}_{card_number}"
    
    # Add the card to Firestore
    db.collection('cards').document(doc_id).set(card)
    print(f"Uploaded: {card['name']} ({doc_id})")

print("Upload complete!") 