import xmlrpc.client
import gnupg
import os
import getpass

# Define directory and file paths
HOME_DIR = os.path.expanduser("~")
ODOO_DIR = os.path.join(HOME_DIR, ".odoo")
API_KEY_FILE = os.path.join(ODOO_DIR, "api_key.gpg")
DECRYPTED_FILE = os.path.join(ODOO_DIR, "api_key.txt")
USERNAME_FILE = os.path.join(ODOO_DIR, "username.txt")
URL_FILE = os.path.join(ODOO_DIR, "odoo_url.txt")
DB_FILE = os.path.join(ODOO_DIR, "odoo_db.txt")

# Ensure the directory exists
if not os.path.exists(ODOO_DIR):
    os.makedirs(ODOO_DIR, mode=0o700)  # Secure permissions

# Initialize GPG
GPG = gnupg.GPG()

# Function to store text data (URL, DB, username)
def store_text_data(file_path, data):
    with open(file_path, "w") as f:
        f.write(data)

# Function to retrieve stored text data
def get_stored_text(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read().strip()
    return None

# Check if Odoo URL is stored
URL = get_stored_text(URL_FILE)
if not URL:
    print("If you want to paste the URL, E-mail address or API key into this terminal, use Ctrl + SHIFT + V")
    URL = input("Enter your Odoo server URL (e.g., https://yourcompany.odoo.com): ").strip()
    store_text_data(URL_FILE, URL)
    print("Odoo URL stored.")

# Check if Database (DB) is stored
DB = get_stored_text(DB_FILE)
if not DB:
    DB = input("Enter your Odoo database name: ").strip()
    store_text_data(DB_FILE, DB)
    print("Odoo database name stored.")

# Check if username is stored
USERNAME = get_stored_text(USERNAME_FILE)
if not USERNAME:
    USERNAME = input("Enter your Odoo username: ").strip()
    store_text_data(USERNAME_FILE, USERNAME)
    print("Username stored.")

# Function to store API key securely
def store_api_key(api_key, password):
    encrypted_data = GPG.encrypt(api_key, recipients=None, passphrase=password, symmetric=True)
    with open(API_KEY_FILE, "wb") as f:
        f.write(encrypted_data.data)

# Function to retrieve the API key
def get_api_key(password):
    if not os.path.exists(API_KEY_FILE):
        print("Error: No encrypted API key found.")
        exit()
    
    with open(API_KEY_FILE, "rb") as f:
        decrypted_data = GPG.decrypt_file(f, passphrase=password)
    
    if not decrypted_data.ok:
        print("Error: Incorrect password or decryption failed.")
        exit()
    
    decrypted_key = str(decrypted_data).strip()  # Ensure it's clean
    
    if not decrypted_key:
        print("Error: Decryption succeeded but API key is empty.")
        exit()
    
    return decrypted_key  # Use this clean API key

# Function to securely delete decrypted file
def cleanup():
    if os.path.exists(DECRYPTED_FILE):
        os.remove(DECRYPTED_FILE)

# Check if API key is already stored
if not os.path.exists(API_KEY_FILE):
    PASSWORD = getpass.getpass("Enter a new password to secure your API key: ")
    API_KEY = getpass.getpass("Enter your Odoo generated API key: ")
    store_api_key(API_KEY, PASSWORD)
    print("API key encrypted and stored securely.")
    exit()

# User authentication for decryption
PASSWORD = getpass.getpass("Enter your password to decrypt the API key: ")
API_KEY = get_api_key(PASSWORD)

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
ud = common.authenticate(DB, USERNAME, API_KEY, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

if not ud:
    print("Authentication failed. Please check your credentials.")
    cleanup()
    exit()

# Get user input for locations
input_location = input("Enter the name of the input location: ")
stock_location = input("Enter the name of the stock location: ")

# Function to get location ID from name, including hierarchical names
def get_location_id(location_name):
    locations = models.execute_kw(DB, ud, API_KEY, 'stock.location', 'search_read', [[['complete_name', 'ilike', location_name]]], {'fields': ['id', 'complete_name']})
    return locations[0]['id'] if locations else None

input_location_id = get_location_id(input_location)
stock_location_id = get_location_id(stock_location)

if not input_location_id or not stock_location_id:
    print("Error: One or both locations were not found.")
    cleanup()
    exit()

# Get all stock moves from both locations
all_moves = models.execute_kw(DB, ud, API_KEY, 'stock.quant', 'search_read', [
    [['location_id', 'in', [input_location_id, stock_location_id]], ['lot_id', '!=', False]]
], {'fields': ['product_id', 'lot_id', 'quantity', 'location_id']})

# Organize stock data by lot ID
lot_dict = {}
for move in all_moves:
    lot_id = move['lot_id'][0]
    if lot_id not in lot_dict:
        lot_dict[lot_id] = []
    lot_dict[lot_id].append(move)

duplicates = []

# Check for duplicate lot IDs across locations
for lot_id, moves in lot_dict.items():
    if len(moves) > 1:  # More than one occurrence means a duplicate
        for move in moves:
            product = models.execute_kw(DB, ud, API_KEY, 'product.product', 'read', [[move['product_id'][0]]], {'fields': ['name', 'default_code']})[0]
            lot = models.execute_kw(DB, ud, API_KEY, 'stock.lot', 'read', [[lot_id]], {'fields': ['name']})[0]
            location = models.execute_kw(DB, ud, API_KEY, 'stock.location', 'read', [[move['location_id'][0]]], {'fields': ['complete_name']})[0]
            
            duplicates.append({
                "Product Name": product['name'],
                "Internal Reference": product.get('default_code', ''),
                "Lot/Serial Number": lot['name'],
                "Location": location['complete_name'],
                "Quantity": move['quantity'],
            })

# Print results
if duplicates:
    print("Duplicate Serial Numbers Found:")
    for d in duplicates:
        print(d)
else:
    print("No duplicates found.")

# Clean up decrypted file
cleanup()
