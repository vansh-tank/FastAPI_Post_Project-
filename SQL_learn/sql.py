import mysql.connector  
from mysql.connector import Error

try:
  conn = mysql.connector.connect(
      host='localhost',
      database='FastAPI',
      user='root',
      password='vanshtank',
      port=3306
  )
  if conn.is_connected():
      print('Connected to MySQL database')
except Error as e:
  print(f'Error connecting to MySQL database: {e}') 
cursor = conn.cursor()
print('-----------------------------------')
cursor.execute('desc posts')

for i in cursor:
    print(i)

# cursor.rowcount returns the number of rows affected by the last executed statement for update insert and delete statements
# fetchone give one reverses pointer and throws internal error when we close cursor without reading all data at end None is given 
# fetchmany we define how many rows we want to read and it gives us that many rows and moves pointer forward and throws
# internal error when we close cursor without reading all data at end None is given
# put  in conn.cursor(prepared = True) for fast and prevent injection 


sql = "INSERT INTO posts (title, content, published) VALUES (%s, %s, %s)"
cursor.execute(sql, ('vansh', 'tank', True))
conn.commit()
cursor.close()
conn.close()
print('MySQL connection closed')

