from exts import db
from datetime import datetime
from sqlalchemy import CheckConstraint


class UserModel(db.Model):
    __tablename__ = "user"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # id，编号，主键
    phone = db.Column(db.String(11), unique=True, nullable=False)
    # phone number, check 11位在输入时检查
    name = db.Column(db.String(10), nullable=False)
    # real name
    idcard = db.Column(db.String(18), nullable=False, unique=True)  # py程序check 18位，至于是否校验身份证的合法性的话...尚待决定
    # id card
    age = db.Column(db.Integer, CheckConstraint('age>=0'), nullable=False)
    # age must >= 0
    sex = db.Column(db.Integer, nullable=False, default=0)
    # sex, 0:Female; 1:Male
    nickname = db.Column(db.String(20), nullable=False)
    # nickname, 限制可以在插入数据时，通过py程序控制
    password = db.Column(db.String(200), nullable=False)
    # 因为采用werkzeug.security.generate_password加密，会让密码变长...所以设置的是string(200)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # create account time, not so useful
    indentify = db.Column(db.Integer, CheckConstraint(' indentify >= 0 and indentify<=2'), nullable=False, default=0)
    # 0:common Passenger; 1: Captain; 2:Admin
    # passengers = db.relationship("PassengerModel", secondary="userpassenger", backref="users")


class UserPassengerModel(db.Model):
    __tablename__ = "userpassenger"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_phone = db.Column(db.String(11), db.ForeignKey("user.phone"), nullable=False)
    passenger_idcard = db.Column(db.String(18), db.ForeignKey("passenger.idcard"), nullable=False)


class PassengerModel(db.Model):
    __tablename__ = "passenger"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idcard = db.Column(db.String(18), nullable=False, unique=True)
    # py程序check 18位，至于是否校验身份证的合法性的话...尚待决定
    name = db.Column(db.String(10), nullable=False)
    # real name
    age = db.Column(db.Integer, CheckConstraint('age>=0'), nullable=False)
    # age >= 0
    sex = db.Column(db.Integer, nullable=False, default=0)
    # sex, 0:Female; 1:Male
    users = db.relationship("UserModel", secondary="userpassenger", backref="passengers")


class AdminModel(db.Model):
    __tablename__ = "admin"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    salary = db.Column(db.Integer, CheckConstraint('salary>0'), nullable=False)
    description = db.Column(db.Text, nullable=True, default="No description.")
    user = db.relationship(UserModel, backref="admins")


class CaptainModel(db.Model):
    __tablename__ = "captain"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    salary = db.Column(db.Integer, CheckConstraint('salary>0'), nullable=False, default=5000)
    description = db.Column(db.Text, nullable=True, default="No description.")
    user = db.relationship(UserModel, backref="captains")


class TrainModel(db.Model):
    __tablename__ = "train"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 编号，也可以理解为类型的编号
    type = db.Column(db.String(20), unique=True, nullable=False)
    # 类型的名字（id和type其实有点重复）
    number = db.Column(db.Integer, CheckConstraint("number >= 0"), nullable=False)
    # 该种车型的数量
    runtime = db.Column(db.Integer, CheckConstraint("runtime>=0"), nullable=False)
    # 投入使用的时间，其实应该自动增长的，这里简化一下
    seat_size = db.Column(db.Integer, CheckConstraint("seat_size > 0"), nullable=False, default=60)
    # 座位数量
    coach_size = db.Column(db.Integer, CheckConstraint("coach_size > 0"), nullable=False, default=15)
    introduction = db.Column(db.Text, nullable=True)
    # 车型简介？有点不必要


class RouteModel(db.Model):
    # 路线
    __tablename__ = "route"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(10), nullable=False)
    start_station = db.Column(db.String(10), nullable=False)
    end_station = db.Column(db.String(10), nullable=False)


class TripModel(db.Model):
    # 车次
    __tablename__ = "trip"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 由于存储时间只能使用datetime,但是这又涉及时分秒，插入数据不太方便，于是将年月日分开储存
    dateYear = db.Column(db.Integer, nullable=False, default=2023)
    dateMonth = db.Column(db.Integer, nullable=False, default=6)
    dateDay = db.Column(db.Integer, nullable=False, default=1)
    # time part
    tickets_num = db.Column(db.Integer, CheckConstraint("tickets_num>=0"), nullable=False)
    # 总票数
    res_tickets = db.Column(db.Integer, CheckConstraint("res_tickets>=0"), nullable=False)
    # 剩余票数
    route_id = db.Column(db.Integer, db.ForeignKey("route.id"), nullable=False)
    # route id
    train_id = db.Column(db.Integer, db.ForeignKey("train.id"), nullable=False)
    # train id
    captain_id = db.Column(db.Integer, db.ForeignKey("captain.id"), nullable=False)
    # captain id

    # relationship
    route = db.relationship(RouteModel, backref="trips")
    train = db.relationship(TrainModel, backref="trips")
    captain = db.relationship(CaptainModel, backref="trips")


class StationModel(db.Model):
    # 站点以及时刻
    __tablename__ = "station"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 编号, PK
    route_id = db.Column(db.Integer, db.ForeignKey("route.id"), nullable=False)
    # route id
    # 由于没找到好的只存储HH::MM的方法，于是只好把小时和分钟分成两个部分存储了...
    # 由于有的路线可能会花费几天时间，所以增加一个arrive_day
    name = db.Column(db.String(18), nullable=False)
    arrive_day = db.Column(db.Integer, CheckConstraint("arrive_day>=0"), nullable=False, default=0)
    arrive_hour = db.Column(db.Integer, CheckConstraint("arrive_hour >=0 and arrive_hour < 24"), nullable=False)
    arrive_minute = db.Column(db.Integer, CheckConstraint("arrive_minute >=0 and arrive_minute < 60"), nullable=False)
    # arrive time part
    break_time = db.Column(db.Integer, CheckConstraint("break_time > 0"), nullable=False, default=5)
    # 停留时间（分钟）
    # relationship
    route = db.relationship(RouteModel, backref="stations")


class TicketModel(db.Model):
    __tablename__ = "ticket"
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_general_ci',
    }
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # id, PK
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 购票者
    passenger_id = db.Column(db.String(18), db.ForeignKey('passenger.idcard'), nullable=False)
    # id-card | passenger |乘车的人 != 买票的人
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    # 车次id
    state = db.Column(db.Integer, default=0, nullable=False)
    # state: False(0) not use and not overdue; True(1), used or overdue; default: is usable
    # seat = db.Column(db.Integer, nullable=False)
    # coach = db.Column(db.Integer, nullable=False)
    start_station = db.Column(db.String(18), nullable=False)
    end_station = db.Column(db.String(18), nullable=False)
    # check whether the seat or coach is available, whether out of range?
    # based on the type of train, 在后续py程序中实现
    buy_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # create/buy ticket time. Not so useful?

    # relationship || back reference
    user = db.relationship(UserModel, backref="tickets")
    passenger = db.relationship(PassengerModel, backref="tickets")
    trip = db.relationship(TripModel, backref="tickets")
