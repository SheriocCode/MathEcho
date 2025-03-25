from flask import jsonify

def success_response(data, code=200, msg="success"):
    """
    生成成功的响应对象  
    :param data: 返回的数据  
    :param code: HTTP状态码，默认为200  
    :param msg: 成功消息，默认为"success"  
    :return: JSON响应
    """
    response = {
        "code": code,
        "msg": msg,
        "res_data": data
    }
    return jsonify(response)

def error_response(msg, code=500):
    """
    生成错误的响应对象
    :param msg: 错误消息
    :param code: HTTP状态码，默认为500
    :param data: 可选的错误数据
    :return: JSON响应
    """
    response = {
        "code": code,
        "msg": msg,
    }
    return jsonify(response)