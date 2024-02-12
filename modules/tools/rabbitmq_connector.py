# -*- coding: utf-8 -*-
####################################################################
# 環境變數
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)
RABBITMA_HOST = config['rabbitMQ']['host']
RABBITMQ_PORT = config['rabbitMQ']['port']
print(f'HOST ON:{RABBITMA_HOST}:{RABBITMQ_PORT}')

RABBITMQ_USERNAME = config['rabbitMQ']['username']
RABBITMQ_PASSSWORD = config['rabbitMQ']['password']
print(f'ACC:{RABBITMQ_USERNAME} | PASS: {RABBITMQ_PASSSWORD}')

####################################################################


####################################################################
# Import RabbitMQ Module ＆ Set Connection
####################################################################
import pika
import json
# 连接到RabbitMQ服务器
credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSSWORD)
parameters = pika.ConnectionParameters(RABBITMA_HOST, RABBITMQ_PORT, '/', credentials)
####################################################################


def send_trello_mission(data, coreNum=1):
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    #  建立隊列
    if(coreNum == 1):
        channel.queue_declare(queue='trello_mission')
    else:
        channel.queue_declare(queue=f'trello_mission{coreNum}', durable=True)

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
    if(coreNum == 1):
        channel.basic_publish(exchange='', routing_key='trello_mission', body=data_json)
    else:
        channel.basic_publish(exchange='', routing_key=f'trello_mission{coreNum}', body=data_json)

    print(f" [x] Sent data: {card_id} | {input_string}. ")

    # 釋放資源，關閉連結
    connection.close()

    return {
        "state" : True,
        "value" : " [x] Sent data: " + card_id + " | " + input_string,
    }