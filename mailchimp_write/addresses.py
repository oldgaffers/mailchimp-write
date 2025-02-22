import iso3166
import difflib

def country(member):
  if member['Country'] == '':
    r = 'GB'
  elif member['Country'] == 'United Kingdom':
    r = 'GB'
  elif member['Country'] == 'Eire':
    r = 'IE'
  elif len(member['Country']) == 2:
    r = iso3166.countries_by_alpha2[member['Country'].upper()].alpha2
  elif len(member['Country']) == 3:
    r = iso3166.countries_by_alpha3[member['Country'].upper()].alpha2
  else:
    n = member['Country'].upper()
    if n in iso3166.countries_by_name:
      r = iso3166.countries_by_name[n].alpha2
    else:
      rr = difflib.get_close_matches(n, iso3166.countries_by_name, 5)
      n0 = n.split(' ')[0].rstrip('S')
      r = 'GB'
      for s in rr:
        if n0 in s:
          r = iso3166.countries_by_name[s].alpha2
  return r

def tidy(s):
  if type(s) != str:
    return str(s)
  return ' '.join([x for x in s.split(' ') if x != ''])

def address(member):
  addr1 = tidy(member['Address1'])
  if member['Address2'] != '':
    addr1 = addr1 + ', ' + tidy(member['Address2'])
  r = { 'addr1': addr1, 'city': tidy(member['Town']), 'state': tidy(member['County']), 'zip': tidy(member['Postcode']) }
  if member['Address3'] == '':
    r['addr2'] = ''
  else:
    r['addr2'] = tidy(member['Address3'])
  if member['Postcode'] == '' and member['Country'] == 'France':
    x = member['Address2'].split(' ')
    if len(x)==2 and x[0].isnumeric():
      r['addr1'] = member['Address1']
      r['zip'] = x[0]
      r['city'] = x[1]
    x = member['Town'].split(' ')
    if len(x)==2 and x[0].isnumeric():
      r['zip'] = x[0]
      r['city'] = x[1]
  elif member['County'] == '' and member['Country'] == 'USA':
    if member['Postcode'].isnumeric():
      pass
    else:
      # print('XXXXX', member['Postcode'], member['Postcode'].isnumeric())
      x = member['Postcode'].split(' ')
      if len(x)==2:
        r['state'] = x[0]
        r['zip'] = x[1]
  elif member['County'] == '' and member['Country'] == 'Australia':
    x = member['Postcode'].split(' ')
    if len(x)==2:
      r['state'] = x[0]
      r['zip'] = x[1]
  elif member['Postcode'] == '' and member['Country'] == 'Netherlands':
    if member['Address3'].strip() != '':
      r['zip'] = member['Address3'].strip()
    elif member['Address2'].strip() != '':
      r['zip'] = member['Address2'].strip()
  elif member['Postcode'] == '' and member['Country'] == 'Eire':
    t = member['Town'].split(' ')
    if len(t) == 2 and t[0] == 'Dublin' and t[1].isnumeric():
      district = int(t[1])
      r['zip'] = f"D{district:02d}"
    else:
      pass
  r['country'] = country(member)
  return r

def address1(member):
  r = []
  r.append(tidy(member['Address1']))
  r.append(tidy(member['Address2']))
  r.append(tidy(member['Address3']))
  r.append(tidy(member['Town']))
  r.append(tidy(member['County']))
  r.append(tidy(member['Postcode']))
  r.append(country(member))
  return ', '.join([word for word in r if word != ''])

def add_address(merge_fields, member):
  addr = address(member)
  if addr['addr1'] != '' and addr['city'] != '' and addr['zip'] != '':
    merge_fields['ADDRESS'] = addr
    return
  if addr['zip'] != '':
    a = addr['zip']
  else:
    a = address1(member)
  location = None # geolocator.geocode(a, addressdetails=True)
  if location is None:
    print('no location found')
    merge_fields['ADDRESS'] = a
  else:
    # print('augmented address')
    retrieved_address = location.raw['address']
    if addr['zip'] == '' and 'postcode' in retrieved_address:
      member['Postcode'] = retrieved_address['postcode']
    if addr['city'] == '':
      if 'city' in retrieved_address:
        member['Town'] = retrieved_address['city']
      elif 'suburb' in retrieved_address:
        member['Town'] = retrieved_address['suburb']
    merge_fields['ADDRESS'] = address(member)


def empty_address():
    return { 'addr1': '', 'addr2': '', 'city': '', 'state': '', 'zip': '', 'country': '' }
