# -*- coding: utf-8 -*-
import pika
import json

import os
from dotenv import load_dotenv
load_dotenv()
rabbitmq_host = os.getenv("rabbitmq_host")
rabbitmq_port = os.getenv("rabbitmq_port")
rabbitmq_username = os.getenv("rabbitmq_username")
rabbitmq_password = os.getenv("rabbitmq_password")

# 连接到RabbitMQ服务器
credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
parameters = pika.ConnectionParameters(rabbitmq_host, rabbitmq_port, '/', credentials)


def send_trello_mission(data):
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    #  建立隊列
    channel.queue_declare(queue='trello_mission')

    card_id = data.get('card_id', '')
    input_string = data.get('input_string', '')
    trello_req = data.get('trello_req', {})
    
    if(card_id == '' or input_string == ''):
        return {
            "state" : False,
            "err_msg" : "card_id or input_string is empty. \n - car_id:" + card_id + "\n - input_string:" + input_string,
        }
    
    # 将Dict数据转换为JSON字符串
    data_json = json.dumps({
        'card_id' : card_id,
        'input_string' : input_string,
        'trello_req' : trello_req,
    })

    # 发送消息
    channel.basic_publish(exchange='', routing_key='trello_mission', body=data_json)

    print(f" [x] Sent data: {card_id} | {input_string}. ")

    # 釋放資源，關閉連結
    connection.close()

    return {
        "state" : True,
        "value" : " [x] Sent data: " + card_id + " | " + input_string,
    }