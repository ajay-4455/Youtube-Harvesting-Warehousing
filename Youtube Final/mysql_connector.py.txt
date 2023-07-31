import mysql.connector

def connect_to_mysql():
    mysql_conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="youtube_database"  
    )
    return mysql_conn
