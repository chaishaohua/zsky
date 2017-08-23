#encoding:utf-8
#我本戏子2017.7
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import random
import re
import base64
import json
import codecs
import time
import os
import datetime
from flask import Flask,request,render_template,session,g,url_for,redirect,flash,current_app,jsonify,send_from_directory
from flask_login import LoginManager,UserMixin,current_user,login_required,login_user,logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date, cast,func
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField,TextField,TextAreaField
from wtforms.validators import DataRequired,Length,EqualTo,ValidationError
from flask_babelex import Babel,gettext
from flask_admin import helpers, AdminIndexView, Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.form.upload import ImageUploadField
from getpass import getpass
from flask_caching import Cache
from werkzeug.security import generate_password_hash,check_password_hash
import jieba
import jieba.analyse
import pymysql
#from flask_debugtoolbar import DebugToolbarExtension


nvyoupath = os.path.join(os.path.dirname(__file__), 'uploads/nvyou')
fanhaopath = os.path.join(os.path.dirname(__file__), 'uploads/fanhao')
# Initialize Flask and set some config values
app = Flask(__name__)
app.config['DEBUG']=True
app.config['SECRET_KEY'] = 'super-secret'
#debug_toolbar=DebugToolbarExtension()
#debug_toolbar.init_app(app)
#app.config['DEBUG_TB_INTERCEPT_REDIRECTS']=False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/zsky'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_POOL_SIZE']=5000
db = SQLAlchemy(app)
manager = Manager(app)
migrate = Migrate(app, db)
babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
loginmanager=LoginManager()
loginmanager.init_app(app)
loginmanager.session_protection='strong'
loginmanager.login_view='login'
loginmanager.login_message = "请先登录！"
cache = Cache(app,config = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': '127.0.0.1',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': '',
    'CACHE_REDIS_PASSWORD': ''
})
cache.init_app(app)


DB_HOST='127.0.0.1'
DB_NAME_MYSQL='zsky'
DB_PORT_MYSQL=3306
DB_NAME_SPHINX='film'
DB_PORT_SPHINX=9306
DB_USER='root'
DB_PASS=''
DB_CHARSET='utf8mb4'

sitename="磁力管家"

class LoginForm(FlaskForm):
    name=StringField('用户名',validators=[DataRequired(),Length(1,32)])
    password=PasswordField('密码',validators=[DataRequired(),Length(1,20)])
    def get_user(self):
        return db.session.query(User).filter_by(name=self.name.data).first()


class ComplaintForm(FlaskForm):
    info_hash = StringField('Hash: ',validators = [DataRequired()])
    reason = TextAreaField('原因: ',validators = [DataRequired()])
    submit = SubmitField('屏蔽')

class SearchForm(FlaskForm):
    search = StringField(validators = [DataRequired(message= '请输入关键字')])
    submit = SubmitField('搜索')


class Complaint(db.Model):
    """ DMCA投诉记录 """
    __tablename__ = 'complaint'
    id = db.Column(db.Integer,primary_key=True,nullable=False,autoincrement=True)
    info_hash = db.Column(db.String(40), unique=True, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    create_time = db.Column(db.DateTime,default=datetime.datetime.now)

class Search_Filelist(db.Model):
    """ 这个表可以定期清空数据 """
    __tablename__ = 'search_filelist'
    info_hash = db.Column(db.String(40), primary_key=True,nullable=False)
    file_list = db.Column(db.Text,nullable=False)


class Search_Hash(db.Model,UserMixin):
    __tablename__ = 'search_hash'
    id = db.Column(db.Integer,primary_key=True,nullable=False,autoincrement=True)
    info_hash = db.Column(db.String(40),unique=True)
    category = db.Column(db.String(20))
    data_hash = db.Column(db.String(32))
    name = db.Column(db.String(200))
    extension = db.Column(db.String(20))
    classified = db.Column(db.Boolean())
    source_ip = db.Column(db.String(20))
    tagged = db.Column(db.Boolean(),default=False)
    length = db.Column(db.BigInteger)
    create_time = db.Column(db.DateTime,default=datetime.datetime.now)
    last_seen = db.Column(db.DateTime,default=datetime.datetime.now)
    requests = db.Column(db.Integer)
    comment = db.Column(db.String(100))
    creator = db.Column(db.String(20))



class Search_Keywords(db.Model):
    """ 影片推荐 """
    __tablename__ = 'search_keywords'
    id = db.Column(db.Integer,primary_key=True,nullable=False,autoincrement=True)
    keyword = db.Column(db.String(20),nullable=False,unique=True)
    order = db.Column(db.Integer,nullable=False)
    pic = db.Column(db.String(100),nullable=False)
    score = db.Column(db.String(10),nullable=False)

class Search_Actors(db.Model):
    """ 演员推荐 """
    __tablename__ = 'search_actors'
    id = db.Column(db.Integer,primary_key=True,nullable=False,autoincrement=True)
    actorname = db.Column(db.String(20),nullable=False,unique=True)
    order = db.Column(db.Integer,nullable=False)
    pic = db.Column(db.String(100),nullable=False)
    score = db.Column(db.String(10),nullable=False)

class Search_Tags(db.Model):
    """ 搜索记录 """
    __tablename__ = 'search_tags'
    id = db.Column(db.Integer,primary_key=True,nullable=False,autoincrement=True)
    tag = db.Column(db.String(50),nullable=False,unique=True)

class Search_Statusreport(db.Model):
    """ 爬取统计 """
    __tablename__ = 'search_statusreport'
    id = db.Column(db.Integer, primary_key=True,nullable=False,autoincrement=True)
    date = db.Column(db.DateTime,nullable=False,default=datetime.datetime.now)
    new_hashes = db.Column(db.Integer,nullable=False)
    total_requests = db.Column(db.Integer,nullable=False)
    valid_requests = db.Column(db.Integer,nullable=False)
    
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    email = db.Column(db.String(50),nullable=False)
    name = db.Column(db.String(50),unique=True,nullable=False)
    password = db.Column(db.String(200),nullable=False)
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return self.id
    def __unicode__(self):
        return self.username


def make_shell_context():
    return dict(app=app, db=db, Search_Filelist=Search_Filelist, Search_Hash=Search_Hash, Search_Keywords=Search_Keywords, Search_Tags=Search_Tags, Search_Actors=Search_Actors, Search_Statusreport=Search_Statusreport, User=User)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@loginmanager.user_loader
def load_user(id):
    return User.query.get(int(id))


def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return (path + args).encode('utf-8')


def todate_filter(s):
    return datetime.datetime.fromtimestamp(int(s)).strftime('%Y-%m-%d')
app.add_template_filter(todate_filter,'todate')

def fromjson_filter(s):
    try:
        return json.loads(s)
    except ValueError:
        pass
app.add_template_filter(fromjson_filter,'fromjson')

def tothunder_filter(magnet):
    return base64.b64encode('AA'+magnet+'ZZ')
app.add_template_filter(tothunder_filter,'tothunder')


yesterday=int(time.mktime(datetime.datetime.now().timetuple()))-86400
thisweek=int(time.mktime(datetime.datetime.now().timetuple()))-86400*7
categoryquery={0:"",1:"and category='影视'",2:"and category='音乐'",3:"and category='图像'",4:"and category='文档书籍'",5:"and category='压缩文件'",6:"and category='安装包'",7:"and category='其他'"}
sorts={0:"",1:"ORDER BY length DESC",2:"ORDER BY create_time DESC",3:"ORDER BY requests DESC",4:"ORDER BY last_seen DESC"}

def geticon_filter(ext):
    cats = {".html":"html",".nfo":"nfo",".pdf":"pdf",".url":"url",".aac":"audio",".flac":"audio",
        ".ape":"audio",".inf":"inf",".chm":"chm",".swf":"flash",".mp4":"mp4",".exe":"exe",
        ".txt":"txt",".iso":"iso",".text":"txt",".avi":"video",".rmvb":"video",".m2ts":"video",
        ".wmv":"video",".mkv":"video",".flv":"video",".qmv":"videovideo",".rm":"video",".mov":"video",
        ".vob":"video",".asf":"video",".3gp":"video",".mpg":"video",".mpeg":"video",".m4v":"video",
        ".f4v":"video",".ts":"video",".jpg":"jpg",".jpeg":"jpg",".bmp":"jpg",".png":"jpg",
        ".gif":"jpg",".tiff":"jpg",".mp3":"mp3",".wma":"mp3",".wav":"mp3",".dts":"mp3",
        ".mdf":"mp3",".mid":"mp3",".midi":"mp3",".zip":"rar",".rar":"rar", ".7z":"rar", 
        ".tar":"rar",".gz":"rar", ".dmg":"rar", ".pkg":"rar"}    
    return cats.get(ext,"other")
app.add_template_filter(geticon_filter,'geticon')


def fenci_filter(title,n):
    return jieba.analyse.extract_tags(title, n)
app.add_template_filter(fenci_filter,'fenci')

#@cache.cached(60*10,key_prefix=make_cache_key)
def filelist_filter(info_hash):
    try:
        return json.loads(Search_Filelist.query.filter_by(info_hash=info_hash).first().file_list)
    except:
        return [{
       'path':Search_Hash.query.filter_by(info_hash=info_hash).first().name, 
       'length':Search_Hash.query.filter_by(info_hash=info_hash).first().length
       }]
app.add_template_filter(filelist_filter,'filelist')


@cache.cached(60*10,key_prefix="total_cache")
def totalcache():
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    totalsql='select count(*) from film'
    curr.execute(totalsql)
    totalcounts=curr.fetchall()
    total=int(totalcounts[0]['count(*)'])
    curr.close()
    conn.close()
    return total

@cache.cached(60*10,key_prefix="weekhot_cache")
def weekhotcache():
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    weekhotsql=' SELECT * FROM film WHERE last_seen>%s order by requests desc limit 200'
    curr.execute(weekhotsql,thisweek)
    weekhot=curr.fetchall()
    curr.close()
    conn.close()
    return weekhot

@cache.cached(60*10,key_prefix="dayhot_cache")
def dayhotcache():
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    dayhotsql=' SELECT * FROM film WHERE last_seen>%s order by requests desc limit 200'
    curr.execute(dayhotsql,yesterday)
    dayhot=curr.fetchall()
    curr.close()
    conn.close()
    return dayhot

@cache.cached(60*10,key_prefix="newest_cache")
def newestcache():
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    newsql=' SELECT * FROM film WHERE create_time>%s  order by create_time desc limit 200'
    curr.execute(newsql,yesterday)
    newest=curr.fetchall()
    curr.close()
    conn.close()
    return newest

#@cache.cached(60*60,key_prefix="keywords_cache")
#def keywordscache():
#    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
#    curr = conn.cursor()
#    keywordsquerysql='SELECT * FROM keywords order by id desc  LIMIT 300'
#    curr.execute(keywordsquerysql)
#    keywords=curr.fetchall()
#    curr.close()
#    conn.close()
#    return keywords
#
#@cache.cached(60*60,key_prefix="actors_cache")
#def actorscache():
#    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
#    curr = conn.cursor()
#    actorsquerysql='SELECT * FROM actors order by id desc  LIMIT 300'
#    curr.execute(actorsquerysql)
#    actors=curr.fetchall()
#    curr.close()
#    conn.close()
#    return actors
#
#def tagscache():
#    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
#    curr = conn.cursor()
#    tagssql=' SELECT * FROM tags order by id desc limit 300'
#    curr.execute(tagssql)
#    tags=curr.fetchall()
#    curr.close()
#    conn.close()
#    return tags




@app.route('/',methods=['GET','POST'])
def index():
    total=totalcache()
    tags=Search_Tags.query.order_by(Search_Tags.id.desc()).limit(300)
    keywords=Search_Keywords.query.order_by(Search_Keywords.id.desc()).limit(300)
    dayhot=dayhotcache()
    weekhot=weekhotcache()
    newest=newestcache()
    form=SearchForm()
    query = db.session.query(Search_Actors)
    rowCount = int(query.count())
    randomRow = query.offset(int(rowCount*random.random())).limit(40)
    #todaysql='select sum(new_hashes) from search_statusreport where to_days(search_statusreport.date)= to_days(now())'
    today=db.session.query(func.sum(Search_Statusreport.new_hashes)).filter(cast(Search_Statusreport.date,Date) == datetime.date.today()).scalar()
    return render_template('index.html',form=form,today=today,total=total,tags=tags,keywords=keywords,actors=randomRow,dayhot=dayhot,weekhot=weekhot,newest=newest,sitename=sitename)


@app.route('/fanhao-<int:page>.html',methods=['GET','POST'])
#@cache.cached(timeout=60*60,key_prefix=make_cache_key)
def fanhao(page=1):
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_MYSQL,user=DB_USER,password=DB_PASS,db=DB_NAME_MYSQL,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    tags=Search_Tags.query.order_by(Search_Tags.id.desc()).limit(300)
    actors=Search_Actors.query.order_by(Search_Actors.id.desc()).limit(300)
    keywordsquerysql='SELECT * FROM search_keywords order by id desc limit %s,300'
    curr.execute(keywordsquerysql,(page-1)*300)
    keywords=curr.fetchall()
    countsql='SELECT count(id) FROM search_keywords'
    curr.execute(countsql)
    resultcounts=curr.fetchall()
    counts=int(resultcounts[0]['count(id)'])
    curr.close()
    conn.close()
    pages=(counts+299)/300
    form=SearchForm()
    return render_template('fanhao.html',form=form,keywords=keywords,actors=actors,tags=tags,page=page,pages=pages,sitename=sitename)


@app.route('/nvyou-<int:page>.html',methods=['GET','POST'])
#@cache.cached(timeout=60*60,key_prefix=make_cache_key)
def nvyou(page=1):
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_MYSQL,user=DB_USER,password=DB_PASS,db=DB_NAME_MYSQL,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    tags=Search_Tags.query.order_by(Search_Tags.id.desc()).limit(300)
    keywords=Search_Keywords.query.order_by(Search_Keywords.id.desc()).limit(300)
    actorsquerysql='SELECT * FROM search_actors order by id desc limit %s,300'
    curr.execute(actorsquerysql,(page-1)*300)
    actors=curr.fetchall()
    countsql='SELECT count(id) FROM search_actors'
    curr.execute(countsql)
    resultcounts=curr.fetchall()
    counts=int(resultcounts[0]['count(id)'])
    curr.close()
    conn.close()
    pages=(counts+299)/300
    form=SearchForm()
    return render_template('nvyou.html',form=form,keywords=keywords,actors=actors,tags=tags,page=page,pages=pages,sitename=sitename)


@app.route('/tag-<int:page>.html',methods=['GET','POST'])
#@cache.cached(timeout=60*60,key_prefix=make_cache_key)
def tag(page=1):
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_MYSQL,user=DB_USER,password=DB_PASS,db=DB_NAME_MYSQL,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    keywords=Search_Keywords.query.order_by(Search_Keywords.id.desc()).limit(300)
    actors=Search_Actors.query.order_by(Search_Actors.id.desc()).limit(300)
    tagssql='SELECT * FROM search_tags order by id desc limit %s,300'
    curr.execute(tagssql,(page-1)*300)
    tags=curr.fetchall()
    countsql='SELECT count(id) FROM search_tags'
    curr.execute(countsql)
    resultcounts=curr.fetchall()
    counts=int(resultcounts[0]['count(id)'])
    curr.close()
    conn.close()
    pages=(counts+299)/300
    form=SearchForm()
    return render_template('tag.html',form=form,keywords=keywords,actors=actors,tags=tags,page=page,pages=pages,sitename=sitename)


@app.route('/weekhot.html',methods=['GET','POST'])
#@cache.cached(timeout=60*10,key_prefix=make_cache_key)
def weekhot():
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    weekhotsql='SELECT * FROM film WHERE last_seen>%s order by requests desc OPTION max_matches=200'
    curr.execute(weekhotsql,thisweek)
    weekhot=curr.fetchall()
    tags=Search_Tags.query.order_by(Search_Tags.id.desc()).limit(300)
    curr.close()
    conn.close()
    form=SearchForm()
    return render_template('weekhot.html',form=form,weekhot=weekhot,tags=tags,sitename=sitename)


@app.route('/dayhot.html',methods=['GET','POST'])
#@cache.cached(timeout=60*10,key_prefix=make_cache_key)
def dayhot():
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    dayhotsql='SELECT * FROM film WHERE last_seen>%s  order by requests desc  OPTION max_matches=200'
    curr.execute(dayhotsql,yesterday)
    dayhot=curr.fetchall()
    tags=Search_Tags.query.order_by(Search_Tags.id.desc()).limit(300)
    curr.close()
    conn.close()
    form=SearchForm()
    return render_template('dayhot.html',form=form,dayhot=dayhot,tags=tags,sitename=sitename)


@app.route('/new.html',methods=['GET','POST'])
#@cache.cached(timeout=60*60,key_prefix=make_cache_key)
def new():
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    newestsql='SELECT * FROM film WHERE create_time>%s  order by create_time desc  OPTION max_matches=200'
    curr.execute(newestsql,yesterday)
    newest=curr.fetchall()
    tags=Search_Tags.query.order_by(Search_Tags.id.desc()).limit(300)
    curr.close()
    conn.close()
    form=SearchForm()
    return render_template('new.html',form=form,newest=newest,tags=tags,sitename=sitename)


@app.route('/search-<query>-<int:category>-<int:order>-<int:page>.html',methods=['GET','POST'])
#@cache.cached(timeout=60*60,key_prefix=make_cache_key)
def search_results(query,category,order,page=1):
    connzsky = pymysql.connect(host=DB_HOST,port=DB_PORT_MYSQL,user=DB_USER,password=DB_PASS,db=DB_NAME_MYSQL,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    currzsky = connzsky.cursor()
    taginsertsql = 'REPLACE INTO search_tags(tag) VALUES(%s)'
    currzsky.execute(taginsertsql,query)
    connzsky.commit()
    currzsky.close()
    connzsky.close()
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    sqlpre=' SELECT * FROM film WHERE match(%s) '
    sqlend=' limit %s,20 OPTION max_matches=20000 '
    querysql=sqlpre + categoryquery[category] + sorts[order] +sqlend
    curr.execute(querysql,(query,(page-1)*20))
    queryresult=curr.fetchall()
    countsql='SHOW META'
    curr.execute(countsql)
    resultcounts=curr.fetchall()
    counts=int(resultcounts[0]['Value'])
    taketime=float(resultcounts[2]['Value'])
    actors=Search_Actors.query.order_by(Search_Actors.id.desc()).limit(300)
    tags=Search_Tags.query.order_by(Search_Tags.id.desc()).limit(300)
    curr.close()
    conn.close()
    pages=(counts+19)/20
    form=SearchForm()
    form.search.data=query
    return render_template('list.html',form=form,query=query,pages=pages,page=page,actors=actors,category=category,order=order,hashs=queryresult,counts=counts,taketime=taketime,tags=tags,sitename=sitename)


@app.route('/search',methods=['GET','POST'])
def search():
    form=SearchForm()
    query=re.sub(r"(['`=\(\)|\-!@~\"&/\\\^\$])", r"\\\1", form.search.data)
    if not form.search.data:
        return redirect(url_for('index'))
    return redirect(url_for('search_results',query=query,category=0,order=0,page=1))


@app.route('/hash/<info_hash>.html',methods=['GET','POST'])
#@cache.cached(timeout=60*60,key_prefix=make_cache_key)
def detail(info_hash):
    form=SearchForm()
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    detailsql='SELECT * FROM film WHERE info_hash=%s'
    curr.execute(detailsql,info_hash)
    hash=curr.fetchone()
    tags=Search_Tags.query.order_by(Search_Tags.id.desc()).limit(300)
    keywords=Search_Keywords.query.order_by(Search_Keywords.id.desc()).limit(300)
    actors=Search_Actors.query.order_by(Search_Actors.id.desc()).limit(300)
    dayhot=dayhotcache()
    weekhot=weekhotcache()
    newest=newestcache()
    curr.close()
    conn.close()
    if not hash:
        return redirect(url_for('index'))
    if Complaint.query.filter_by(info_hash=info_hash).first():
        return render_template('complaintdetail.html',form=form,tags=tags,hash=hash,keywords=keywords,actors=actors,dayhot=dayhot,weekhot=weekhot,newest=newest,sitename=sitename) 
    return render_template('detail.html',form=form,tags=tags,hash=hash,keywords=keywords,actors=actors,dayhot=dayhot,weekhot=weekhot,newest=newest,sitename=sitename)

@app.route('/download/<info_hash>',methods=['GET','POST'])
def download(info_hash):
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    querysql='SELECT * FROM film WHERE info_hash=%s'
    curr.execute(querysql,info_hash)
    hash=curr.fetchone()
    curr.close()
    conn.close()
    if not hash:
        return redirect(url_for('index'))
    if Complaint.query.filter_by(info_hash=info_hash).first():
        return render_template('complaintdetail.html',form=form,tags=tags,hash=hash,keywords=keywords,actors=actors,dayhot=dayhot,weekhot=weekhot,newest=newest,sitename=sitename) 
    return render_template('download.html',hash=hash,sitename=sitename)

@app.route('/sitemap.xml')
def sitemap():    
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    querysql='SELECT info_hash,create_time FROM film order by create_time desc limit 200'
    curr.execute(querysql)
    rows=curr.fetchall()
    curr.close()
    conn.close()
    sitemaplist=[]
    for row in rows:
        info_hash = row['info_hash']
        mtime = datetime.datetime.fromtimestamp(int(row['create_time'])).strftime('%Y-%m-%d')
        url = request.url_root+'hash/{}.html'.format(info_hash)
        url_xml = '<url><loc>{}</loc><lastmod>{}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>'.format(url, mtime)
        sitemaplist.append(url_xml)
    xml_content = '<?xml version="1.0" encoding="UTF-8"?><urlset>{}</urlset>'.format("".join(x for x in sitemaplist))
    with open('static/sitemap.xml', 'wb') as f:
        f.write(xml_content)
        f.close()
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/dmca/<info_hash>',methods=['GET','POST'])
def dmca(info_hash):
    if Complaint.query.filter_by(info_hash=info_hash).first():
        return redirect(url_for('index'))
    form=ComplaintForm()
    conn = pymysql.connect(host=DB_HOST,port=DB_PORT_SPHINX,user=DB_USER,password=DB_PASS,db=DB_NAME_SPHINX,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
    curr = conn.cursor()
    querysql='SELECT * FROM film WHERE info_hash=%s'
    curr.execute(querysql,info_hash)
    thishash=curr.fetchone()
    form.info_hash.data=info_hash
    if form.validate_on_submit():
        hash=form.info_hash.data
        reason=form.reason.data
        create_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        newcomplaint=Complaint(info_hash=hash,reason=reason,create_time=create_time)
        db.session.add(newcomplaint)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('dmca.html',form=form,thishash=thishash,sitename=sitename)

@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/uploads/nvyou/<filename>')
def nvyoupics(filename):
    return send_from_directory(nvyoupath, filename)

@app.route('/uploads/fanhao/<filename>')
def fanhaopics(filename):
    return send_from_directory(fanhaopath, filename)

@app.errorhandler(404)
def notfound(e):
    return render_template("404.html"),404


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login_view'))
        connzsky = pymysql.connect(host=DB_HOST,port=DB_PORT_MYSQL,user=DB_USER,password=DB_PASS,db=DB_NAME_MYSQL,charset=DB_CHARSET,cursorclass=pymysql.cursors.DictCursor)
        currzsky = connzsky.cursor()
        totalsql = 'select count(id) from search_hash'
        currzsky.execute(totalsql)
        totalcounts=currzsky.fetchall()
        total=int(totalcounts[0]['count(id)'])
        todaysql='select count(id) from search_hash where to_days(search_hash.create_time)= to_days(now())'
        currzsky.execute(todaysql)
        todaycounts=currzsky.fetchall()
        today=int(todaycounts[0]['count(id)'])
        currzsky.close()
        connzsky.close()
        logfile=os.path.join(os.path.dirname(__file__),'spider.log')
        if os.path.exists(logfile):
            body = codecs.open(logfile, 'r' ,encoding='utf-8', errors='ignore').readlines()[-20:]
        else:
            os.mknod(logfile)
            body = codecs.open(logfile, 'r',encoding='utf-8' , errors='ignore').readlines()[-20:]
        htmlbody = '\n'.join('<p>%s</p>' % line for line in body)
        return self.render('admin/index.html',total=total,today=today,htmlbody=htmlbody)
    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            if user is None:
                flash('用户名错误！')
            elif not check_password_hash(user.password, form.password.data):
                flash('密码错误！')
            elif user is not None and check_password_hash(user.password, form.password.data):
                login_user(user)
        if current_user.is_authenticated:
            return redirect(url_for('admin.index'))
        self._template_args['form'] = form
        #self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()
    @expose('/logout/')
    def logout_view(self):
        logout_user()
        return redirect(url_for('admin.index'))

    
class HashView(ModelView):
    create_modal = True
    edit_modal = True
    can_export = True
    column_searchable_list = ['name']
    def get_list(self, *args, **kwargs):
        count, data = super(HashView, self).get_list(*args, **kwargs)
        count=10000
        return count,data
    def is_accessible(self):
        if current_user.is_authenticated :
            return True
        return False
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))


class TagsView(ModelView):
    create_modal = True
    edit_modal = True
    can_export = True
    column_searchable_list = ['tag']
    def is_accessible(self):
        if current_user.is_authenticated :
            return True
        return False
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))


class KeywordsView(ModelView):
    create_modal = True
    edit_modal = True
    can_export = True
    def is_accessible(self):
        if current_user.is_authenticated :
            return True
        return False
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))

class UserView(ModelView):
    #column_exclude_list = 'password'
    create_modal = True
    edit_modal = True
    can_export = True
    def is_accessible(self):
        if current_user.is_authenticated :
            return True
        return False
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))

class NvyouFile(FileAdmin):
    def is_accessible(self):
        if current_user.is_authenticated :
            return True
        return False
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))

class FanhaoFile(FileAdmin):
    def is_accessible(self):
        if current_user.is_authenticated :
            return True
        return False
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.login_view'))

admin = Admin(app,name='管理中心',base_template='admin/my_master.html',index_view=MyAdminIndexView(name='首页',template='admin/index.html',url='/admin'))
admin.add_view(HashView(Search_Hash, db.session,name='磁力Hash'))
admin.add_view(KeywordsView(Search_Keywords, db.session,name='热门番号',category='番号'))
admin.add_view(FanhaoFile(fanhaopath, '/uploads/fanhao', name='番号图片',category='番号'))
admin.add_view(KeywordsView(Search_Actors, db.session,name='女优大全',category='女优'))
admin.add_view(NvyouFile(nvyoupath, '/uploads/nvyou', name='女优图片',category='女优'))
admin.add_view(TagsView(Search_Tags, db.session,name='搜索记录'))
admin.add_view(UserView(Complaint, db.session,name='投诉记录'))
admin.add_view(UserView(Search_Statusreport, db.session,name='爬取统计'))
admin.add_view(UserView(User, db.session,name='用户管理'))


@manager.command
def init_db():
    db.create_all()
    db.session.commit()


@manager.option('-u', '--name', dest='name')
@manager.option('-e', '--email', dest='email')
@manager.option('-p', '--password', dest='password')
def create_user(name,password,email):
    if name is None:
        name = raw_input('输入用户名(默认admin):') or 'admin'
    if password is None:
        password = generate_password_hash(getpass('密码:'))
    if email is None:
        email=raw_input('Email地址:')
    user = User(name=name,password=password,email=email)
    db.session.add(user)
    db.session.commit()
    print u"管理员创建成功!"

@manager.option('-np', '--newpassword', dest='newpassword')
def changepassword(newpassword):
    name = raw_input(u'输入用户名:')
    thisuser = User.query.filter_by(name=name).first()
    if not thisuser:
        print u"用户不存在,请重新输入用户名!"
        name = raw_input(u'输入用户名:')    
        thisuser = User.query.filter_by(name=name).first()
    if newpassword is None:
        newpassword = generate_password_hash(getpass(u'新密码:'))
    thisuser.password=newpassword
    db.session.add(thisuser)
    db.session.commit()
    print u"密码已更新,请牢记新密码!"

if __name__ == '__main__':
    manager.run()
