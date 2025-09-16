import re

# Read the product_list.html file
with open(r'e:\Python Django\pjp_new\core\templates\product_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all price and data-id pairs
price_pattern = r'<p class="mb-2">₹(\d+)</p>'
id_pattern = r'data-id="(\d+)"'

prices = re.findall(price_pattern, content)
ids = re.findall(id_pattern, content)

# Create price mapping
price_mapping = {}
for i in range(min(len(prices), len(ids))):
    price_mapping[ids[i]] = int(prices[i])

# Print the mapping in JavaScript format
print("const PRICES = {")
for product_id, price in sorted(price_mapping.items(), key=lambda x: int(x[0])):
    print(f"  '{product_id}': {price},")
print("};")

print(f"\nTotal products: {len(price_mapping)}")
