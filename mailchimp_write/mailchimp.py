import json
import os
from sync import get_client, getlistid, crud, archive, audit

def update_mailchimp(action, record):
  # print('update_mailchimp', action, record)
  apiKey = os.environ['API_KEY']
  server = os.environ['SERVER']
  audience = os.environ['AUDIENCE']
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
