# -*- coding: utf-8 -*-
####################################################################
## 環境變數
####################################################################
import yaml
with open('config.yml', 'r', encoding='utf-8') as config_File:
    config = yaml.safe_load(config_File)
RABBITMA_HOST = config['rabbitMQ']['host']
RABBITMQ_PORT = config['rabbitMQ']['port']
print(f'HOST ON:{RABBITMA_HOST}:{RABBITMQ_PORT}')

RABBITMQ_USERNAME = config['rabbitMQ']['username']
RABBITMQ_PASSSWORD = config['rabbitMQ']['password']
RABBITMQ_SEARCH_QUEUE = config['rabbitMQ']['search_queue']
RABBITMQ_COMMENT_QUEUE = config['rabbitMQ']['comment_queue']
print(f'ACC:{RABBITMQ_USERNAME} | PASS: {RABBITMQ_PASSSWORD}')

####################################################################


####################################################################
## Import RabbitMQ Module ＆ Set Connection
####################################################################
import pika
import json
# 连接到RabbitMQ服务器
credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSSWORD)
parameters = pika.ConnectionParameters(RABBITMA_HOST, RABBITMQ_PORT, '/', credentials)
####################################################################


####################################################################
## 發送任務至 RabbitMQ (Trello Search)
####################################################################
def send_trello_mission(data):
    # 建立連結
    connection = pika.BlockingConnection(parameters)
    #  建立隊列
    channel = connection.channel()
    channel.queue_declare(queue = RABBITMQ_SEARCH_QUEUE)
    
    # 取得資料
    card_id = data.get('card_id', '')
    input_string = data.get('input_string', '')
    trello_req = data.get('trello_req', {})
    # 確認資料是否完整
    if(card_id == '' or input_string == ''):
        return {
            "state" : False,
            "err_msg" : "card_id or input_string is empty. \n - car_id:" + card_id + "\n - input_string:" + input_string,
        }
    # 轉換成 JSON 格式 (這樣才能在 RabbitMQ 中傳遞)
    data_json = json.dumps({
        'card_id' : card_id,
        'input_string' : input_string,
        'trello_req' : trello_req,
    })

    # 发送消息
    channel.basic_publish(exchange='', routing_key = RABBITMQ_SEARCH_QUEUE, body=data_json)
    print(f" [x] Sent data: {card_id} | {input_string}. ")
    # 釋放資源，關閉連結
    connection.close()
    # 回傳成功
    return {
        "state" : True,
        "value" : " [x] Sent data: " + card_id + " | " + input_string,
    }
####################################################################


####################################################################
## 發送交流至 RabbitMQ (Trello Comment)
####################################################################
def send_trello_discuess(data):
    # 建立連結
    connection = pika.BlockingConnection(parameters)
    #  建立隊列
    channel = connection.channel()
    channel.queue_declare(queue = RABBITMQ_COMMENT_QUEUE)
    
    # 取得資料
    card_id = data.get('card_id', '')
    input_string = data.get('input_string', '')
    trello_req = data.get('trello_req', {})
    # 確認資料是否完整
    if(card_id == '' or input_string == ''):
        return {
            "state" : False,
            "err_msg" : "card_id or input_string is empty. \n - car_id:" + card_id + "\n - input_string:" + input_string,
        }
    # 轉換成 JSON 格式 (這樣才能在 RabbitMQ 中傳遞)
    data_json = json.dumps({
        'card_id' : card_id,
        'input_string' : input_string,
        'trello_req' : trello_req,
    })

    # 发送消息
    channel.basic_publish(exchange='', routing_key = RABBITMQ_COMMENT_QUEUE, body=data_json)
    print(f" [x] Sent data: {card_id} | {input_string}. ")
    # 釋放資源，關閉連結
    connection.close()
    # 回傳成功
    return {
        "state" : True,
        "value" : " [x] Sent data: " + card_id + " | " + input_string,
    }
####################################################################
