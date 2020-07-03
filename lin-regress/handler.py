import json

def handle(req):
    data = json.loads(req)

    parameter_1 = 0.00003  # 富氧率对应参数
    parameter_2 = 0.0004  # 透气性指数对应参数
    parameter_3 = 0.0005  # co含量对应参数
    parameter_4 = 0.000027  # 富氧流量含量对应参数
    parameter_5 = 0.000007  # 顶压含量对应参数
    prediction = float(data['fyl']) * parameter_1 + float(data['tqx']) * parameter_2 + float(
        data['co']) * parameter_3 + float(data['fyll']) * parameter_4 + float(data['dy']) * parameter_5
    prediction = round(prediction, 2)

    return json.dumps({ "prediction": prediction })
