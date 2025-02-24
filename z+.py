from fastapi import FastAPI, Request
from pydantic import BaseModel
from SBIBANKSERVER import account, transaction_history
from ZGuard import average_module , zanalyzer
from datetime import datetime
import json
from fpdf import FPDF
app = FastAPI()

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
from fpdf import FPDF
import json
from datetime import datetime

def sanitize_text(text):
    """ Remove non-ASCII characters to avoid encoding issues in PDF """
    return ''.join(char for char in text if ord(char) < 128)

from fpdf import FPDF
import json
from datetime import datetime

def sanitize_text(text):
    """Convert text to a latin-1 safe format by removing unsupported characters."""
    if text is None:
        return "N/A"
    text = str(text).replace("₹", "INR")  # Replace Rupee symbol
    return text.encode("latin-1", "ignore").decode("latin-1")  # Remove unsupported characters

def append_fraud_summary_to_pdf(response_json, transaction, filename="fraud_report.pdf"):
    try:
        data = json.loads(response_json)  
        
        if data.get("fraud_or_scam_happened") == "true":
            global summary
            summary = sanitize_text(data.get("summary", "No details provided."))
            transaction_name = sanitize_text(data.get("name", "Unknown Transaction"))

            # Fetch payer and payee details
            adb = account.Account()
            payer_details = sanitize_text(adb.get_account_details(transaction.payer.vpa))
            payee_details = sanitize_text(adb.get_account_details(transaction.payee.vpa))

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Header
            pdf.cell(200, 10, "Fraud Detection Report", ln=True, align='C')
            pdf.ln(10)

            # Fraud Summary
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(200, 10, "Fraud Summary", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, f"Transaction: {transaction_name}\nSummary: {summary}")
            pdf.ln(5)

            # Payer Details
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(200, 10, "Payer Details", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, payer_details)
            pdf.ln(5)

            # Payee Details
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(200, 10, "Payee Details", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, payee_details)
            pdf.ln(5)

            # Transaction Details
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(200, 10, "Transaction Details", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                  f"Amount: INR {sanitize_text(transaction.amount)}\n"
                                  f"Note: {sanitize_text(transaction.description)}\n"
                                  f"Location: {sanitize_text(transaction.locationDetails.city)}, {sanitize_text(transaction.locationDetails.state)}, {sanitize_text(transaction.locationDetails.country)}\n"
                                  f"Zipcode: {sanitize_text(transaction.payer.zipcode)}\n"
                                  f"Device Type: {sanitize_text(transaction.payer.deviceInfo.deviceType)}\n"
                                  f"Mobile Carrier: {sanitize_text(transaction.payer.deviceInfo.mobileCarrier)}\n"
                                  f"Latitude: {sanitize_text(transaction.payer.geolocation.latitude)}, Longitude: {sanitize_text(transaction.payer.geolocation.longitude)}\n"
                                  f"IP Address: {sanitize_text(transaction.payer.ipAddress)}")

            # Save PDF
            pdf.output(filename, 'F')
            print(f"✅ PDF updated: {transaction_name}")
        else:
            print("ℹ️ No fraud detected. PDF not updated.")

    except json.JSONDecodeError:
        print("⚠️ Invalid JSON response")
    except Exception as e:
        print(f"❌ Error while updating PDF: {e}")




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
          
        #   now here is the one of the important and last Step  to analayze the pattterns at Human level
          fffresult = (zanalyzer.send_to_z_analyze(patterndb,tdb.get_transactions_by_vpa_combined(transaction.payer.vpa),str(latestQ)))
          print(fffresult)
          append_fraud_summary_to_pdf(fffresult,transaction)
        #   blocking Fruadlant account 
        # and suspending the User 
        
          adb.update_account_status(transaction.payer.vpa,"Suspended")
          adb.update_account_status(transaction.payee.vpa,"Blocked")
          
        #   updating the logs 
        # ENUM(
        #                     'SUCCESSFUL', 
        #                     'INSUFFICIENT_BALANCE', 
        #                     'NETWORK_DOWN', 
        #                     'BLOCKED_ACCOUNT', 
        #                     'SUSPENDED', 
        #                     'LIMIT_CROSSED', 
        #                     'FRAUD_DETECTED_STOPPED'
        #                   ) 
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
            status="FRAUD_DETECTED_STOPPED"
          )
          return {"error": "❌ This is a Scam or Fraud:."+str(summary)+ "Your Account Has Been Suspended For Security Reasons" }
         
       
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


