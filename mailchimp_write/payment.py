from audience_data import get_audience_data

def add_payment_methods(interests, member, audience_data, list):
  payment_methods = audience_data['Payment Method']
  for k,v in payment_methods.items():
    interests[v] = False
  payment_method = member['Payment Method']
  if payment_method == None or payment_method == '':
    payment_method = 'PayPal'
  if payment_method not in payment_methods.keys():
    # print('missing payment method', payment_method)
    # print(payment_methods)
    category_id = audience_data['categories']['Payment Method']
    r = client.lists.create_interest_category_interest(list, category_id, {'name': payment_method})
    # print('re-fetching audience data')
    audience_data = get_audience_data(client, list)
    payment_methods = audience_data['Payment Method']
    for k,v in payment_methods.items():
      interests[v] = False
  try:
    interests[payment_methods[member['Payment Method']]] = True
  except KeyError as error:
    print(error)
    print(member)