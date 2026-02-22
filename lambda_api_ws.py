import json
import boto3
import datetime
import secrets
import random

dynamodb = boto3.resource('dynamodb')
table_estado = dynamodb.Table('ChatApiConnections')
table_historico = dynamodb.Table('ChatHistory')

def handle_connect(event, connection_id):
    #Gera um nome aleatório para o teste
    username = f"User_{random.randint(100,999)}"
    params = event.get('queryStringParameters', {})
    id_caso = params.get('id', 'GERAL')
    
    table_estado.put_item(Item={
        'connection_id': connection_id,
        'id': id_caso,
        'username': username,
        'timestamp': datetime.datetime.utcnow().isoformat()
    })
    return {"statusCode": 200}



def handle_disconnect(connection_id):
    table_estado.delete_item(Key={'connection_id': connection_id})
    return {"statusCode": 200}

def handle_send_message(event, connection_id, body):
    id_caso = body.get('id_caso')
    conteudo = body.get('message')
    
    # Gerando SK Única e Ordenável (Timestamp + Sufixo Aleatório)
    now = datetime.datetime.utcnow().isoformat()
    suffix = secrets.token_hex(3)
    sk = f"MSG#{now}#{suffix}"
    
    # Salva no Histórico (O Stream fará o Broadcast depois!)
    table_historico.put_item(Item={
        'id': f"CASO#{id_caso}",
        'sort_key': sk,
        'message': conteudo,
        'sender_connection': connection_id
    })
    return {"statusCode": 200}

def lambda_handler(event, context):
    route = event['requestContext']['routeKey']
    conn_id = event['requestContext']['connectionId']
    body = json.loads(event.get('body', '{}'))
    print(event)
    if route == '$connect':
        return handle_connect(event, conn_id)
    elif route == '$disconnect':
        return handle_disconnect(conn_id)
    elif route == 'sendMessage':
        return handle_send_message(event, conn_id, body)
    else:
        return {"statusCode": 404, "body": "Rota não encontrada."}