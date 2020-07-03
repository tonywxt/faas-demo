import datetime
import json
import pymysql
from DBUtils.PooledDB import PooledDB

POOL = PooledDB(
    creator=pymysql,   # 使用链接数据库的模块
    maxconnections=6,  # 连接池允许的最大连接数，0和None表示不限制连接数
    mincached=2,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
    maxcached=5,  # 链接池中最多闲置的链接，0和None不限制
    maxshared=3,
    # 链接池中最多共享的链接数量，0和None表示全部共享。PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，所有值无论设置为多少，_maxcached永远为0，所以永远是所有链接都共享。
    blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
    maxusage=None,  # 一个链接最多被重复使用的次数，None表示无限制
    setsession=[],  # 开始会话前执行的命令列表。如：["set datestyle to ...", "set time zone ..."]
    ping=0,
    # ping MySQL服务端，检查是否服务可用，如：0 = None = never, 1 = default = whenever it is requested, 2 = when a cursor is created, 4 = when a query is executed, 7 = always
    host="172.16.22.136",
    port=30006,
    user="root",
    password="123456",
    database="si_predict_faas"
)

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)

def handle(req):
    res = {}
    sql = "select * from input order by produce_date desc LIMIT 100"

    conn = POOL.connection()
    cursor1 = conn.cursor()
    cursor1.execute(sql)   # 查询历史数据
    rows = cursor1.fetchall()
    datas = []
    indexs = ("id","produce_date","o_rate","per_index","co","o_flow","max_pressure")
    for row in reversed(rows):
        data = dict(zip(indexs, row))
        datas.append(data)

    res['data'] = datas
    res['success'] = True
    return json.dumps(res, cls=DateEncoder)
