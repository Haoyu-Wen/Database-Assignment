from flask import Blueprint, request, render_template, redirect, g, url_for, session
# from
from exts import db
from models import UserModel, CaptainModel, PassengerModel, UserPassengerModel, RouteModel, StationModel, \
    TripModel, TrainModel, TicketModel
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import PassengerForm
from decorators import login_requried
from sqlalchemy import text

bp = Blueprint("index", __name__, url_prefix="/")
# 不安全的全局变量传参...为了简化出此下策，暂时没想到更好的解决方案
start_station = ""
end_station = ""


@bp.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return render_template("index.html")
    else:
        start_station = request.form.get('start_station')
        end_station = request.form.get('end_station')
        print("*"*10)
        print(start_station, end_station)
        print("*"*10)
        date = request.form.get('trip_date').split('-')
        year, month, day = int(date[0]), int(date[1]), int(date[2])
        # 根据日期进行查询,得到了所有当天出发的trip/车次，然后我们再查询起点、终点站是否在里面即可(根据route id)
        sql = text(f"SELECT "
                   f"route.name, route.id as route_id, trip.id trip_id, trip.dateYear, trip.dateMonth,"
                   f"trip.dateDay, trip.res_tickets, trip.train_id,trip.captain_id, start_station, end_station "
                   f"FROM route,trip WHERE trip.dateYear={year} AND trip.dateMonth={month} And "
                   f"trip.dateDay={day} AND trip.route_id=route.id")
        trip_route_proxy = db.session.execute(sql)
        trip_routes = trip_route_proxy.fetchall()
        if not trip_routes:
            return render_template("return.html", value="没有符合要求的车票")
        else:
            # this part 根据route id 查询起点、终点是否在里面
            trips = []
            trains = []
            captains = []
            # 存储一些其它要显示的信息，诸如火车型号，余票
            for trip_route in trip_routes:
                sql = text(f"SELECT * FROM station WHERE route_id={trip_route.route_id}"
                           f" ORDER BY arrive_day , arrive_hour, arrive_minute ")
                stations_proxy = db.session.execute(sql)
                stations = stations_proxy.fetchall()
                station_positive = [station.name for station in stations]
                # 根据抵达时间所排的正向到站顺序的站点名
                if (start_station in station_positive) and (end_station in station_positive) \
                        and (station_positive.index(start_station) < station_positive.index(end_station)):
                    # 终点、起点是否在站点list里面，以及顺序是否正确
                    trips.append(trip_route)
                    # 添加trip_route
                    train = TrainModel.query.filter_by(id=trip_route.train_id).first()
                    sql = text(f'SELECT user.name AS name, user.id id FROM user WHERE '
                               f'user.id={trip_route.captain_id}')
                    captain = db.session.execute(sql)
                    captain = captain.fetchone()
                    trains.append(train)
                    captains.append(captain)
                    # captain = CaptainModel.query.filter_by(id=trip_route.captain_id).first()
                    # 其实要显示的应该是captain name，但是captain表没存储需要和user表关联一下
                    # 或许换一下储存方式会比较好？比如captain表也储存name之类的，或者干脆把user、captain、admin分成互不相干的三个表？

            if not trips:
                return render_template("return.html", value="没有符合要求的票")
            else:
                return render_template("show_ticket.html", stations=stations, trips=trips, captains=captains,
                                       trains=trains, st=start_station, es=end_station)
                # return render_template("buy_ticket.html", stations=stations, trip_routes=all_trips)


@bp.route("/show/<trip_id>", methods=['POST', 'GET'])
@login_requried
def show_ticket(trip_id):
    if request.method == 'GET':
        trips = TripModel.query.filter_by(id=trip_id).all()
        passengers = UserPassengerModel.query.filter_by(user_phone=g.user.phone).all()
        u_passengers = []
        for passenger in passengers:
            u_passenger = PassengerModel.query.filter_by(idcard=passenger.passenger_idcard).first()
            # .first() .all() 效果一样不过返回类型有点不一样，all是可迭代的
            u_passengers.append(u_passenger)
        return render_template("detail_ticket.html", trips=trips, passengers=u_passengers, trip_id=trip_id)
    else:
        # post，点击购买按钮
        passenger_idcard = request.form.get('buy')
        result = TicketModel.query.filter_by(trip_id=trip_id, passenger_id=passenger_idcard).first()
        # 查看相应trip, 该passenger是否有票，如果有票，则不能购买；以及是否还剩票
        if not result:
            trip = TripModel.query.filter_by(id=trip_id).first()
            # 是否剩票
            if trip.res_tickets == 0:
                return render_template("return.html", value="该车次已经没票了")
            else:
                ticket = TicketModel(user_id=g.user.id, passenger_id=passenger_idcard, trip_id=trip_id,
                                     start_station=start_station,
                                     end_station=end_station)
                db.session.add(ticket)
                db.session.commit()
                db.session.execute(text(f"UPDATE trip SET res_tickets=res_tickets-1 WHERE id={trip_id}"))
                db.session.commit()
                return render_template("return.html", value="购买成功")
        else:
            return render_template('return.html', value="该乘客在这个已经有这趟车的车票了")


@bp.route("/add_passenger", methods=['POST', 'GET'])
@login_requried
def add_passenger():
    if request.method == 'GET':
        return render_template('addpassenger.html')
    else:
        form = PassengerForm(request.form)
        if not form.validate():
            return render_template('form_errors.html', errors=form.errors)
        else:
            name = form.name.data
            age = form.age.data
            idcard = form.idcard.data
            sex = int(request.form.get('sex'))
            result = PassengerModel.query.filter_by(idcard=idcard).first()
            if not result:
                # 如果不存在则添加
                passenger = PassengerModel(name=name, age=age, idcard=idcard, sex=sex)
                user_passenger = UserPassengerModel(user_phone=g.user.phone, passenger_idcard=idcard)
                db.session.add_all([passenger, user_passenger])
                db.session.commit()
                return render_template('return.html', value='添加成功')
            else:
                # 存在的话:1.需要比对是否和表中信息一致 2.然后查看是否已经关联过了
                if name != result.name or age != result.age or idcard != result.idcard or sex != result.sex:
                    # 1.是否一致
                    return "输入信息和系统储存信息不一致"
                else:
                    # 2.是否关联
                    result = UserPassengerModel.query.filter_by(user_phone=g.user.phone, passenger_idcard=idcard).first()
                    if not result:
                        user_passenger = UserPassengerModel(user_phone=g.user.phone, passenger_idcard=idcard)
                        db.session.add(user_passenger)
                        db.session.commit()
                        return render_template('return.html', value="添加成功")
                    else:
                        return render_template('return.html', value="已经添加过该乘客，无法重复添加")

