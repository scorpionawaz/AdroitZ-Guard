import json
import mysql.connector
from mysql.connector import Error

class TransactionHistory:
    def __init__(self, config_file='SBIBANKSERVER/config.json'):
        """Initialize the connection once using credentials from a JSON file."""
        self.connection = None
        self.cursor = None
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)
            self.connection = mysql.connector.connect(
                host=config['host'],
                user=config['user'],
                password=config['password'],
                database='BANK'
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                print("Database connection established successfully.")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None

    def is_valid_account(self, account_no, vpa):
     """Check if the given account number and VPA exist in the database."""
     if self.connection:
         try:
             if account_no is not None:
                 # Ensure case-insensitive and trimmed VPA comparison
                 query = "SELECT COUNT(*) FROM account WHERE account_no = %s AND TRIM(LOWER(vpa)) = TRIM(LOWER(%s))"
                 print(f"Executing query: {query} with values ({account_no}, {vpa.strip().lower()})")  # Debugging print
                 self.cursor.execute(query, (account_no, vpa.strip().lower()))
             else:
                 # Only check if receiver's VPA exists
                 query = "SELECT COUNT(*) FROM account WHERE TRIM(LOWER(vpa)) = TRIM(LOWER(%s))"
                 print(f"Executing query: {query} with values ({vpa.strip().lower()})")  # Debugging print
                 self.cursor.execute(query, (vpa.strip().lower(),))
 
             result = self.cursor.fetchone()[0]
             print(f"Query result: {result}")  # Debugging print
             return result > 0
         except Error as e:
             print(f"Error validating account: {e}")
     return False




    def insert_transaction(self, payer_account_no, payer_vpa, receiver_vpa, transaction_amount, 
                        payer_location_zip, payer_city, payer_state, ip_address, transaction_note, device, mode, status):
     """Insert a new transaction into the Transaction_History table if accounts are valid."""
     if not self.connection:
         print("Database connection not available.")
         return
     
     # Validate payer: Must match both account number and VPA
     if not self.is_valid_account(payer_account_no, payer_vpa):
         print("Error: Payer account number and VPA do not match.")
         return
     
     # Validate receiver: Only the VPA needs to exist
     if not self.is_valid_account(None, receiver_vpa):
         print("Error: Receiver VPA not found.")
         return
     
     try:
         query = """
         INSERT INTO Transaction_History 
         (payer_account_no, payer_vpa, receiver_vpa, transaction_amount, payer_location_zip, payer_city, 
          payer_state, ip_address, transaction_note, device, mode, status) 
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
         """
         self.cursor.execute(query, (payer_account_no, payer_vpa, receiver_vpa, transaction_amount, 
                                     payer_location_zip, payer_city, payer_state, ip_address, 
                                     transaction_note, device, mode, status))
         self.connection.commit()
         print("Transaction inserted successfully.")
     
     except Error as e:
         print(f"Error inserting transaction: {e}")
 
 
    def get_transactions(self, payer_account_no):
        """Retrieve all transactions for a specific payer account."""
        if self.connection:
            try:
                self.cursor.execute("SELECT * FROM Transaction_History WHERE payer_account_no = %s", (payer_account_no,))
                transactions = self.cursor.fetchall()
                return transactions if transactions else "No transactions found."
            except Error as e:
                print(f"Error retrieving transactions: {e}")
                return "Error fetching data."
        return "Database connection not available."

    #   get latest trasanctions 
    def get_latest_transactions(self, limit=100):
        """Retrieve the latest 100 transactions and format them into a structured dataset."""
        if not self.connection:
            print("Database connection not available.")
            return []

        try:
            query = """
            SELECT receiver_vpa, transaction_amount, date_time_stamp, payer_location_zip, transaction_note
            FROM Transaction_History
            ORDER BY date_time_stamp DESC
            LIMIT %s
            """
            self.cursor.execute(query, (limit,))
            transactions = self.cursor.fetchall()

            # Format transactions into the required JSON structure
            formatted_transactions = [
                {
                    "receiver_vpa": tx["receiver_vpa"],
                    "transaction_amount": float(tx["transaction_amount"]),
                    "date_time_stamp": tx["date_time_stamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "payer_location_zip": tx["payer_location_zip"],
                    "transaction_note": tx["transaction_note"]
                }
                for tx in transactions
            ]
            return formatted_transactions

        except Error as e:
            print(f"Error retrieving transactions: {e}")
            return []

# function to extract the transaction 
    import json
    #  currently i dont have time so assueme i am using this in redis 
    def get_transactions_by_vpa(self, vpa, limit=100):
     """Retrieve transactions for a specific VPA and return structured JSON."""
     if not self.connection:
         print("Database connection not available.")
         return json.dumps([])  # Return empty JSON array if no DB connection
 
     try:
         query = """
         SELECT receiver_vpa, transaction_amount, date_time_stamp, payer_location_zip, transaction_note
         FROM Transaction_History
         WHERE payer_vpa = %s
         ORDER BY date_time_stamp DESC
         LIMIT %s
         """
 
         with self.connection.cursor(dictionary=True) as cursor:
             cursor.execute(query, (vpa, limit))
             transactions = cursor.fetchall()
 
         # ✅ Formatting Transactions as JSON Array
         formatted_transactions = [
             {
                 "receiver_vpa": tx["receiver_vpa"],
                 "transaction_amount": float(tx["transaction_amount"]),
                 "date_time_stamp": tx["date_time_stamp"].strftime("%Y-%m-%d %H:%M:%S"),
                 "payer_location_zip": tx["payer_location_zip"],
                 "transaction_note": tx["transaction_note"]
             }
             for tx in transactions
         ]
 
         return formatted_transactions  # Return a list instead of a JSON string

 
     except Error as e:
         print(f"Error retrieving transactions: {e}")
         return json.dumps([])  # Return empty JSON on error


    def get_transactions_by_vpa_combined(self, vpa, limit=10):
        """Retrieve both sent and received transactions for a given VPA."""
        if not self.connection:
            print("Database connection not available.")
            return json.dumps([])  # Return empty JSON array if no DB connection

        try:
            query = """
            (SELECT 'sent' AS transaction_type, receiver_vpa, transaction_amount, date_time_stamp, payer_location_zip, transaction_note
             FROM Transaction_History 
             WHERE payer_vpa = %s AND status = 'SUCCESSFUL')
            UNION ALL
            (SELECT 'received' AS transaction_type, payer_vpa AS receiver_vpa, transaction_amount, date_time_stamp, payer_location_zip, transaction_note
             FROM Transaction_History 
             WHERE receiver_vpa = %s AND status = 'SUCCESSFUL')
            ORDER BY date_time_stamp DESC
            LIMIT %s
        """

            
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (vpa, vpa, limit))
                transactions = cursor.fetchall()

            # ✅ Formatting Transactions as JSON Array
            formatted_transactions = [
                {
                    "transaction_type": tx["transaction_type"],
                    "counterparty_vpa": tx["receiver_vpa"],
                    "transaction_amount": float(tx["transaction_amount"]),
                    "date_time_stamp": tx["date_time_stamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "payer_location_zip": tx["payer_location_zip"],
                    "transaction_note": tx["transaction_note"]
                }
                for tx in transactions
            ]
            
            return json.dumps(formatted_transactions, indent=4)  # Return a list instead of a JSON string

        except Error as e:
            print(f"Error retrieving transactions: {e}")
            return json.dumps([])  # Return empty JSON on error    
        
    def close_connection(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Database connection closed.")

