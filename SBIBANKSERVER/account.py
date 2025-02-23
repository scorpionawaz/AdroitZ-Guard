import json
import mysql.connector
from mysql.connector import Error
import qrcode

class Account:
    def __init__(self, config_file='SBIBANKSERVER/config.json'):
        """Initialize the connection using credentials from a JSON file."""
        self.connection = None
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
                print("✅ Database connection established successfully.")
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            self.connection = None
            
    def update_bank_balance(self, vpa, new_balance):
        """Update the bank balance of a specific account using VPA."""
        if self.connection:
            cursor = self.connection.cursor()
            query = """
                UPDATE account 
                SET BANK_BALANCE = %s 
                WHERE VPA = %s
            """
            try:
                cursor.execute(query, (new_balance, vpa))
                self.connection.commit()
                cursor.close()
                return "✅ Bank balance updated successfully."
            except Error as e:
                return f"❌ Error updating bank balance: {e}"
        return "⚠️ Database connection not available."

    def update_account_status(self, vpa, new_status):
        """Update the account status of a specific account using VPA."""
        if self.connection:
            cursor = self.connection.cursor()
            query = """
                UPDATE account 
                SET ACCOUNT_STATUS = %s 
                WHERE VPA = %s
            """
            try:
                cursor.execute(query, (new_status, vpa))
                self.connection.commit()
                cursor.close()
                return "✅ Account status updated successfully."
            except Error as e:
                return f"❌ Error updating account status: {e}"
        return "⚠️ Database connection not available."


    def get_account_details(self, vpa):
        """Retrieve all details of a specific account using VPA."""
        if self.connection:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM account WHERE VPA = %s"
            cursor.execute(query, (vpa,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                details = "\n".join([f"{key}: {value}" for key, value in result.items()])
                return f"📜 Account Details:\n{details}"
            return "⚠️ Account not found."
        return "⚠️ Database connection not available."

    def get_account_balance(self, vpa):
       """Retrieve only the balance of a specific account using VPA."""
       if self.connection:
           cursor = self.connection.cursor()
           query = "SELECT BANK_BALANCE FROM account WHERE VPA = %s"
           cursor.execute(query, (vpa,))
           result = cursor.fetchone()
           cursor.close()
           
           if result:  # Ensure result is not None before accessing
               return float(result[0])
           else:
               return   # Default balance to "0" if account not found
       return "⚠️ Database connection not available."

    def get_account_status(self, vpa):
        """Retrieve the status of a specific account using VPA."""
        if self.connection:
            cursor = self.connection.cursor()
            query = "SELECT ACCOUNT_STATUS FROM account WHERE VPA = %s"
            cursor.execute(query, (vpa,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return result[0]  # Return only the status value
            return   # Return "NOT_FOUND" if no record exists
        return "⚠️ Database connection not available."

    def get_account_number(self, vpa):
        """Retrieve the Account Number of a specific account using VPA."""
        if self.connection:
            cursor = self.connection.cursor()
            query = "SELECT ACCOUNT_NO FROM account WHERE VPA = %s"
            cursor.execute(query, (vpa,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:  # Ensure result is not None
                return str(result[0])
            else:
                return None  # Return None explicitly if account not found
        return None  # Return None if the database connection fails

    
    def generate_qr_code(self, vpa):
        """Generate a QR code for the given VPA."""
        if self.connection:
            cursor = self.connection.cursor()
            query = "SELECT FIRST_NAME, LAST_NAME FROM account WHERE VPA = %s"
            cursor.execute(query, (vpa,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                name = f"{result[0]} {result[1]}"
                upi_link = f"upi://pay?pa={vpa}&pn={name.replace(' ', '%20')}&aid="
                qr = qrcode.make(upi_link)
                qr.save(f"{vpa}_QR.png")
                print(f"✅ QR Code generated and saved as {vpa}_QR.png")
                return upi_link
            return "⚠️ Account not found."
        return "⚠️ Database connection not available."

    def close_connection(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Database connection closed.")
            
db  = Account()
db.generate_qr_code("sandeepmore3@apl")