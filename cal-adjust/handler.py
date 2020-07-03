import datetime
import json
import pymysql
from DBUtils.PooledDB import PooledDB
import time
import requests
import sys

POOL = PooledDB(
    creator=pymysql,  # 使用链接数据库的模块
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

def produce():
    conn = POOL.connection()

    sql1 = "select * from input_pool order by RAND() LIMIT 1"

    cursor = conn.cursor()
    cursor.execute(sql1)  # 从数据池中随机读取数据
    data = cursor.fetchone()
    # print(data)

    sql2 = """
    insert into input(produce_date, o_rate, per_index, co, o_flow, max_pressure)
    values (%s, %s, %s, %s, %s, %s)
    """
    
    # 将时间改为当前时间存入数据库中的input表
    values = (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data[2], data[3], data[4], data[5], data[6])
    cursor.execute(sql2, values)
    conn.commit()
    cursor.close()
    return

def get_prediction():
    conn = POOL.connection()

    sql1 = "select * from input order by produce_date desc LIMIT 1"
    cursor1 = conn.cursor()
    cursor1.execute(sql1)  # 数据读取-get_prediction
    row1 = cursor1.fetchone()
    cursor1.close()

    data = {"fyl": row1[2], "tqx": row1[3], "co": row1[4], "fyll": row1[5], "dy": row1[6]}

    # inner-cluster address
    url = 'http://gateway.openfaas:8080/function/lin-regress'
    # external address
    # url = 'http://172.16.22.177:31112/function/lin-regress'
    sys.stderr.write("invoke linear regression function\n")
    r = requests.post(url, None, data)
    rjs = r.json()
    sys.stderr.write("json result:" + str(rjs))

    return rjs["prediction"]


def cal_adjust(prediction, reference=0.4):  # 设定值： 从图形界面读取设定好的reference：硅含量
    p = -100  # p的值人为设定
    e = prediction - reference  # 偏差值
    # -----------------------------------------
    # 输出：
    y = round(p * e, 2)  # 推荐的操作参数变化
    predict_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    sql = "insert into output values (%s, %s)"
    values = (predict_date, y)

    conn = POOL.connection()
    cursor1 = conn.cursor()
    cursor1.execute(sql, values)  # 数据库插入推荐的操作参数变化

    conn.commit()
    return y

def handle(req):
    res = {}
    datas = []
    real = 0.4
    if req:
        req_json = json.loads(req)
        real = req_json["real"]
    # print("硅含量目标设定：", real)
    else:
        produce()
        time.sleep(0.1)

    prediction = get_prediction()  # 计算预测值
    # print("预测值：", prediction)
    result = cal_adjust(prediction, real)  # 计算调整量并写入数据库
    # print("推荐调整量：", result)

    data = {}
    data["prediction"] = prediction
    data["adjustment"] = result
    datas.append(data)

    res['data'] = datas
    res['success'] = True
    return json.dumps(res)

if __name__ == '__main__':
    handle("")