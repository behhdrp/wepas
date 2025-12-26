import requests

print("Starting test")

# Test root
try:
    response = requests.get("http://127.0.0.1:8003/")
    print("Root Status Code:", response.status_code)
    print("Root Response:", response.text[:200])
except Exception as e:
    print("Root error:", e)

print("Testing API")

# Test API
url = "http://127.0.0.1:8003/api/transactions/pix/"
data = {
    "customer": {"name": "Teste", "email": "teste@example.com"},
    "amount": 10.00,
    "items": [{"description": "Item Teste", "quantity": 1, "price": 10.00}]
}

try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)
    try:
        print("Response JSON:", response.json())
    except:
        print("Not JSON")
except Exception as e:
    print("API error:", e)

print("Test done")