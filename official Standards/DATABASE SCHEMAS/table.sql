-- the postgresql is used and database name is BANK

--show databases;
--create database BANK; 
use BANK;
CREATE TABLE `ACCOUNT` (
    `ACCOUNT_NO` BIGINT AUTO_INCREMENT PRIMARY KEY,  -- Auto-increment enabled from the start
    `BANK_BALANCE` DECIMAL(20,2) NOT NULL,  -- Precise financial storage
    `BRANCH_NO` BIGINT NOT NULL,
    `ACCOUNT_STATUS` VARCHAR(20) NOT NULL,  -- Using VARCHAR instead of ENUM for flexibility
    `ADDRESS` VARCHAR(500) NOT NULL,  -- Using VARCHAR instead of TEXT for better performance
    `FIRST_NAME` VARCHAR(100) NOT NULL,
    `MIDDLE_NAME` VARCHAR(100),
    `LAST_NAME` VARCHAR(100) NOT NULL,
    `PHONE_NUMBERS` VARCHAR(20) NOT NULL
) AUTO_INCREMENT = 525555;  -- ✅ Set the starting value at the time of table creation

-- this is the script in insert the account    --------------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE Insert_Realistic_Accounts()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE first_names TEXT DEFAULT 'Aarav,Vihaan,Aditya,Rajesh,Amit,Neha,Pooja,Kavita,Sunita,Manish,Rohan,Raj,Divya,Anjali,Sneha,Vikram,Ankit,Varun,Karan,Alok';
    DECLARE last_names TEXT DEFAULT 'Sharma,Verma,Patil,Desai,Reddy,Nair,Gupta,Jain,Mishra,Yadav,Chopra,Kapoor,Mehta,Malhotra,Banerjee,Sengupta,Bhatt,Bhattacharya,Goswami,Joshi';

    WHILE i < 100 DO
        INSERT INTO `ACCOUNT` (`BANK_BALANCE`, `BRANCH_NO`, `ACCOUNT_STATUS`, `ADDRESS`, `FIRST_NAME`, `MIDDLE_NAME`, `LAST_NAME`, `PHONE_NUMBERS`)
        VALUES (
            ROUND(RAND() * 500000, 2),  -- Random bank balance up to ₹5,00,000
            LPAD(FLOOR(RAND() * 50) + 1, 8, '0'),  -- 8-digit padded Branch No (e.g., 00000123)
            CASE FLOOR(RAND() * 3)       -- Random status selection
                WHEN 0 THEN 'ACTIVE'
                WHEN 1 THEN 'BLOCKED'
                ELSE 'SUSPENDED'
            END,
            CONCAT(FLOOR(RAND() * 200), ' ', 
                   CASE FLOOR(RAND() * 5)
                       WHEN 0 THEN 'MG Road'
                       WHEN 1 THEN 'Shivaji Nagar'
                       WHEN 2 THEN 'JP Nagar'
                       WHEN 3 THEN 'Kothrud'
                       ELSE 'Baner'
                   END, ', Pune, Maharashtra'),  -- Random Address in Pune
            SUBSTRING_INDEX(SUBSTRING_INDEX(first_names, ',', FLOOR(RAND() * 20) + 1), ',', -1),  -- Random First Name
            'Kumar',  -- Fixed middle name
            SUBSTRING_INDEX(SUBSTRING_INDEX(last_names, ',', FLOOR(RAND() * 20) + 1), ',', -1),  -- Random Last Name
            CONCAT('+91 94220 ', LPAD(FLOOR(RAND() * 99999), 5, '0'))  -- Phone format: +91 94220 XXXXX
        );
        SET i = i + 1;
    END WHILE;
END $$

DELIMITER ;

-- ✅ Call the procedure to insert 100 genuine-looking records
CALL Insert_Realistic_Accounts();




--------------------------------------------------------------------------------------------------------------------------------------------

-- Transaction_history  
CREATE TABLE Transaction_History (
    transaction_id        VARCHAR(50) PRIMARY KEY,  -- Unique transaction ID
    account_no           BIGINT NOT NULL,          -- Foreign key from Account table
    receiver_vpa         VARCHAR(100) NOT NULL,    -- Receiver account VPA
    transaction_amount   DECIMAL(15,2) NOT NULL,  -- Amount involved in the transaction
    transaction_mode     VARCHAR(50) NOT NULL,    -- Mode (UPI, NEFT, IMPS, etc.)
    transaction_status   ENUM('Successful', 'Insufficient Balance', 'Network Down', 'Blocked Account', 'Suspended', 'Limit Crossed', 'Fraud Detected') NOT NULL,  
    transaction_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Date and time of transaction
    location            VARCHAR(255),             -- Location of transaction
    FOREIGN KEY (account_no) REFERENCES account(account_no) ON DELETE CASCADE
);

DELIMITER $$
CREATE FUNCTION generate_transaction_id() RETURNS VARCHAR(50) DETERMINISTIC
BEGIN
    DECLARE new_id VARCHAR(50);
    SET new_id = CONCAT('TXN', UNIX_TIMESTAMP(), FLOOR(RAND() * 1000));
    RETURN new_id;
END $$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER before_insert_transaction
BEFORE INSERT ON Transaction_History
FOR EACH ROW
BEGIN
    SET NEW.transaction_id = generate_transaction_id();
END $$
DELIMITER ;
