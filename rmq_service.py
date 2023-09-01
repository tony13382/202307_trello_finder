# -*- coding: utf-8 -*-
from modules.tools.trello_connector import addCoverToCard, addFileToCard

import pika
import json

def callback(ch, method, properties, body):
    # 将收到的JSON字符串转换为Dict数据
    print(body)
    print('------------------')
    data_dict = json.loads(body)
    print(" [x] Received data: %s" % data_dict)
    
    if data_dict['mode'] == 'sendPic':
        try:
            addFileToCard(data_dict['card_id'],data_dict['img_path'])
        except:
            print('Error')
    elif data_dict['mode'] == 'sendCover':
        try:
            addCoverToCard(data_dict['card_id'],data_dict['img_path'])
        except:
            print('Error')
    

# 连接到RabbitMQ服务器
credentials = pika.PlainCredentials('user', '0619rab')
parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# 声明一个队列
channel.queue_declare(queue='img_queue')

# 设置消息回调函数
channel.basic_consume(queue='img_queue', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
