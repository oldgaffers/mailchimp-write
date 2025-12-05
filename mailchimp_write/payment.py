def add_payment_methods(interests, member, audience_data):
  # print('audience_data', audience_data)
  payment_methods = audience_data.get('Payment Method', {})
  # print('payment_methods', payment_methods)
  for k,v in payment_methods.items():
    interests[v] = False
  payment_method = member['Payment Method']
  if payment_method in payment_methods.keys():
    interests[payment_methods[payment_method]] = True
  else:
    print('missing payment method', payment_method)
    print(payment_methods)