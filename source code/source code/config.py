SECRET_KEY = "GoodGradesOnDataBaseAssignment"

# config of connection with database(MySQL)
HOSTNAME = "127.0.0.1"  # Hostname, 本机完成
PORT = "3306"  # Port, MySQL‘s default port is 3306
DATABASE = "TICKETSYSTEM"  #  database name, TICKETSYSTEM, 车票管理系统...
USERNAME = "root"  # user, root
PASSWORD = "20030611wen"  # psw of root
DB_URI = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"  # encoding way:utf8mb4
SQLALCHEMY_DATABASE_URI = DB_URI
