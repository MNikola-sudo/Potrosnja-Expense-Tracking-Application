# Potrosnja-Expense-Tracking-Application
![pocetna](https://github.com/user-attachments/assets/437b6388-2aa6-479e-9f79-c343be6d3ecf)

This expense tracking application, built using Flask and SQLAlchemy, provides users with an efficient and organized way to manage their personal finances. It allows for account creation, expense tracking, categorization, and displays monthly spending summaries.

![po_mjesecima](https://github.com/user-attachments/assets/38816944-4eab-40d2-9c1b-95ae2dd06ab2)

![korisnik](https://github.com/user-attachments/assets/18cd6c92-69d5-40e1-9b50-ec0c4c3d2154)


## Key Features:
  1. User Registration and Login: Users can create an account by entering basic information (first name, last name, username, and password). Passwords are securely hashed using bcrypt, while the application checks for unique usernames to prevent duplicates.
  
  2. Expense Tracking: Users can log expenses with details such as the amount, category (e.g., food, transportation), date, and an optional receipt image. Each expense is linked to a specific user, ensuring a personalized experience.
  
  3. Expense Categorization: Users can organize their expenses into custom categories, making it easier to analyze and track spending across different areas.
  
  4. Monthly Summaries: The main application page displays a summary of expenses for the current month, including the total amount spent and the highest single expense for that period. This helps users monitor their financial habits and make informed decisions.
  
  5. Receipt Image Download and Preview: If an image of a receipt is attached to an expense, users can view or download it as a reference.

![kategorije](https://github.com/user-attachments/assets/c83a114a-9a81-4243-8a59-004da9ccb2de)

![graf](https://github.com/user-attachments/assets/972c1e0d-e832-473a-891e-31433c4fde49)


## Technical Details:
  Database: The application uses SQLAlchemy ORM to manage data stored in an SQLite database, allowing flexible data handling and scalability.
  User Authentication: Flask-Login manages sessions to ensure that only logged-in users can access their data.
  Password Security: Bcrypt is used for secure password hashing to protect user information.
  Web Forms: User forms created with WTForms include input validation, making registration and login user-friendly.
  
This application is ideal for users looking to gain insight into their monthly spending, analyze their financial habits, and track personal financial goals.
