# This is Dhoni the fly side sweeper when he was officially rendered the UP 
# the first breakthrough transaction and sent out processing otherwise it does not


import requests
from flask import Flask, jsonify ,render_template, request

app = Flask(__name__)

# FastAPI server URL

FASTAPI_URL = "http://127.0.0.1:2233/transaction"

# ------------------------------------------------------------------------ 

# ------------------------------------------------------------------------ 
# renders the page no seriois 
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")
# ------------------------------------------------------------------------ 

# getting response from the websiete 
@app.route('/process_payment', methods=['POST'])
def process_payment():
    data = request.json  # Extract data sent from frontend
    
    transaction_data = {
        "amount": float(data.get("amount", 0)),
        "payer": {
            "vpa": data.get("payerVPA", "unknown@bank"),
            "authentication": {
                "upiPin": "encrypted_upi_pin"  # Simulated encrypted PIN
            },
            "deviceInfo": {
                "deviceId": "device12345",
                "deviceType": "mobile",
                "mobileCarrier": "CarrierName"
            },
            "geolocation": {
                "latitude": data.get("latitude", "18.5204"),  # Defaults to Pune
                "longitude": data.get("longitude", "73.8567")
            },
            "ipAddress": data.get("ipAddress", request.remote_addr),  # Capture user's IP
            "zipcode": data.get("zipcode", "411201")
        },
        "payee": {
            "vpa": data.get("payeeVPA", "unknown@bank")
        },
        "locationDetails": {
            "city": data.get("city", "Unknown"),
            "state": data.get("state", "Unknown"),
            "country": data.get("country", "Unknown")
        },
        "description": data.get("description", "No description"),
        "callbackUrl": "https://yourbank.com/callback"
    }

    print("The data which is arrived is"+str(dict(transaction_data)))
    try:
        response = requests.post(FASTAPI_URL, json=transaction_data)
        return jsonify(response.json())  # Return FastAPI response
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)})
    # return jsonify(transaction_data), 200  # Return JSON response


if __name__ == "__main__":
    app.run(port=5000, debug=True,host='0.0.0.0')
