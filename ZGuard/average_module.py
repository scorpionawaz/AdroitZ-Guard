import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import json
from datetime import datetime

def preprocess_text(text):
    return " ".join(text.lower().split())

def time_to_minutes(timestamp):
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    return dt.hour * 60 + dt.minute

def prepare_dataset(transactions):
    df = pd.DataFrame(transactions)
    df["time_in_minutes"] = df["date_time_stamp"].apply(time_to_minutes)
    df["transaction_note"] = df["transaction_note"].fillna("Unknown").apply(preprocess_text)
    return df

def train_model(df):
    X_train = df[["transaction_amount", "time_in_minutes"]].values
    model = IsolationForest(contamination=0.2, random_state=42)
    model.fit(X_train)
    return model

def check_transaction(new_tx, df, model):
    reasons = []
    new_tx_time = time_to_minutes(new_tx["date_time_stamp"])
    is_new_location = new_tx["payer_location_zip"] not in df["payer_location_zip"].values
    is_new_upi = new_tx["receiver_vpa"] not in df["receiver_vpa"].values
    new_tx_vector = np.array([[new_tx["transaction_amount"], new_tx_time]])
    is_amount_anomaly = model.predict(new_tx_vector)[0] == -1
    
    if is_amount_anomaly:
        reasons.append("Due to high amount, this is fraud.")
    if is_new_location and new_tx["transaction_amount"] > df["transaction_amount"].mean() * 1.5:
        reasons.append("New location and significantly high amount, potential fraud.")
    if is_new_upi and new_tx["transaction_amount"] > df["transaction_amount"].mean() * 2:
        reasons.append("New UPI ID with an unusually high transaction amount, possible fraud.")
    
    is_fraud = bool(reasons)
    return {
        "is_fraudulent": is_fraud,
        "reasons": reasons
    }

def is_the_user_normal(transactions, new_transaction):
    df = prepare_dataset(transactions[:100])  # Use top 100 recent transactions
    model = train_model(df)
    result = check_transaction(new_transaction, df, model)
    return json.dumps(result, indent=4)

# Example usage
transactions = [
    {"receiver_vpa": "petrol@hpcl", "transaction_amount": 1200.00, "date_time_stamp": "2025-02-23 08:15:02", "payer_location_zip": "411021", "transaction_note": "Petrol at HP Pump"},
    {"receiver_vpa": "buspass@msrtc", "transaction_amount": 500.00, "date_time_stamp": "2025-02-24 09:00:02", "payer_location_zip": "411111", "transaction_note": "Monthly Bus Pass"},
    {"receiver_vpa": "canteen@iitp", "transaction_amount": 150.00, "date_time_stamp": "2025-02-25 12:30:02", "payer_location_zip": "411032", "transaction_note": "Lunch at IIT Canteen"},
    {"receiver_vpa": "clothes@max", "transaction_amount": 2500.00, "date_time_stamp": "2025-02-26 16:45:02", "payer_location_zip": "411045", "transaction_note": "Clothes at Max Fashion"},
    {"receiver_vpa": "movies@pvr", "transaction_amount": 300.00, "date_time_stamp": "2025-02-27 19:00:02", "payer_location_zip": "411021", "transaction_note": "Movie at PVR Cinemas"},
    {"receiver_vpa": "gym@fitness", "transaction_amount": 800.00, "date_time_stamp": "2025-02-28 07:30:02", "payer_location_zip": "411111", "transaction_note": "Monthly Gym Fee"},
    {"receiver_vpa": "medical@apollo", "transaction_amount": 1200.00, "date_time_stamp": "2025-03-01 11:00:02", "payer_location_zip": "411032", "transaction_note": "Medical Checkup at Apollo"},
    {"receiver_vpa": "electronics@croma", "transaction_amount": 4500.00, "date_time_stamp": "2025-03-02 14:00:02", "payer_location_zip": "411045", "transaction_note": "Headphones at Croma"},
    {"receiver_vpa": "petrol@indianoil", "transaction_amount": 900.00, "date_time_stamp": "2025-03-03 18:30:02", "payer_location_zip": "411021", "transaction_note": "Petrol at Indian Oil"},
    {"receiver_vpa": "buspass@msrtc", "transaction_amount": 600.00, "date_time_stamp": "2025-03-04 08:45:02", "payer_location_zip": "411111", "transaction_note": "Monthly Bus Pass"},
    {"receiver_vpa": "canteen@college", "transaction_amount": 200.00, "date_time_stamp": "2025-03-05 13:15:02", "payer_location_zip": "411032", "transaction_note": "Snacks at College Canteen"},
    {"receiver_vpa": "clothes@pantaloons", "transaction_amount": 1800.00, "date_time_stamp": "2025-03-06 17:30:02", "payer_location_zip": "411045", "transaction_note": "Clothes at Pantaloons"},
    {"receiver_vpa": "movies@inox", "transaction_amount": 350.00, "date_time_stamp": "2025-03-07 20:00:02", "payer_location_zip": "411021", "transaction_note": "Movie at INOX"},
    {"receiver_vpa": "gym@fitlife", "transaction_amount": 1000.00, "date_time_stamp": "2025-03-08 06:45:02", "payer_location_zip": "411111", "transaction_note": "Monthly Gym Fee"},
    {"receiver_vpa": "medical@fortis", "transaction_amount": 1500.00, "date_time_stamp": "2025-03-09 10:30:02", "payer_location_zip": "411032", "transaction_note": "Medical Test at Fortis"},
    {"receiver_vpa": "electronics@reliancedigital", "transaction_amount": 6000.00, "date_time_stamp": "2025-03-10 15:00:02", "payer_location_zip": "411045", "transaction_note": "Laptop at Reliance Digital"},
    {"receiver_vpa": "petrol@bharatpetrol", "transaction_amount": 1100.00, "date_time_stamp": "2025-03-11 19:15:02", "payer_location_zip": "411021", "transaction_note": "Petrol at Bharat Petroleum"},
    {"receiver_vpa": "buspass@msrtc", "transaction_amount": 550.00, "date_time_stamp": "2025-03-12 09:30:02", "payer_location_zip": "411111", "transaction_note": "Monthly Bus Pass"},
    {"receiver_vpa": "canteen@office", "transaction_amount": 180.00, "date_time_stamp": "2025-03-13 12:45:02", "payer_location_zip": "411032", "transaction_note": "Lunch at Office Canteen"},
    {"receiver_vpa": "clothes@westside", "transaction_amount": 2200.00, "date_time_stamp": "2025-03-14 16:00:02", "payer_location_zip": "411045", "transaction_note": "Clothes at Westside"},
    {"receiver_vpa": "movies@cinepolis", "transaction_amount": 400.00, "date_time_stamp": "2025-03-15 18:30:02", "payer_location_zip": "411021", "transaction_note": "Movie at Cinepolis"},
    {"receiver_vpa": "gym@goldgym", "transaction_amount": 1200.00, "date_time_stamp": "2025-03-16 07:00:02", "payer_location_zip": "411111", "transaction_note": "Monthly Gym Fee"},
    {"receiver_vpa": "medical@manipal", "transaction_amount": 2000.00, "date_time_stamp": "2025-03-17 11:45:02", "payer_location_zip": "411032", "transaction_note": "Medical Consultation at Manipal"},
    {"receiver_vpa": "electronics@vijaysales", "transaction_amount": 8000.00, "date_time_stamp": "2025-03-18 14:30:02", "payer_location_zip": "411045", "transaction_note": "TV at Vijay Sales"},
    {"receiver_vpa": "petrol@shell", "transaction_amount": 1300.00, "date_time_stamp": "2025-03-19 20:00:02", "payer_location_zip": "411021", "transaction_note": "Petrol at Shell"},
    {"receiver_vpa": "buspass@msrtc", "transaction_amount": 700.00, "date_time_stamp": "2025-03-20 08:15:02", "payer_location_zip": "411111", "transaction_note": "Monthly Bus Pass"},
    {"receiver_vpa": "canteen@school", "transaction_amount": 250.00, "date_time_stamp": "2025-03-21 13:00:02", "payer_location_zip": "411032", "transaction_note": "Lunch at School Canteen"},
    {"receiver_vpa": "clothes@lifestyle", "transaction_amount": 3000.00, "date_time_stamp": "2025-03-22 15:45:02", "payer_location_zip": "411045", "transaction_note": "Clothes at Lifestyle"},
    {"receiver_vpa": "movies@fun", "transaction_amount": 450.00, "date_time_stamp": "2025-03-23 19:30:02", "payer_location_zip": "411021", "transaction_note": "Movie at Fun Cinemas"},
    {"receiver_vpa": "gym@anytime", "transaction_amount": 1500.00, "date_time_stamp": "2025-03-24 06:30:02", "payer_location_zip": "411111", "transaction_note": "Monthly Gym Fee"},
    {"receiver_vpa": "medical@ruby", "transaction_amount": 2500.00, "date_time_stamp": "2025-03-25 10:15:02", "payer_location_zip": "411032", "transaction_note": "Medical Test at Ruby Hall"},
    {"receiver_vpa": "electronics@poorvika", "transaction_amount": 10000.00, "date_time_stamp": "2025-03-26 13:45:02", "payer_location_zip": "411045", "transaction_note": "Mobile at Poorvika"},
    {"receiver_vpa": "petrol@reliance", "transaction_amount": 1400.00, "date_time_stamp": "2025-03-27 18:45:02", "payer_location_zip": "411021", "transaction_note": "Petrol at Reliance Pump"},
    {"receiver_vpa": "buspass@msrtc", "transaction_amount": 800.00, "date_time_stamp": "2025-03-28 09:00:02", "payer_location_zip": "411111", "transaction_note": "Monthly Bus Pass"},
    {"receiver_vpa": "canteen@hospital", "transaction_amount": 300.00, "date_time_stamp": "2025-03-29 12:15:02", "payer_location_zip": "411032", "transaction_note": "Snacks at Hospital Canteen"},
    {"receiver_vpa": "clothes@shoppersstop", "transaction_amount": 3500.00, "date_time_stamp": "2025-03-30 16:30:02", "payer_location_zip": "411045", "transaction_note": "Clothes at Shoppers Stop"},
    {"receiver_vpa": "movies@bigcinemas", "transaction_amount": 500.00, "date_time_stamp": "2025-03-31 20:15:02", "payer_location_zip": "411021", "transaction_note": "Movie at Big Cinemas"},
    {"receiver_vpa": "gym@talwalkars", "transaction_amount": 2000.00, "date_time_stamp": "2025-04-01 07:15:02", "payer_location_zip": "411111", "transaction_note": "Monthly Gym Fee"},
    {"receiver_vpa": "medical@sahyadri", "transaction_amount": 3000.00, "date_time_stamp": "2025-04-02 11:00:02", "payer_location_zip": "411032", "transaction_note": "Medical Test at Sahyadri"},
    {"receiver_vpa": "electronics@bajaj", "transaction_amount": 12000.00, "date_time_stamp": "2025-04-03 14:45:02", "payer_location_zip": "411045", "transaction_note": "Washing Machine at Bajaj"},
    {"receiver_vpa": "petrol@essar", "transaction_amount": 1600.00, "date_time_stamp": "2025-04-04 19:30:02", "payer_location_zip": "411021", "transaction_note": "Petrol at Essar Pump"},
    {"receiver_vpa": "buspass@msrtc", "transaction_amount": 900.00, "date_time_stamp": "2025-04-05 08:30:02", "payer_location_zip": "411111", "transaction_note": "Monthly Bus Pass"},
    {"receiver_vpa": "canteen@station", "transaction_amount": 350.00, "date_time_stamp": "2025-04-06 13:00:02", "payer_location_zip": "411032", "transaction_note": "Lunch at Railway Station"},
    {"receiver_vpa": "clothes@brandfactory", "transaction_amount": 4000.00, "date_time_stamp": "2025-04-07 17:15:02", "payer_location_zip": "411045", "transaction_note": "Clothes at Brand Factory"},
    {"receiver_vpa": "movies@miraj", "transaction_amount": 600.00, "date_time_stamp": "2025-04-08 21:00:02", "payer_location_zip": "411021", "transaction_note": "Movie at Miraj Cinemas"},
    {"receiver_vpa": "gym@fitnessfirst", "transaction_amount": 2500.00, "date_time_stamp": "2025-04-09 06:45:02", "payer_location_zip": "411111", "transaction_note": "Monthly Gym Fee"},
    {"receiver_vpa": "medical@kohinoor", "transaction_amount": 3500.00, "date_time_stamp": "2025-04-10 10:30:02", "payer_location_zip": "411032", "transaction_note": "Medical Test at Kohinoor"},
    {"receiver_vpa": "electronics@lot", "transaction_amount": 15000.00, "date_time_stamp": "2025-04-11 15:00:02", "payer_location_zip": "411045", "transaction_note": "Refrigerator at LOT"},
    
    
]

new_transaction = {
    "receiver_vpa": "petrol@essar",
    "transaction_amount": 2000.00,
    "date_time_stamp": "2025-02-23 18:45:00",
    "payer_location_zip": "411333",
    "transaction_note": "Luxury Purchase"
}

# result_json = detect_fraud(transactions, new_transaction)
# print(result_json)
