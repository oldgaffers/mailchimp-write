import json
from mailchimp_marketing.api_client import ApiClientError

def get_audience_data(client, list):
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