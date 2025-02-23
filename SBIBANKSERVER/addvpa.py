import json
import mysql.connector
from mysql.connector import Error
import random

# Mapping of known branch numbers to VPA extensions
branch_vpa_mapping = {
    218: '@sbi',       
    256: '@okicici',   
    259: '@ybl',       
    136: '@oksbi',     
    741: '@apl',       
    723: '@paytm',     
    186: '@sbi',       
    956: '@okicici',   
    491: '@ybl',       
    659: '@oksbi',     
    486: '@paytm'      
}

# List of valid VPA extensions to cycle through when branch_no is unknown
vpa_extensions = ['@sbi', '@okicici', '@ybl', '@oksbi', '@apl', '@paytm']

def generate_vpa(first_name, last_name, branch_no, existing_vpas):
    """Generate a unique VPA using first name, last name, and branch number."""
    base_vpa = f"{first_name.lower()}{last_name.lower()}"

    # Assign an extension based on branch number or randomly if not found
    extension = branch_vpa_mapping.get(branch_no, random.choice(vpa_extensions))
    
    vpa = base_vpa + extension
    counter = 1

    # Ensure the VPA is unique
    while vpa in existing_vpas:
        vpa = f"{base_vpa}{counter}{extension}"
        counter += 1

    return vpa

def update_vpas(config_file='config.json'):
    """Update the VPA field for each account in the ACCOUNT table."""
    try:
        # Load database configuration from JSON file
        with open(config_file, 'r') as file:
            config = json.load(file)

        # Establish database connection
        connection = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)

            # Retrieve existing VPAs to ensure uniqueness
            cursor.execute("SELECT VPA FROM ACCOUNT WHERE VPA IS NOT NULL")
            existing_vpas = {row['VPA'] for row in cursor.fetchall()}

            # Retrieve account details
            cursor.execute("SELECT ACCOUNT_NO, FIRST_NAME, LAST_NAME, BRANCH_NO FROM ACCOUNT")
            accounts = cursor.fetchall()

            # Update each account with a new unique VPA
            for account in accounts:
                account_no = account['ACCOUNT_NO']
                first_name = account['FIRST_NAME']
                last_name = account['LAST_NAME']
                branch_no = account['BRANCH_NO']

                # Generate unique VPA
                vpa = generate_vpa(first_name, last_name, branch_no, existing_vpas)
                existing_vpas.add(vpa)  # Add to the set of existing VPAs

                # Update the ACCOUNT table with the new VPA
                update_query = "UPDATE ACCOUNT SET VPA = %s WHERE ACCOUNT_NO = %s"
                cursor.execute(update_query, (vpa, account_no))

            # Commit the changes to the database
            connection.commit()
            print("VPAs updated successfully.")

    except Error as e:
        print(f"Error: {e}")
        if connection:
            connection.rollback()  # Rollback in case of error

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed.")

# Run the update function
if __name__ == "__main__":
    update_vpas()
