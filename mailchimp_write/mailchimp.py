import json
import os
import boto3
from sync import get_client, getlistid, crud, archive, audit

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
  list = getlistid(client, audience)
  if action == 'added':
    # print('add', record)
    crud(client, list, record)
  elif action == 'changed':
    # print('change', record)
    crud(client, list, record['after'])
  elif action == 'deleted':
    # print('delete', record)
    archive(client, list, record)
  elif action == 'audit':
    # print('audit', record)
    audit(client, list, record)
  else:
    print(action, json.dumps(record))
