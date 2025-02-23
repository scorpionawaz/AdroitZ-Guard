from fastapi import FastAPI, Request
from pydantic import BaseModel
from SBIBANKSERVER import account, transaction_history
from ZGuard import average_module , zanalyzer
from datetime import datetime
import json
from fpdf import FPDF
app = FastAPI()
def append_fraud_summary_to_pdf(response_json, filename="fraud_report.pdf"):
    try:
        data = json.loads(response_json)  # Convert JSON string to dictionary
        if data.get("fraud_or_scam_happened") == "true":
            summary = data.get("summary", "No details provided.")
            transaction_name = data.get("name", "Unknown Transaction")
            
            pdf = FPDF()
            try:
                pdf.add_page()
                pdf.set_font("Arial", style='', size=12)
                pdf.cell(200, 10, "Fraud Detection Report by Z+Guard BY Automation", ln=True, align='C')
                pdf.ln(10)  # Line break
                pdf.multi_cell(0, 10, f"Transaction: {transaction_name}\nSummary: {summary}")
                pdf.output(filename, 'F')
                print(f"PDF updated with transaction: {transaction_name}")
            except Exception as e:
                print(f"Error while updating PDF: {e}")
        else:
            print("No fraud detected. PDF not updated.")
    except json.JSONDecodeError:
        print("Invalid JSON response")
class Authentication(BaseModel):
    upiPin: str

class DeviceInfo(BaseModel):
    deviceId: str
    deviceType: str
    mobileCarrier: str

class Geolocation(BaseModel):
    latitude: str
    longitude: str

class Payer(BaseModel):
    vpa: str
    authentication: Authentication
    deviceInfo: DeviceInfo
    geolocation: Geolocation
    ipAddress: str
    zipcode: str

class Payee(BaseModel):
    vpa: str

class LocationDetails(BaseModel):
    city: str
    state: str
    country: str

class Transaction(BaseModel):
    amount: float
    payer: Payer
    payee: Payee
    locationDetails: LocationDetails
    description: str
    callbackUrl: str

@app.post("/transaction")
async def create_transaction(transaction: Transaction, request: Request):
    adb = account.Account()
    tdb = transaction_history.TransactionHistory()

    # Validate payer account existence
    payer_accountno = adb.get_account_number(transaction.payer.vpa)
    if payer_accountno is None:
        print("❌ Invalid Payer VPA detected.")
        return {"error": "❌ Invalid Payer VPA. Transaction cannot be processed."}

    # Validate payee account existence
    payee_accountno = adb.get_account_number(transaction.payee.vpa)
    if payee_accountno is None:
        return {"error": "❌ Invalid Payee VPA. Transaction cannot be processed."}

    # Get Payer Account Balance
    payer_balance = adb.get_account_balance(transaction.payer.vpa)
    print("Payer Amount balance is:", payer_balance)

    # Get Payer Account Status
    payer_status = adb.get_account_status(transaction.payer.vpa)

    # Get Payee Account Status
    payee_status = adb.get_account_status(transaction.payee.vpa)

    # Check if Payer's account is suspended or blocked
    if payer_status in ["Suspended", "Blocked"]:
        return {"error": f"❌ Payer's account is {payer_status}. Cannot proceed further."}

    # Check if Payee's account is suspended or blocked
    print("The Status of Payee is:", payee_status)
    if payee_status in ["Suspended", "Blocked"]:
        return {"error": f"❌ Receiver's account is {payee_status}. Cannot process transaction."}

    # **Handle Insufficient Balance Case**
    if payer_balance < transaction.amount:
        transaction_status = "INSUFFICIENT_BALANCE"

        # Log the failed transaction into transaction history
        tdb.insert_transaction(
            payer_account_no=payer_accountno,
            payer_vpa=transaction.payer.vpa,
            receiver_vpa=transaction.payee.vpa,
            transaction_amount=transaction.amount,
            payer_location_zip=transaction.payer.zipcode,
            payer_city=transaction.locationDetails.city,
            payer_state=transaction.locationDetails.state,
            ip_address=transaction.payer.ipAddress,
            transaction_note=transaction.description,
            device=transaction.payer.deviceInfo.deviceType,
            mode="UPI",
            status=transaction_status
        )
        
        return {"error": "❌ Insufficient balance. Transaction logged with status INSUFFICIENT_BALANCE."}
    

# --------------------------------------------------------------------------------------------------------------------


    # ==/////////////////\\\\\\\\\\\\\\\\\////////////////\\\\\\\\\\\\\\\\\\//////////////////\\\\\\\\\\\\\\\\\\/////////\ 
    
    # detecting if its going beyound Avergae Behaviour 
    # for that we need the last 100 transactions 
    try:
       print("hiiiiiiiiiiiiiiiiiiiiiiiii")
        
       import json
       f100rows = tdb.get_transactions_by_vpa((transaction.payer.vpa))  # ✅ Directly use the list
       exact_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       print("her Transactions "+str(f100rows))
       latestQ = {
       "receiver_vpa":transaction.payee.vpa,
       "transaction_amount":transaction.amount,
       "date_time_stamp": exact_timestamp,
       "payer_location_zip":transaction.payer.zipcode,
       "transaction_note": transaction.description
                }   
       result  =  average_module.is_the_user_normal(f100rows,latestQ)
       print("The type resukt is "+str(type(result)))
       result = json.loads(result)
       print((result))
       
       is_fraudulent = result["is_fraudulent"]  # Correct way to access
       reasons = result["reasons"]
       
       print("Fraud Or not ?"+str(is_fraudulent))
       if is_fraudulent == True:
          with open("patterndatabase.json", "r") as file:
            patterndb = str(json.load(file))
            
          fffresult = (zanalyzer.send_to_z_analyze(patterndb,tdb.get_transactions_by_vpa_combined(transaction.payer.vpa),str(latestQ)))
          print(fffresult)
          append_fraud_summary_to_pdf(fffresult)
          return {"error": "❌ WARNING :: Unusal Behavior Check the Values and AMount Again."+str(reasons) }
         
       
    except:
        print("Error in detecting the behaviour")
    # ==/////////////////\\\\\\\\\\\\\\\\\////////////////\\\\\\\\\\\\\\\\\\//////////////////\\\\\\\\\\\\\\\\\\/////////\ 
    
    # **Process the transaction normally if balance is sufficient**
    new_payer_balance = payer_balance - transaction.amount
    update_payer = adb.update_bank_balance(transaction.payer.vpa, new_payer_balance)
    
    if "✅" not in update_payer:
        return {"error": "❌ Failed to deduct amount from payer's account. Transaction aborted."}

    # Get Payee Account Balance
    payee_balance = adb.get_account_balance(transaction.payee.vpa)

    # Credit amount to Payee's account
    new_payee_balance = payee_balance + transaction.amount
    update_payee = adb.update_bank_balance(transaction.payee.vpa, new_payee_balance)

    if "✅" not in update_payee:
        # Rollback payer's balance if crediting payee fails
        adb.update_bank_balance(transaction.payer.vpa, payer_balance)
        return {"error": "❌ Failed to credit amount to payee's account. Transaction reverted."}

    # **Transaction Successful**
    transaction_status = "SUCCESSFUL"

    # Log the successful transaction into transaction history
    tdb.insert_transaction(
        payer_account_no=payer_accountno,
        payer_vpa=transaction.payer.vpa,
        receiver_vpa=transaction.payee.vpa,
        transaction_amount=transaction.amount,
        payer_location_zip=transaction.payer.zipcode,
        payer_city=transaction.locationDetails.city,
        payer_state=transaction.locationDetails.state,
        ip_address=transaction.payer.ipAddress,
        transaction_note=transaction.description,
        device=transaction.payer.deviceInfo.deviceType,
        mode="UPI",
        status=transaction_status
    )
    
    return {"message": f"Transaction processed successfully with status: {transaction_status}"}


