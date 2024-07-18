from flask import Blueprint, request, render_template, redirect, g, url_for, session
from exts import db
from models import UserModel, CaptainModel, PassengerModel, UserPassengerModel, AdminModel, StationModel, TicketModel, \
    TripModel, RouteModel, TrainModel
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import RegisterForm, LoginForm, ModifyForm
from decorators import login_requried
from sqlalchemy import text
from datetime import datetime

# include register, login, account center
bp = Blueprint("account", __name__, url_prefix="/account")


@bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        form = RegisterForm(request.form)
        if form.validate():
            # 得到表单数据，有的是表单验证过的，有的是request.form.get获得的（string类型）
            password = form.password.data
            phone = form.phonenumber.data
            sex = int(request.form.get("sex"))
            indentify = int(request.form.get("indentify"))
            age = int(form.age.data)
            nickname = form.nickname.data
            name = form.name.data
            idcard = form.idcard.data
            result = UserModel.query.filter_by(phone=phone).all()
            if result:
                # user是否存在
                return render_template("return.html", value="电话被注册喽！")
            else:
                # 首先需要查看passenger表中是否存在该人，然后比较name、idcard、sex、age等是否符合
                result = PassengerModel.query.filter_by(idcard=idcard).first()
                if not result:
                    # 不存在
                    passenger = PassengerModel(idcard=idcard, name=name, sex=sex, age=age)
                    db.session.add(passenger)
                    db.session.commit()
                else:
                    # passenger存在，则检查对应乘客信息
                    if result.age != age or result.sex != sex or result.idcard != idcard or result.name != name:
                        return render_template("return.html", value="输入信息和系统已储存的信息不一致，请检查个人信息部分")
                # 无误后（不存在passenger则创建，存在passenger比对信息），再创建user
                password = generate_password_hash(password)
                user = UserModel(phone=phone, name=name, nickname=nickname, age=age, sex=sex, indentify=indentify,
                                 idcard=idcard, password=password)
                # user 被创建，user passenger一定不存在，需要创建
                user_passenger = UserPassengerModel(user_phone=phone, passenger_idcard=idcard)
                db.session.add_all([user, user_passenger])
                db.session.commit()
                if indentify == 1:
                    result = CaptainModel.query.filter_by(id=user.id).first()
                    if not result:
                        captain = CaptainModel(id=user.id, salary=5000, description=None)
                        db.session.add(captain)
                        db.session.commit()
                if indentify == 2:
                    result = AdminModel.query.filter_by(id=user.id).first()
                    if not result:
                        admin = AdminModel(id=user.id, salary=10000)
                        db.session.add(admin)
                        db.session.commit()
            return render_template("return.html", value="账户创建成功！")
        else:
            return render_template('form_errors.html', errors=form.errors)


@bp.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:  # method = POST
        form = LoginForm(request.form)
        phone = form.phone.data
        password = form.password.data
        if not form.validate():
            print(form.errors)
            return render_template('form_errors.html', errors=form.errors)

        else:
            result = UserModel.query.filter_by(phone=phone).first()
            if not result:
                return render_template("return.html", value="no such phone")
            else:
                if check_password_hash(result.password, password):
                    session["user_id"] = result.id
                    return redirect("/")
                else:
                    return render_template("return.html", value="password error")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect('/')


@bp.route("/center", methods=['GET'])
@login_requried
def center():
    if g.user.indentify == 0:
        return render_template('account_passenger.html')
    elif g.user.indentify == 1:
        captain = CaptainModel.query.filter_by(id=g.user.id).first()
        return render_template('account_captain.html', captain=captain)
    elif g.user.indentify == 2:
        admin = AdminModel.query.filter_by(id=g.user.id).first()
        return render_template('account_admin.html', admin=admin)
    else:
        # 应该不会发生的hhh
        return "404 ERROR"


@bp.route("/shift_indentify", methods=['GET', 'POST'])
@login_requried
def shift_indentify():
    if request.method == 'GET':
        return render_template('shift.html')
    else:
        # post
        indentify = int(request.form.get("indentify"))
        if indentify == 0:
            return render_template("account_passenger.html")
        elif indentify == 1:
            captain = CaptainModel.query.filter_by(id=g.user.id).first()
            return render_template("account_captain.html", captain=captain)
        else:
            admin = AdminModel.query.filter_by(id=g.user.id).first()
            return render_template("account_admin.html", admin=admin)


@bp.route("/relational_passengers", methods=['POST', 'GET'])
@login_requried
def relational_passengers():
    if request.method == 'POST':
        idcard = request.form.get('idcard')
        passenger = UserPassengerModel.query.filter_by(user_phone=g.user.phone, passenger_idcard=idcard).first()
        if passenger:
            if passenger.passenger_idcard == g.user.idcard:
                return render_template('return.html', value="不能删除自己和自己的关联")
            db.session.delete(passenger)
            db.session.commit()
            return render_template("return.html", value="删除成功")
        else:
            return render_template("return.html", value="未查询到关联的乘客，请刷新")
    passengers = UserPassengerModel.query.filter_by(user_phone=g.user.phone)
    all_passengers = []
    for passenger in passengers:
        all_passengers.append(PassengerModel.query.filter_by(idcard=passenger.passenger_idcard).first())
    return render_template("show_passengers.html", passengers=all_passengers)


@bp.route("/bought_tickets_user", methods=['POST', 'GET'])
@login_requried
def bought_tickets_user():
    tickets = TicketModel.query.filter_by(user_id=g.user.id).all()
    # ticket(id,user_id,passenger_id,trip_id,state,seat,coach,buy_time)
    # 似乎只显示ticket的信息有点，单薄，显示route,trip的一些信息可能比较好
    # 显示user_name, user_phone, passenger_name, passenger_idcard, date, captain_name, train_type, route_name
    # s_station, e_station, buy_time, state
    results = []
    for ticket in tickets:
        sql = text(f"SELECT user.name as uname, user.phone phone, passenger.name pname, passenger.idcard pidcard,"
                   f" trip.dateYear dyear, trip.dateMonth dmonth, trip.dateDay dday, route.name rname, train.type type,"
                   f"route.start_station ss, route.end_station es, ticket.buy_time buy_time, ticket.state state,"
                   f" ticket.start_station tss, ticket.end_station tes, ticket.id tid "
                   f"FROM user,passenger,ticket,train,route,trip "
                   f"WHERE user.id={ticket.user_id} AND passenger.idcard='{ticket.passenger_id}' AND "
                   f"trip.id={ticket.trip_id} AND route.id=trip.route_id AND "
                   f"train.id=trip.train_id AND ticket.id={ticket.id}")
        result = db.session.execute(sql)
        result = result.fetchone()
        # 只有一条数据
        results.append(result)
    return render_template("show_bought_tickets.html", infos=results, value="我购买的车票")


@bp.route("/bought_tickets_passenger", methods=['POST', 'GET'])
@login_requried
def bought_tickets_passenger():
    tickets = TicketModel.query.filter_by(passenger_id=g.user.idcard).all()
    # 和上面类似，只不过查询条件变成了自己的idcard，user-id 不是g.user.id了
    results = []
    for ticket in tickets:
        sql = text(f"SELECT user.name as uname, user.phone phone, passenger.name pname, passenger.idcard pidcard,"
                   f" trip.dateYear dyear, trip.dateMonth dmonth, trip.dateDay dday, route.name rname, train.type type,"
                   f"route.start_station ss, route.end_station es, ticket.buy_time buy_time, ticket.state state, "
                   f"ticket.start_station tss, ticket.end_station tes, ticket.id tid "
                   f"FROM user,passenger,ticket,train,route,trip "
                   f"WHERE user.id={ticket.user_id} AND passenger.idcard='{ticket.passenger_id}' AND "
                   f"trip.id={ticket.trip_id} AND route.id=trip.route_id AND "
                   f"train.id=trip.train_id AND ticket.id={ticket.id}")
        result = db.session.execute(sql)
        result = result.fetchone()
        # 只有一条数据
        results.append(result)
    return render_template("show_bought_tickets.html", infos=results, value="我的车票")


@bp.route("/delete_ticket/<ticket_id>")
@login_requried
def delete_ticket(ticket_id):
    ticket = TicketModel.query.filter_by(id=ticket_id).first()
    db.session.execute(text(f"UPDATE trip SET res_tickets=res_tickets+1 WHERE id={ticket.trip_id}"))
    db.session.commit()
    db.session.delete(ticket)
    db.session.commit()
    return render_template("return.html", value="退票成功")


@bp.route("/show_trips", methods=['GET'])
@login_requried
def show_trips():
    # return "show trips"
    now_time = datetime.utcnow().strftime("%Y-%m-%d").split('-')
    trips = TripModel.query.all()
    t_year, t_month, t_day = int(now_time[0]), int(now_time[1]), int(now_time[2])
    all_trip = []
    for trip in trips:
        if trip.dateYear > t_year or (trip.dateYear == t_year and trip.dateMonth > t_month) or \
                (trip.dateYear == t_year and trip.dateMonth == t_month and trip.dateDay >= t_day):
            sql = text(f"SELECT trip.dateYear as year, trip.dateMonth month, trip.dateDay day, trip.res_tickets "
                        f"res_tickets, trip.tickets_num all_tickets, user.name cname, route.start_station ss, "
                        f"route.end_station es, route.name "
                        f"rname, train.type type "
                        f"FROM user, train, route, trip " \
                        f"WHERE user.id={trip.captain_id} AND train.id={trip.train_id} AND trip.id={trip.id} AND " 
                        f"route.id={trip.route_id}")
            t_trip = db.session.execute(sql)
            t_trip = t_trip.fetchone()
            all_trip.append(t_trip)
    return render_template("show_trips.html", trips=all_trip)


@bp.route("/show_routes", methods=['GET'])
@login_requried
def show_routes():
    routes = RouteModel.query.all()
    all_routes = []
    for route in routes:
        sql = text(f"SELECT route.name as rname, station.name sname, station.arrive_day day, station.arrive_hour "
                    f"hour, station.arrive_minute minute, station.break_time break, route.id id "
                    f"FROM station,route "
                    f"WHERE route.id={route.id} AND station.route_id={route.id} "
                    f"ORDER BY station.arrive_day, station.arrive_hour, station.arrive_minute")
        t_route = db.session.execute(sql)
        t_route = t_route.fetchall()
        all_routes.append(t_route)
    return render_template('show_routes.html', routes=all_routes)


@bp.route("/add_trips", methods=['POST', 'GET'])
@login_requried
def add_trips():
    if request.method == 'GET':
        routes = RouteModel.query.all()
        captains = db.session.execute(text(f"SELECT captain.id as id, user.name as cname FROM user,captain "
                                           f"WHERE user.id=captain.id")).fetchall()
        trains = TrainModel.query.all()
        return render_template("add_trips.html", routes=routes, captains=captains, trains=trains)
    else:
        # 没啥必要写表单验证了...直接这里判断了
        route_id = int(request.form.get("route_id"))
        ticket_num = int(request.form.get("all_tickets"))
        res_ticket = ticket_num
        date = request.form.get('date').split("-")
        year, month, day = int(date[0]), int(date[1]), int(date[2])
        captain_id = int(request.form.get("captain_id"))
        train_id = int(request.form.get("train_id"))
        trip = TripModel(dateYear=year, dateMonth=month, dateDay=day, captain_id=captain_id, route_id=route_id,
                         train_id=train_id, res_tickets=res_ticket, tickets_num=ticket_num)
        db.session.add(trip)
        db.session.commit()
        return render_template("return.html", value="车次添加成功！")


@bp.route("/add_routes", methods=['POST', 'GET'])
@login_requried
def add_routes():
    if request.method == 'GET':
        return render_template("add_routes.html")
    else:
        data = ["name", "day", "hour", "minute", "breaktime"]
        all_data = []
        count = 0
        rname = request.form.get("route_name") #route name
        while 1:
            t_data = [request.form.get(data[i]+str(count)) for i in range(0, 5)]
            if t_data[0]:
                name, day, hour, minute, breaktime = t_data[0], int(t_data[1]), int(t_data[2]), int(t_data[3]), \
                    int(t_data[4])
                all_data.append([name, day, hour, minute, breaktime])
            else:
                break
            count += 1
        all_data.sort(key=lambda x: x[1]*61*25+x[2]*61+x[3], reverse=False)
        # 加权对 day,hour, minute排了个序，方便确定start, end -station
        start_station = all_data[0][0]
        end_station = all_data[-1][0]
        route = RouteModel(name=rname, start_station=start_station, end_station=end_station)
        db.session.add(route)
        db.session.commit()
        for _ in all_data:
            station = StationModel(route_id=route.id, name=_[0], arrive_day=_[1], arrive_hour=_[2],
                                   arrive_minute=_[3], break_time=_[4])
            db.session.add(station)
            db.session.commit()
        return render_template("return.html", value="添加路线成功！")


@bp.route("/show_captains", methods=['POST', 'GET'])
@login_requried
def show_captains():
    if request.method == 'GET':
        # captains = UserModel.query.filter_by(indentify=1)
        captains = db.session.execute(text("SELECT captain.id as id, user.name name, user.sex sex, user.age age "
                                           "FROM user,captain WHERE user.id=captain.id")).fetchall()
        return render_template("show_captains.html", captains=captains)
    else:
        return "show captains"


@bp.route("/show_captain/<captain_id>", methods=['GET'])
@login_requried
def show_captain(captain_id):
    captain = db.session.execute(text(f"SELECT * FROM user,captain WHERE user.id={captain_id} AND captain.id="
                                      f"{captain_id}")).fetchone()
    return render_template("show_captain.html", captain=captain)


@bp.route("/show_trains", methods=['GET'])
@login_requried
def show_trains():
    trains = TrainModel.query.all()
    return render_template("show_trains.html", trains=trains)


@bp.route("/add_trains", methods=['POST', 'GET'])
@login_requried
def add_trains():
    if request.method == 'GET':
        return render_template("add_trains.html")
    else:
        t_type = request.form.get("type")
        number = int(request.form.get("number"))
        runtime = int(request.form.get("runtime"))
        seat = int(request.form.get("seat"))
        coach = int(request.form.get("coach"))
        introduction = request.form.get("introduction")
        if TrainModel.query.filter_by(type=t_type).first():
            return render_template("return.html", value="已经有该型号的列车了！")
        else:
            train = TrainModel(type=t_type, number=number, runtime=runtime, seat_size=seat, coach_size=coach,
                               introduction=introduction)
            db.session.add(train)
            db.session.commit()
            return render_template("return.html", value='添加列车成功')


@bp.route("/my_trips", methods=['GET'])
@login_requried
def my_trips():
    if g.user.indentify != 1:
        return render_template("return.html", value="您的身份不是列车长！")
    else:
        sql = text(f"SELECT trip.dateYear as year, trip.dateMonth month, trip.dateDay day, route.name rname, train.type"
                   f" type, station.arrive_hour hour, station.arrive_minute  minute "
                   f"FROM trip,route,train,station "
                   f"WHERE trip.captain_id={g.user.id} AND train.id=trip.train_id AND route.id=trip.route_id AND"
                   f" station.route_id=route.id AND station.name=route.start_station")
        trips = db.session.execute(sql).fetchall()
        return render_template("my_trips.html", trips=trips)


@bp.route("/modify", methods=['POST', 'GET'])
@login_requried
def modify():
    if request.method == 'GET':
        if g.user.indentify == 0:
            user=None
        elif g.user.indentify == 1:
            user = CaptainModel.query.filter_by(id=g.user.id).first()
        else:
            user = AdminModel.query.filter_by(id=g.user.id).first()
        return render_template("modify.html", user=user)
    else:
        form = ModifyForm(request.form)
        name = form.name.data
        nickname = form.nickname.data
        age = int(request.form.get("age"))
        sex = int(request.form.get("sex"))
        db.session.execute(text(f"UPDATE user set name='{name}', nickname='{nickname}', age={age}, sex={sex} "
                                f"where id={g.user.id}"))
        db.session.commit()
        db.session.execute(text(f"UPDATE passenger set name='{name}', age={age}, sex={sex} "
                                f"where id={g.user.id}"))
        db.session.commit()
        if g.user.indentify != 0:
            description = request.form.get("description")
            indentify_dict = {1: "captain", 2: 'admin'}
            indentify = indentify_dict[g.user.indentify]
            print(indentify)
            description = request.form.get("description")
            db.session.execute(text(f"UPDATE {indentify} set description='{description}' WHERE id={g.user.id}"))
            db.session.commit()
        return render_template("return.html", value="修改成功")


