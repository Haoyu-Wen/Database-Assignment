import wtforms
from wtforms.validators import Length, EqualTo, InputRequired, Regexp, NumberRange
from models import UserModel, PassengerModel


# verify the form if is valid
class RegisterForm(wtforms.Form):
    # phonenumber; name; idcard; age; sex; nickname; password
    phonenumber = wtforms.StringField(validators=[Regexp(r'1[34578]\d{9}', message='手机号格式错误')])
    nickname = wtforms.StringField(validators=[Length(min=2, max=20, message="用户名必须为2-20个字符")])
    password = wtforms.StringField(validators=[Length(min=5, max=10, message="密码为5-10位")])
    confirm_password = wtforms.StringField(validators=[EqualTo("password",message="密码不一致")])
    name = wtforms.StringField(validators=[Length(min=2, max=10, message="真实姓名应该为2-10位")])
    age = wtforms.IntegerRangeField(validators=[NumberRange(min=0, max=100, message="年龄应该为0-100岁")])
    idcard = wtforms.StringField(validators=[Length(min=18, max=18, message="身份证号应该为18位")])


class LoginForm(wtforms.Form):
    phone = wtforms.StringField(validators=[Regexp(r'1[34578]\d{9}', message='手机号格式错误')])
    password = wtforms.StringField(validators=[Length(min=5, max=10,message="密码为5-10位,格式错误")])


class PassengerForm(wtforms.Form):
    idcard = wtforms.StringField(validators=[Length(min=18, max=18, message="身份证号应该为18位")])
    name = wtforms.StringField(validators=[Length(min=2, max=10, message="真实姓名应该为2-10位")])
    age = wtforms.IntegerRangeField(validators=[NumberRange(min=0, max=100, message="年龄应该为0-100岁")])


class ModifyForm(wtforms.Form):
    name = wtforms.StringField(validators=[Length(min=2, max=10, message="真实姓名应该为2-10位")])
    # age = wtforms.IntegerRangeField(validators=[NumberRange(min=0, max=100, message="年龄应该为0-100岁")])
    nickname = wtforms.StringField(validators=[Length(min=2, max=20, message="用户名必须为2-20个字符")])
