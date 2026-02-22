import boto3
import json
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table_estado = dynamodb.Table('ChatApiConnections')
# Importante: O endpoint deve ser o 'Connection URL' do seu API Gateway
gateway = boto3.client('apigatewaymanagementapi', endpoint_url="https://idapi.execute-api.region.amazonaws.com/stage/")

def lambda_handler(event, context):
    for record in event['Records']:
        # Processa apenas inserções de novas mensagens
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            
            # Extraindo dados da mensagem (formato DynamoDB JSON)
            id_caso = new_image['id']['S'].replace('CASO#', '')
            conteudo = new_image['message']['S']
            
            # 1. Buscar conexões ativas via GSI
            # Substitua 'id_content' pelo nome que você deu ao seu GSI
            resposta = table_estado.query(
                IndexName='id_content',
                KeyConditionExpression=Key('id').eq(id_caso)
            )
            
            # 2. Criar o payload para o Front-end
            payload = json.dumps({
                "type": "NEW_MESSAGE",
                "data": {
                    "text": conteudo,
                    "timestamp": new_image['sort_key']['S']
                }
            })

            # 3. Enviar para todos os usuários do caso
            for item in resposta['Items']:
                conn_id = item['connection_id']
                try:
                    gateway.post_to_connection(
                        ConnectionId=conn_id,
                        Data=payload
                    )
                except gateway.exceptions.GoneException:
                    # Limpeza automática: se o usuário caiu e o socket não avisou
                    table_estado.delete_item(Key={'connection_id': conn_id})