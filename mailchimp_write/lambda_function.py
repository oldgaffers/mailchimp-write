import json
import os
import boto3
from sync import get_client, getlistid, crud, archive

ssm = boto3.client('ssm')

def update_mailchimp(action, record):
  # print('update_mailchimp', action, record)
  excludes = {}
  if 'EXCLUDE' in os.environ:
    excludes = json.loads(os.environ.get('EXCLUDE'))
  r = ssm.get_parameter(Name='/MAILCHIMP/API_KEY', WithDecryption=True)
  apiKey = r['Parameter']['Value']
  r = ssm.get_parameter(Name='/MAILCHIMP/SERVER')
  server = r['Parameter']['Value']
  r = ssm.get_parameter(Name='/MAILCHIMP/AUDIENCE')
  audience = r['Parameter']['Value']
  client = get_client()
  client.set_config({
   "api_key": apiKey,
   "server": server,
  })
  list = getlistid(audience)
  if action == 'added':
    # print('add', record)
    crud(list, record)
  elif action == 'changed':
    # print('change', record)
    crud(list, record['after'])
  elif action == 'deleted':
    # print('delete', record)
    archive(list, record)
  else:
    print(action, json.dumps(record))

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

def topic_handler(event, context):
  # print('topic handler')
  for record in event['Records']:
    message = json.loads(record['Sns']['Message'])
    detailType = message['DetailType']
    detail = json.loads(message['Detail'])
    update_mailchimp(detailType, detail)

def lambda_handler(event, context):
  # print(json.dumps(event))
  if 'Records' in event:
    return topic_handler(event, context)
  return eventbus_handler(event, context)
