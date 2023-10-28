import mysql.connector
import hashlib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from decimal import Decimal
import csv
from multiprocessing import Pool


INITIAL_ADMIN_USERNAME = "admin"
INITIAL_ADMIN_PASSWORD = "admin"

db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="finance_pool",
    pool_size=5,
    host="localhost",
    user="root",
    password="root",
    database="finance"
)

def get_db_connection():
    return db_pool.get_connection()

def login(username, password):
    query = "SELECT id, password_hash, is_admin, approved FROM users WHERE username = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if result:
            user_id, password_hash, is_admin, approved = result
            if password_hash == hashlib.sha256(password.encode()).hexdigest():
                if is_admin:
                    print("Admin login successful.")
                    if approved:
                        admin_menu(user_id)
                    else:
                        print("Admin approval required. Please try again later.")
                else:
                    if approved:
                        print("User login successful.")
                        main(user_id)
                    else:
                        print("Admin approval required. Please try again later.")
            else:
                print("Invalid credentials.")
        else:
            print("User not found.")

def main(user_id):
    performed_predictive_analysis = False
    while True:
        print("1. Enter Information:")
        print("2. View Information:")
        print("3. Predictive Analysis:")
        print("4. Update Data:")
        print("5. Delete Data:")
        print("6. Set Monthly Budget:")
        print("7. Check Alerts:")
        print("8. Investment Tracking:")
        print("9. Analyze Financial Data:")  
        print("10. Export Financial Data to CSV:")  
        print("11. Import Financial Data from CSV:")  
        print("12. Generate Reports:") 
        print("13. Logout")

        choice = input("Enter your choice: ")

        if choice == '1':
            input_data(user_id)
        elif choice == '2':
            view_financial_data(user_id)
            print("Do you want to view the visualize data of this (y/n):")
            choice1 = input("Enter your choice: ")
            if choice1 == 'y':
                visualize_financial_data(user_id)
        elif choice == '3':
            if not performed_predictive_analysis:
                performed_predictive_analysis = True
                model = train_predictive_model(user_id)
                if model:
                    future_expense = float(input("Enter a future expense: "))
                    future_investment = float(input("Enter a future investment: "))
                    predicted_income = predict_future_income(model, future_expense, future_investment)
                    print(f"Predicted future income: {predicted_income}")
                else:
                    print("Insufficient data to train the predictive model.")
            else:
                print("Predictive analysis already performed.")
        elif choice == '4':
            update_data(user_id)
        elif choice == '5':
            delete_data(user_id)
        elif choice == '6':
            set_budget(user_id)
        elif choice == '7':
            check_alerts(user_id)
        elif choice == '8':
            track_investments(user_id)
        elif choice == '9':
            analyze_financial_data(user_id)
        elif choice == '10':
            export_financial_data_csv(user_id)
        elif choice == '11':
            import_financial_data_csv(user_id)
        elif choice == '12':
            generate_reports(user_id)
        elif choice == '13':
            print("Exiting.")
            auth()
        else:
            print("Invalid choice. Please choose again.")

def auth():
    while True:
        print("1. Register")
        print("2. Login")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            register(username, password)
        elif choice == '2':
            username = input("Enter username: ")
            password = input("Enter password: ")
            user_id = login(username, password)
            if user_id:
                if user_id == "admin":
                    admin_menu(user_id)
                else:
                    main(user_id)
        else:
            print("Invalid choice. Please choose again.")

def assign_initial_admin():
    query = "SELECT id FROM users WHERE username = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (INITIAL_ADMIN_USERNAME,))
        result = cursor.fetchone()
        if not result:

            register(INITIAL_ADMIN_USERNAME, INITIAL_ADMIN_PASSWORD, is_admin=True)
        else:
            print("Initial admin user already exists.")

def change_admin_password(admin_id):
    new_password = input("Enter the new admin password: ")
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
    
    update_query = "UPDATE users SET password_hash = %s WHERE id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(update_query, (hashed_password, admin_id))
        conn.commit()
        print("Admin password updated successfully.")

def generate_new_admin():
    username = input("Enter the new admin username: ")
    password = input("Enter the new admin password: ")
    register(username, password, is_admin=True, approved=True)  
    print("New admin user created.")

def admin_menu(admin_id):
    global current_admin_id
    current_admin_id = admin_id

    while True:
        print("Admin Menu:")
        print("1. Change Admin Password")
        print("2. Generate New Admin User")
        print("3. User Approvals")
        print("4. View All User Records")
        print("5. Delete User")
        print("6. Logout")

        choice = input("Enter your choice: ")

        if choice == '1':
            change_admin_password(admin_id)
        elif choice == '2':
            generate_new_admin()
        elif choice == '3':
            view_user_approvals(admin_id)
        elif choice == '4':
            view_all_records(admin_id)
        elif choice == '5':
            if current_admin_id:
                view_and_delete_users(current_admin_id) 
            else:
                print("No admin user is logged in. Please log in as an admin.")
        elif choice == '6':
            print("Logging out as admin.")
            current_admin_id = None 
            auth()
            break
        else:
            print("Invalid choice. Please choose again.")

def view_and_delete_users(admin_id):
    query = "SELECT id, username FROM users WHERE is_admin = 0"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        all_users = cursor.fetchall()

    if all_users:
        print("All User Records:")
        for user in all_users:
            user_id, username = user
            print(f"User ID: {user_id}, Username: {username}")

        while True:
            user_id_to_delete = input("Enter the User ID you want to delete (0 to cancel): ")
            if user_id_to_delete == '0':
                print("User deletion canceled.")
                break
            user_id_to_delete = int(user_id_to_delete)

            if user_id_to_delete in [user[0] for user in all_users]:
                delete_user(admin_id, user_id_to_delete)
                print(f"User with ID {user_id_to_delete} has been deleted.")
            else:
                print("Invalid User ID. Please enter a valid User ID.")
    else:
        print("No regular user records available.")


def get_admin_password(admin_id):
    query = "SELECT password_hash FROM users WHERE id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (admin_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

def view_user_approvals():
    query = "SELECT id, username FROM users WHERE approved = 0"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        user_approvals = cursor.fetchall()

    if user_approvals:
        print("User Approvals:")
        for user in user_approvals:
            user_id, username = user
            print(f"User ID: {user_id}, Username: {username}")
        
        admin_approve_id = int(input("Enter the User ID you want to approve (0 to cancel): "))
        
        if admin_approve_id == 0:
            print("User approvals canceled.")
            admin_menu()
        else:
            approve_user(admin_approve_id)
    else:
        print("No user approval requests available.")

def approve_user(user_id):
    update_query = "UPDATE users SET approved = 1 WHERE id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(update_query, (user_id,))
        conn.commit()
    print(f"User with ID {user_id} has been approved.")

def delete_user(admin_id, user_id_to_delete):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        delete_query = "DELETE FROM users WHERE id = %s"
        cursor.execute(delete_query, (user_id_to_delete,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"User with ID {user_id_to_delete} has been deleted.")
        else:
            print(f"User with ID {user_id_to_delete} not found.")
        admin_menu(admin_id)
    
def is_admin_user(user_id):
    query = "SELECT is_admin FROM users WHERE id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        if result:
            return result[0] == 1  # 1 represents an admin user
        else:
            return False

def view_all_records(admin_id):
    query = "SELECT id, username, is_admin FROM users WHERE is_admin = 0"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        all_users = cursor.fetchall()

    if all_users:
        print("All User Records:")
        for user in all_users:
            user_id, username, is_admin = user
            print(f"User ID: {user_id}, Username: {username}")

        user_id = input("Enter the User ID of the user whose data you want to access: ")
        user_id = int(user_id)  # Convert to integer

        # Check if the selected user is not an admin
        if user_id in [user[0] for user in all_users]:
            user_data = get_user_data(user_id)
            
            if user_data:
                print("\nUser Financial Data:")
                for data in user_data:
                    year, month, income, expense, investment = data
                    print(f"Year: {year}, Month: {month}, Income: {income}, Expense: {expense}, Investment: {investment}")
            else:
                print("No financial data available for this user.")
        else:
            print("Invalid User ID. The selected user is not a regular user.")
    else:
        print("No regular user records available.")


    if all_users:
        print("All Records:")
        for user in all_users:
            user_id, username, is_admin = user
            admin_status = "Yes" if is_admin else "No"
            print(f"User ID: {user_id}, Username: {username}, Admin: {admin_status}")

        user_id = input("Enter the User ID of the user whose data you want to access: ")
        user_id = int(user_id)  # Convert to integer
        user_data = get_user_data(user_id)

        if user_data:
            print("\nUser Financial Data:")
            for data in user_data:
                year, month, income, expense, investment = data
                print(f"Year: {year}, Month: {month}, Income: {income}, Expense: {expense}, Investment: {investment}")
        else:
            print("No financial data available for this user.")
    else:
        print("No records available.")

def get_user_data(user_id):
    query = "SELECT year, month, income, expense, monthly_investment FROM financial_data WHERE user_id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        financial_data = cursor.fetchall()
    return financial_data

def register(username, password, is_admin=False, approved=False):
    query = "SELECT * FROM users WHERE username = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (username,))
        if cursor.fetchone():
            print("Username already exists.")
        else:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            insert_query = "INSERT INTO users (username, password_hash, is_admin, approved) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (username, hashed_password, is_admin, approved))
            conn.commit()
            if is_admin:
                print("Admin registration successful.")
            else:
                print("User registration successful.")
                if not approved:
                    print("Admin approval required. Please try again later.")

def admin_approve_users():
    admin_password = input("Enter the admin password to approve users: ")

    if admin_password == "root":
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT id, username FROM users WHERE approved = 0"
            cursor.execute(query)
            users_to_approve = cursor.fetchall()

            if users_to_approve:
                print("Users pending approval:")
                for user in users_to_approve:
                    user_id, username = user
                    print(f"User ID: {user_id}, Username: {username}")

                user_id_to_approve = input("Enter the User ID to approve (or 'q' to quit): ")
                if user_id_to_approve == 'q':
                    return

                user_id_to_approve = int(user_id_to_approve)
                if user_id_to_approve in [user[0] for user in users_to_approve]:
                    update_query = "UPDATE users SET approved = 1 WHERE id = %s"
                    cursor.execute(update_query, (user_id_to_approve,))
                    conn.commit()
                    print(f"User with ID {user_id_to_approve} has been approved.")
                else:
                    print("Invalid User ID.")
            else:
                print("No users pending approval.")
    else:
        print("Invalid admin password. Approval process canceled.")

def input_data(user_id):
    while True:
        year = int(input("Enter the year: "))
        query = "SELECT MAX(month) FROM financial_data WHERE user_id = %s AND year = %s"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, year))
            latest_month = cursor.fetchone()[0]

        if latest_month is None:
            latest_month = 0

        data_list = []
        for month in range(latest_month + 1, 13):
            print(f"Enter financial data for Month {month}")
            try:
                income = float(input("Enter your Income: "))
                expense = float(input("Enter your expense: "))
                investment = float(input("Enter your Investments: "))
            except ValueError:
                print("Invalid input. Please enter a valid numeric value.")
                continue

            data = (user_id, year, month, income, expense, investment)
            data_list.append(data)

            more_data = input("Do you want to enter data for another month (y/n): ")
            if more_data.lower() != 'y':
                break

        batch_insert_financial_data(user_id, data_list)
        print("Financial data for year", year, "added successfully.")

        more_years = input("Do you want to enter data for another year (y/n): ")
        if more_years.lower() != 'y':
            break

def update_data(user_id):
    year = int(input("Enter the year for which you want to update data: "))
    month = int(input("Enter the month for which you want to update data: "))
    
    update_query = "UPDATE financial_data SET income = %s, expense = %s, monthly_investment = %s WHERE user_id = %s AND year = %s AND month = %s"
    
    try:
        new_income = float(input("Enter the new Income: "))
        new_expense = float(input("Enter the new Expense: "))
        new_investment = float(input("Enter the new Investment: "))
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(update_query, (new_income, new_expense, new_investment, user_id, year, month))
            conn.commit()
        print(f"Financial data for Month {month}, Year {year} updated successfully.")
    except ValueError:
        print("Invalid input. Please enter valid numeric values.")

def delete_data(user_id):
    year = int(input("Enter the year for which you want to delete data: "))
    month = int(input("Enter the month for which you want to delete data: "))
    
    delete_query = "DELETE FROM financial_data WHERE user_id = %s AND year = %s AND month = %s"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(delete_query, (user_id, year, month))
        conn.commit()
    print(f"Financial data for Month {month}, Year {year} deleted successfully.")

def view_user_approvals(admin_id):
    query = "SELECT id, username FROM users WHERE approved = 0"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        user_approvals = cursor.fetchall()

    if user_approvals:
        print("User Approvals:")
        for user in user_approvals:
            user_id, username = user
            print(f"User ID: {user_id}, Username: {username}")
        
        admin_approve_id = int(input("Enter the User ID you want to approve (0 to cancel): "))
        
        if admin_approve_id == 0:
            print("User approvals canceled.")
            admin_menu(admin_id) 
        else:
            approve_user(admin_approve_id)
    else:
        print("No user approval requests available.")
def view_financial_data(user_id):
    query = "SELECT income, expense, monthly_investment FROM financial_data WHERE user_id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        financial_data = cursor.fetchall()

    if financial_data:
        print("Financial Data:")
        for data in financial_data:
            income, expense, investment = data
            print(f"Income: {income}, Expense: {expense}, Investment: {investment}")
    else:
        print("No financial data available.")


def visualize_financial_data(user_id):
    query = "SELECT year, month, income, expense, monthly_investment FROM financial_data WHERE user_id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        financial_data = cursor.fetchall()

    if financial_data:
        years = [data[0] for data in financial_data]
        months = [data[1] for data in financial_data]
        incomes = [data[2] for data in financial_data]
        expenses = [data[3] for data in financial_data]
        monthly_investment = [data[4] for data in financial_data]

        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        plt.figure(figsize=(10, 6))
        x_ticks = [f"{month_names[month - 1]} {year}" for year, month in zip(years, months)]
        
        plt.bar(range(len(incomes)), incomes, color='green', label='Income')
        plt.bar(range(len(expenses)), expenses, color='red', label='Expense')
        plt.bar(range(len(monthly_investment)), monthly_investment, color='blue', label='Investment')
        
        plt.xlabel('Month-Year')
        plt.ylabel('Amount')
        plt.title('Financial Data Visualization')
        plt.xticks(range(len(incomes)), x_ticks, rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()
    else:
        print("No financial data available.")


def train_predictive_model(user_id):
    query = "SELECT expense, monthly_investment, income FROM financial_data WHERE user_id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        financial_data = cursor.fetchall()

    print("Number of historical data points:", len(financial_data))
    if len(financial_data) < 2:
        print("Insufficient data to train the model.")
        return

    expenses = [data[0] for data in financial_data]
    monthly_investment = [data[1] for data in financial_data]
    incomes = [data[2] for data in financial_data]

    X = np.array(list(zip(expenses, monthly_investment)))
    y = np.array(incomes)

    model = LinearRegression()
    model.fit(X, y)

    return model

def predict_future_income(model, future_expense, future_investment):
    predicted_income = model.predict(np.array([[future_expense, future_investment]]))
    return predicted_income[0]

def set_budget(user_id):
    monthly_budget = float(input("Enter your monthly budget: "))
    update_query = "UPDATE users SET monthly_budget = %s WHERE id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(update_query, (monthly_budget, user_id))
        conn.commit()
    print("Monthly budget updated successfully.")

def get_monthly_budget(user_id):
    query = "SELECT monthly_budget FROM users WHERE id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return 0.0 

def check_alerts(user_id):
    query = """
    SELECT expense, IFNULL(SUM(amount), 0) AS total_investment
    FROM financial_data
    JOIN investments ON financial_data.user_id = investments.user_id
    WHERE financial_data.user_id = %s
    GROUP BY financial_data.id
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        financial_data = cursor.fetchall()

    if financial_data:
        for data in financial_data:
            expense, total_investment = data
            total_expenses = Decimal(str(expense)) + total_investment
            monthly_budget_value = get_monthly_budget(user_id)

            if total_expenses > monthly_budget_value:
                print("Alert: Your expenses have exceeded your monthly budget!")
            else:
                print("Alert: Your expenses are within your monthly budget!")
    else:
        print("No financial data available.")

def track_investments(user_id):
    while True:
        print("Investment Tracking:")
        print("1. Add Investment")
        print("2. View Investments")
        print("3. Return To Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            add_investment(user_id)
            track_investments(user_id)
        elif choice == '2':
            view_investments(user_id)
            track_investments(user_id)
        elif choice == '3':
            main(user_id)
        else:
            print("Invalid choice.")
            track_investments(user_id)

def add_investment(user_id):
    investment_name = input("Enter investment name: ")
    investment_amount = float(input("Enter investment amount: "))
    investment_date = input("Enter investment date (YYYY-MM-DD): ")
    investment_description = input("Enter investment description: ")

    insert_query = "INSERT INTO investments (user_id, name, amount, investment_date, description) VALUES (%s, %s, %s, %s, %s)"
    data = (user_id, investment_name, investment_amount, investment_date, investment_description)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(insert_query, data)
        conn.commit()
    print("Investment added successfully.")

def view_investments(user_id):
    query = "SELECT name, amount FROM investments WHERE user_id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        investments = cursor.fetchall()

    if investments:
        print("Investment Tracking:")
        for investment in investments:
            investment_name, investment_amount = investment
            print(f"Investment: {investment_name}, Amount: {investment_amount}")
    else:
        print("No investments tracked.")

def analyze_financial_data(user_id):
    print("Performing advanced financial data analysis...")

    query = "SELECT AVG(income), AVG(expense) FROM financial_data WHERE user_id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

    if result:
        avg_income, avg_expense = result
        print(f"Average Monthly Income: {avg_income}")
        print(f"Average Monthly Expense: {avg_expense}")
    else:
        print("No financial data available for analysis.")

def export_financial_data_csv(user_id):
    print("Exporting financial data to CSV...")

    csv_file_name = input("Enter CSV file name: ")
    
    if not csv_file_name.endswith(".csv"):
        csv_file_name += ".csv"

    try:
        query = "SELECT year, month, income, expense, monthly_investment FROM financial_data WHERE user_id = %s"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            financial_data = cursor.fetchall()

        if financial_data:
            csv_header = ["Year", "Month", "Income", "Expense", "Monthly Investment"]

            with open(csv_file_name, mode='w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(csv_header)

                for data in financial_data:
                    year, month, income, expense, investment = data
                    writer.writerow([year, month, income, expense, investment])

            print(f"Financial data exported to '{csv_file_name}' successfully.")
        else:
            print("No financial data available for export.")
    except Exception as e:
        print(f"Error during export: {str(e)}")

def import_financial_data_csv(user_id):
    print("Importing financial data from CSV...")

    csv_file_name = input("Enter CSV file name: ")
    
    if not csv_file_name.endswith(".csv"):
        csv_file_name += ".csv"

    try:
        with open(csv_file_name, mode='r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader) 

            data_list = []
            for row in reader:
                year, month, income, expense, investment = row
                year = int(year)
                month = int(month)
                income = float(income)
                expense = float(expense)
                investment = float(investment)
                data = (user_id, year, month, income, expense, investment)
                data_list.append(data)

            upsert_financial_data(user_id, data_list)

        print(f"Financial data imported from '{csv_file_name}' successfully.")
    except Exception as e:
        print(f"Error during import: {str(e)}")

def upsert_financial_data(user_id, data_list):
    insert_query = """
    INSERT INTO financial_data (user_id, year, month, income, expense, monthly_investment)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    income = VALUES(income),
    expense = VALUES(expense),
    monthly_investment = VALUES(monthly_investment)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(insert_query, data_list)
        conn.commit()

def batch_insert_financial_data(user_id, data_list):
    insert_query = "INSERT INTO financial_data (user_id, year, month, income, expense, monthly_investment) VALUES (%s, %s, %s, %s, %s, %s)"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(insert_query, data_list)
        conn.commit()

def generate_reports(user_id):
    print("Generating financial reports...")

    try:
        query = "SELECT year, month, SUM(income) AS total_income, SUM(expense) AS total_expense, SUM(monthly_investment) AS total_investment FROM financial_data WHERE user_id = %s GROUP BY year, month"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            monthly_summary_data = cursor.fetchall()

        if monthly_summary_data:
            print("Monthly Summary Report:")
            print("{:<6} | {:<7} | {:<14} | {:<14} | {:<16}".format("Year", "Month", "Total Income", "Total Expense", "Total Investment"))
            for data in monthly_summary_data:
                year, month, total_income, total_expense, total_investment = data
                print("{:<6} | {:<7} | {:<14.2f} | {:<14.2f} | {:<16.2f}".format(year, month, total_income, total_expense, total_investment))
        else:
            print("No financial data available for the report.")
        print("Reports generated successfully.")
    except Exception as e:
        print(f"Error during report generation: {str(e)}")

if __name__ == "__main__":
    assign_initial_admin()
    auth()
