import cx_Oracle

print("Attempting to connect...")

try:
    # Use a full connection string instead of "MINE"
    connection = cx_Oracle.connect("system", "manager", "localhost:1521/XE")  
    print("Connected successfully!")

    # Close connection after success
    connection.close()

except cx_Oracle.DatabaseError as e:
    print("Error connecting to database:", e)
