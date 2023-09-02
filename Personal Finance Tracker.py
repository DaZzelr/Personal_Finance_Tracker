import mysql.connector
import hashlib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from decimal import Decimal
import csv
from multiprocessing import Pool

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

def register(username, password):
    query = "SELECT * FROM users WHERE username = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (username,))
        if cursor.fetchone():
            print("Username already exists.") 
        else:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            insert_query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
            cursor.execute(insert_query, (username, hashed_password))
            conn.commit()
            print("Registration successful.")
            auth()

def login(username, password):
    query = "SELECT id, password_hash FROM users WHERE username = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if result and result[1] == hashlib.sha256(password.encode()).hexdigest():
            print("Login successful.")
            main(result[0])
        else:
            print("Invalid credentials.")

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
        print("9. Analyze Financial Data:")  # New option
        print("10. Export Financial Data to CSV:")  # New option
        print("11. Import Financial Data from CSV:")  # New option
        print("12. Generate Reports:")  # New option
        print("13. Exit")

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
            analyze_financial_data(user_id)  # New option
        elif choice == '10':
            export_financial_data_csv(user_id)  # New option
        elif choice == '11':
            import_financial_data_csv(user_id)  # New option
        elif choice == '12':
            generate_reports(user_id)  # New option
        elif choice == '13':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please choose again.")

def auth(): 
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
        login(username, password)
    else:
        print("Invalid choice. Please choose again.")

def input_data(user_id):
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

    batch_insert_financial_data(user_id, data_list)
    print("Financial data added successfully.")

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
    query = "SELECT income, expense, monthly_investment FROM financial_data WHERE user_id = %s"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        financial_data = cursor.fetchall()

    if financial_data:
        incomes = [data[0] for data in financial_data]
        expenses = [data[1] for data in financial_data]
        monthly_investment = [data[2] for data in financial_data]

        plt.figure(figsize=(10, 6))
        plt.bar(range(len(incomes)), incomes, color='green', label='Income')
        plt.bar(range(len(expenses)), expenses, color='red', label='Expense')
        plt.bar(range(len(monthly_investment)), monthly_investment, color='blue', label='Investment')
        
        plt.xlabel('Financial Record')
        plt.ylabel('Amount')
        plt.title('Financial Data Visualization')
        plt.xticks(range(len(incomes)), [f'Record {i+1}' for i in range(len(incomes))])
        plt.legend()
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
    print("Investment Tracking:")
    print("1. Add Investment")
    print("2. View Investments")
    choice = input("Enter your choice: ")

    if choice == '1':
        add_investment(user_id)
    elif choice == '2':
        view_investments(user_id)
    else:
        print("Invalid choice.")

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

            batch_insert_financial_data(user_id, data_list)

        print(f"Financial data imported from '{csv_file_name}' successfully.")
    except Exception as e:
        print(f"Error during import: {str(e)}")

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
    auth()
