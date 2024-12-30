import sqlite3
from random import randint
import re

# Database setup
def initialize_database():
    conn = sqlite3.connect('banking_system.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        account_number TEXT UNIQUE NOT NULL,
        dob TEXT NOT NULL,
        city TEXT NOT NULL,
        password TEXT NOT NULL,
        balance REAL NOT NULL CHECK(balance >= 2000),
        contact_number TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        active INTEGER DEFAULT 1
    )''')

    # Create transactions table
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_number TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        amount REAL NOT NULL,
        date_time TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

def generate_account_number():
    return str(randint(1000000000, 9999999999))

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_contact_number(contact):
    return contact.isdigit() and len(contact) == 10

def validate_password(password):
    pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(pattern, password) is not None

def add_user():
    name = input("Enter Name: ")
    dob = input("Enter Date of Birth (YYYY-MM-DD): ")
    city = input("Enter City: ")
    contact = input("Enter Contact Number: ")
    email = input("Enter Email: ")
    address = input("Enter Address: ")

    if not validate_contact_number(contact):
        print("Invalid contact number. Must be 10 digits.")
        return
    if not validate_email(email):
        print("Invalid email format.")
        return

    password = input("Enter Password (min 8 chars, include letters, numbers, special chars): ")
    if not validate_password(password):
        print("Invalid password format.")
        return

    try:
        balance = float(input("Enter Initial Balance (minimum 2000): "))
        if balance < 2000:
            print("Initial balance must be at least 2000.")
            return
    except ValueError:
        print("Invalid balance input.")
        return

    account_number = generate_account_number()

    conn = sqlite3.connect('banking_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''INSERT INTO users (name, account_number, dob, city, password, balance, contact_number, email, address)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (name, account_number, dob, city, password, balance, contact, email, address))
        conn.commit()
        print(f"User added successfully! Account Number: {account_number}")
    except sqlite3.IntegrityError:
        print("Error: Account number already exists. Try again.")
    finally:
        conn.close()

def show_users():
    conn = sqlite3.connect('banking_system.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    if users:
        for user in users:
            print(f"\nID: {user[0]}\nName: {user[1]}\nAccount Number: {user[2]}\nDOB: {user[3]}\nCity: {user[4]}\nBalance: {user[5]}\nContact: {user[6]}\nEmail: {user[7]}\nAddress: {user[8]}\nActive: {'Yes' if user[9] else 'No'}")
    else:
        print("No users found.")

    conn.close()

def login():
    account_number = input("Enter Account Number: ")
    password = input("Enter Password: ")

    conn = sqlite3.connect('banking_system.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE account_number = ? AND password = ?", (account_number, password))
    user = cursor.fetchone()

    if user:
        if user[9] == 0:
            print("Account is deactivated. Contact the bank for assistance.")
            conn.close()
            return

        print(f"Welcome, {user[1]}!\n")

        while True:
            print("1. Show Balance")
            print("2. Show Transactions")
            print("3. Credit Amount")
            print("4. Debit Amount")
            print("5. Transfer Amount")
            print("6. Deactivate Account")
            print("7. Change Password")
            print("8. Update Profile")
            print("9. Logout")

            choice = input("Enter your choice: ")

            if choice == '1':
                print(f"Your current balance is: {user[5]}")

            elif choice == '2':
                cursor.execute("SELECT * FROM transactions WHERE account_number = ?", (account_number,))
                transactions = cursor.fetchall()

                if transactions:
                    for transaction in transactions:
                        print(f"\nTransaction ID: {transaction[0]}\nType: {transaction[2]}\nAmount: {transaction[3]}\nDate: {transaction[4]}")
                else:
                    print("No transactions found.")

            elif choice == '3':  # Credit Amount
                try:
                    amount = float(input("Enter amount to credit: "))
                    if amount <= 0:
                        print("Amount must be greater than 0.")
                        continue

                    new_balance = user[5] + amount
                    cursor.execute("UPDATE users SET balance = ? WHERE account_number = ?", (new_balance, account_number))
                    cursor.execute("INSERT INTO transactions (account_number, transaction_type, amount) VALUES (?, ?, ?)", (account_number, 'Credit', amount))
                    conn.commit()
                    print(f"Amount credited successfully. New Balance: {new_balance}")
                    user = (user[0], user[1], user[2], user[3], user[4], new_balance, user[6], user[7], user[8], user[9])  # Update user tuple locally
                except ValueError:
                    print("Invalid amount.")

            elif choice == '4':  # Debit Amount
                try:
                    amount = float(input("Enter amount to debit: "))
                    if amount <= 0 or amount > user[5]:
                        print("Invalid amount. Ensure it is greater than 0 and less than or equal to your balance.")
                        continue

                    new_balance = user[5] - amount
                    cursor.execute("UPDATE users SET balance = ? WHERE account_number = ?", (new_balance, account_number))
                    cursor.execute("INSERT INTO transactions (account_number, transaction_type, amount) VALUES (?, ?, ?)", (account_number, 'Debit', amount))
                    conn.commit()
                    print(f"Amount debited successfully. New Balance: {new_balance}")
                    user = (user[0], user[1], user[2], user[3], user[4], new_balance, user[6], user[7], user[8], user[9])  # Update user tuple locally
                except ValueError:
                    print("Invalid amount.")


            elif choice == '5':
                target_account = input("Enter target account number: ")
                try:
                    amount = float(input("Enter amount to transfer: "))
                    if amount <= 0 or amount > user[5]:
                        print("Invalid amount. Ensure it is greater than 0 and less than or equal to your balance.")
                        continue

                    cursor.execute("SELECT * FROM users WHERE account_number = ?", (target_account,))
                    target_user = cursor.fetchone()

                    if not target_user:
                        print("Target account does not exist.")
                        continue

                    user[5] -= amount
                    cursor.execute("UPDATE users SET balance = ? WHERE account_number = ?", (user[5], account_number))

                    target_balance = target_user[5] + amount
                    cursor.execute("UPDATE users SET balance = ? WHERE account_number = ?", (target_balance, target_account))

                    cursor.execute("INSERT INTO transactions (account_number, transaction_type, amount) VALUES (?, ?, ?)", (account_number, 'Transfer Out', amount))
                    cursor.execute("INSERT INTO transactions (account_number, transaction_type, amount) VALUES (?, ?, ?)", (target_account, 'Transfer In', amount))

                    conn.commit()
                    print("Amount transferred successfully.")
                except ValueError:
                    print("Invalid amount.")

            elif choice == '6':
                confirm = input("Are you sure you want to deactivate your account? (yes/no): ").lower()
                if confirm == 'yes':
                    cursor.execute("UPDATE users SET active = 0 WHERE account_number = ?", (account_number,))
                    conn.commit()
                    print("Account deactivated. Logging out...")
                    break

            elif choice == '7':
                new_password = input("Enter new password: ")
                if validate_password(new_password):
                    cursor.execute("UPDATE users SET password = ? WHERE account_number = ?", (new_password, account_number))
                    conn.commit()
                    print("Password changed successfully.")
                else:
                    print("Invalid password format.")

            elif choice == '8':
                new_city = input("Enter new city: ")
                new_contact = input("Enter new contact number: ")
                new_email = input("Enter new email: ")
                new_address = input("Enter new address: ")

                if validate_contact_number(new_contact) and validate_email(new_email):
                    cursor.execute("UPDATE users SET city = ?, contact_number = ?, email = ?, address = ? WHERE account_number = ?",
                                   (new_city, new_contact, new_email, new_address, account_number))
                    conn.commit()
                    print("Profile updated successfully.")
                else:
                    print("Invalid contact number or email format.")

            elif choice == '9':
                print("Logging out...")
                break

            else:
                print("Invalid choice. Please try again.")
    else:
        print("Invalid account number or password.")

    conn.close()

def main():
    initialize_database()

    while True:
        print("\nBANKING SYSTEM")
        print("1. Add User")
        print("2. Show Users")
        print("3. Login")
        print("4. Exit")

        choice = input("Enter your choice: ")
        if choice == '1':
            add_user()
        elif choice == '2':
            show_users()
        elif choice == '3':
            login()
        elif choice == '4':
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()