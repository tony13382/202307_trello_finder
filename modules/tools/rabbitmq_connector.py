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
connection = pika.BlockingConnection(parameters)
channel = connection.channel()


def send_img_queue(data):
    #  建立隊列
    channel.queue_declare(queue='img_queue')

    # 将Dict数据转换为JSON字符串
    #data_json = json.dumps({
    #    'mode' : 'sendPic', / "sendCover"
    #    'card_id' : "64e3081f66b89ea448eb7da6",
    #    'img_path' : 'static/images/wordCloud/0_wordcloud.png'
    #})

    data_json = json.dumps(data)

    # 发送消息
    channel.basic_publish(exchange='', routing_key='img_queue', body=data_json)

    print(" [x] Sent data: %s" % data_json)

    #  6. 釋放資源，關閉連結
    # connection.close()