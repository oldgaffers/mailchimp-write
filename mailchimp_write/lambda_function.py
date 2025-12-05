import json
from mailchimp_write.mailchimp import update_mailchimp

def eventbus_handler(event, context):
  if 'x-api-key' not in event['headers']:
    return {
      'statusCode': 403,
      'body': json.dumps('missing api key')
    }
  if event['headers']['x-api-key'] != 'xyz':
    return {
      'statusCode': 403,
      'body': json.dumps('bad api key')
    }
  body = json.loads(event['body'])
  update_mailchimp(body['detail-type'], body['detail'])
  return {
      'statusCode': 200,
      'body': json.dumps('Hello from Lambda!')
  }

def record_handler(record):
  if 'Sns' in record:
    message = json.loads(record['Sns']['Message'])
    detailType = message['DetailType']
    detail = json.loads(message['Detail'])
    update_mailchimp(detailType, detail)
  elif 'body' in record:
    message = json.loads(record['body'])
    detailType = message['DetailType']
    detail = json.loads(message['Detail'])
    update_mailchimp(detailType, detail)
  else:
    print(record)

def lambda_handler(event, context):
  # print(json.dumps(event))
  if 'Records' in event:
    for record in event['Records']:
      record_handler(record)
    return {
      'statusCode': 200,
      'body': json.dumps('Hello from Lambda!')
    } 
  return eventbus_handler(event, context)
