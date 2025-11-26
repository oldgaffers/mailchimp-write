import json
from mailchimp_marketing.api_client import ApiClientError

def get_audience_data(client, list, values):
  add_new_values(client, list, values)
  audience_data = {}
  try:
    response = client.lists.get_list_interest_categories(list, count=100)
    audience_data['categories'] = {}
    for category in response['categories']:
      # print('collecting', category['title'])
      audience_data['categories'][category['title']] = category['id']
      try:
        response = client.lists.list_interest_category_interests(list, category['id'], count=100)
        group = {}
        for interest in response['interests']:
          # print(interest)
          group[interest['name']] = interest['id']  
        audience_data[category['title']] = group
      except ApiClientError as error:
        e = json.loads(error.text)
        print(f'{e["title"]} getting category {interest["name"]}')
  except ApiClientError as error:
    e = json.loads(error.text)
    print(f'{e["title"]} getting categories')
  return audience_data

def add_new_values(client, list, values):
  response = client.lists.get_list_interest_categories(list, count=100)
  # for any field in values which matches a category title
  # add missing values
  # e.g. 'Status' is both a category title and a key in values so
  # if values['Status'] is not in the interests for category 'Status'
  # then create it
  for category in response['categories']:
    title = category['title']
    if title in values:
      value = values[title]
      response = client.lists.list_interest_category_interests(list, category['id'], count=100)
      values = response['interests']
      if not any(v['name'] == value for v in values):
        print(f'adding "{value}" to category "{title}"')
        category_id = category['id']
        client.lists.create_interest_category_interest(list, category_id, {'name': value})