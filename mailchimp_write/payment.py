
def add_payment_methods(interests, member, audience_data):
  # print('audience_data', audience_data)
  payment_methods = audience_data.get('Payment Method', {})
  # print('payment_methods', payment_methods)
  for k,v in payment_methods.items():
    interests[v] = False
  payment_method = member['Payment Method']
  if payment_method == None or payment_method == '':
    payment_method = 'PayPal'
  if payment_method not in payment_methods.keys():
    print('missing payment method', payment_method)
    print(payment_methods)