import json
import hashlib
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from audience_data import get_audience_data
from payment import add_payment_methods
# from addresses import add_address

def get_client():
    return MailchimpMarketing.Client()

def AreaMap(a):
  return {
  'BC': 'Bristol Channel',
  'DB': 'Dublin Bay',
  'EC': 'East Coast',
  'NE': 'North East',
  'NWa': 'North Wales',
  'NW': 'North West',
  'NI': 'Northern Ireland',
  'SC': 'Scotland',
  'SO': 'Solent',
  'SW': 'South West',
  'OS': 'Rest of World',
  'AM': 'The Americas',
  'EU': 'Continental Europe'
  }[a]

def add_joined(merge_fields, member):
  if member['Year Joined'] == '':
    merge_fields['JOINED'] = ''
  elif member['Year Joined'] == None:
    merge_fields['JOINED'] = ''
  else:
    merge_fields['JOINED'] = f"{member['Year Joined']}-01-01"

def add_area(interests, member, audience_data):
  areas = audience_data['Area']
  mia = member['Interest Areas']
  if isinstance(mia, list):
    ia = set([AreaMap(a) for a in mia])
  elif mia.strip() == '':
    ia = set()
  else:
    ia = set([AreaMap(a) for a in member['Interest Areas'].split(',')])
  ia.add(member['Area'])
  for area in areas:
    interests[areas[area]] = area in ia


def add_membership_types(interests, member, audience_data):
  membership_types = audience_data['Membership Type']
  for k,v in membership_types.items():
    interests[v] = False
  if member['Membership Type'] == None:
    interests[membership_types['Single']] = True
  elif member['Membership Type'] == '':
    interests[membership_types['Single']] = True
  else:
    interests[membership_types[member['Membership Type']]] = True

def add_statuses(interests, member, audience_data):
  statuses = audience_data['Status']
  for k,v in statuses.items():
    interests[v] = False
  if member['Membership Type'] == None:
    interests[statuses['Not Paid']] = True
  elif member['Membership Type'] == '':
    interests[statuses['Not Paid']] = True
  else:
    interests[statuses[member['Status']]] = True

def boolToMailchimpBool(val):
  if val:
    return '1'
  return '0'

def build_data(member, audience_data, list):
    small_boats = audience_data['Options']['Interested in events for small boats'];
    primary = audience_data['Family Member']['Primary'];
    use_email = audience_data['Contact Method']['Email'];
    interests = {
       small_boats: member['Trailer'], # Small Boat Events
       primary: member['Primary'] or member['Primary'] == None, # Family Member
       use_email: member['Email'] != '' # contact via email
    }
    add_payment_methods(interests, member, audience_data, list)
    add_area(interests, member, audience_data)
    add_membership_types(interests, member, audience_data)
    add_statuses(interests, member, audience_data)
    merge_fields = {
        'SALUTATION': member['Salutation'], 
        'FNAME': member['Firstname'].strip(),
        'LNAME': member['Lastname'].strip(),
        'PHONE': member['Telephone'],
        'MOBILE': member['Mobile'],
        'MEMBER': int(member['Member Number']),
        'REASON': member['Reason For Joining'],
        'GOLD': int(member['ID']),
        'GDPR': boolToMailchimpBool(member['GDPR'])
    }
    if merge_fields['REASON'] == None:
      merge_fields['REASON'] = ''
    # add_address(merge_fields, member),
    add_joined(merge_fields, member),
    return {
      "status": "subscribed",
      "merge_fields": merge_fields,
      "interests": interests,
    }

def search(client, list, query):
  result = []
  try:
    response = client.searchMembers.search(query, list_id=list)
    r = response['full_search']
    return r['members']
  except ApiClientError as error:
    try:
      e = json.loads(error.text)
      # print(f'{e["title"]} searching for {query}')
    except:
      print(error)
  return result

def mc_key(email):
  return hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()

def entries_for_member(client, list, member):
  r = []
  matches = search(client, list, f'{member["Firstname"]} {member["Lastname"]}')
  id = int(member['ID'])
  for match in matches:
    match_id = match['merge_fields']['GOLD']
    if match_id == id:
      r.append(match)
  return r

def delete(list, email):
  try:
    r = client.lists.delete_list_member(list, mc_key(email))
    # print('archived', email)
  except ApiClientError as error:
    e = json.loads(error.text)
    print(f'{e["title"]} deleting {email}')

def delete_old_email(client, list, email, member):
  matches = entries_for_member(client, list, member)
  if len(matches)>1:
    for match in matches:
      match_email = match['email_address']
      if match_email != email:
        delete(list, match_email)

def add(list, email, member, audience_data):
  data = build_data(member, audience_data, list)
  data['email_address'] = email
  try:
    response = client.lists.add_list_member(list, data)
    # print('added', email)
  except ApiClientError as error:
    e = json.loads(error.text)
    print(error.text)
    if e['title'] == 'Invalid Resource':
      e = json.loads(error.text)
      # print(f'{e["title"]} adding {member["ID"]} {member["Lastname"]} {email}, {e["detail"]}')
      if 'errors' in e:
        print(e['errors'])
      try:
        address = data['merge_fields']['ADDRESS']
        del data['merge_fields']['ADDRESS']
        response = client.lists.add_list_member(list, data)
        # print(f'added {member["Email"]} omitting invalid address {address}')
      except ApiClientError as error:
        e = json.loads(error.text)
        # print(f'{e["title"]} adding {member["ID"]} {member["Lastname"]} {email}')
        return
    elif e['title'] == 'Resource Not Found':
      print(f'{e["title"]} for {member["ID"]} {member["Lastname"]}')
    elif e['title'] == 'Member In Compliance State':
      print(f'{e["title"]} for {member["ID"]} {member["Lastname"]}')
      print(e['detail'])
    else:
      e = json.loads(error.text)
      print(f'{e["title"]} adding {member["ID"]} {member["Lastname"]} {email}')

def same(old, new):
  for key in new:
    if old[key] != new[key]:
        return False, { 'key': key, 'old': old[key], 'new': new[key] }
  for key in old:
    if old[key] != new[key]:
        return False, { 'key': key, 'old': old[key], 'new': new[key] }
  return True, None

def same_interests(complete, partial):
  for key in complete:
    if key in partial:
      if complete[key] != partial[key]:
        return False, { 'key': key, 'complete': complete, 'partial': partial }
    elif complete[key]:
      partial[key] = False
      return False, key
    else:
      pass
  return True, None

def same_permissions(old, new):
  for p in old:
    for q in new:
      if p['marketing_permission_id'] == q['marketing_permission_id']:
        if p['enabled'] != q['enabled']:
          return False, { 'old': old, 'new': new }
  return True, None

def has_changed(old, new):
  s, d = same(old['merge_fields'], new['merge_fields'])
  if s == False:
    return True, d
  s, d = same_interests(old['interests'], new['interests'])
  if s == False:
    return True, d
  #if same_permissions(old['marketing_permissions'], new['marketing_permissions']) == False:
  #  print(old['marketing_permissions'])
  #  print(new['marketing_permissions'])
  #  return True
  return False, None

def update_changed(client, list, email, member, data, changes):
  hash = mc_key(email)
  data['status_if_new'] = 'subscribed'
  try:
    client.lists.set_list_member(list, hash, data)
    print(f'updated member with GOLD ID {member["ID"]} with changes {changes}')
  except ApiClientError as error:
    try:
      e = json.loads(error.text)
      print('json', e)
      print(error)
    except:
      print('can\'t parse error', error)
      e = {'title': 'no idea'}
    print(json.dumps(e))
    if e['title'] == 'Invalid Resource':
      try:
        address = data['merge_fields']['ADDRESS']
        del data['merge_fields']['ADDRESS']
        client.lists.set_list_member(list, hash, data)
        print(f'updated {member["Email"]} omitting invalid address {address}')
      except ApiClientError as error:
        e = json.loads(error.text)
        print(f'{e["title"]} for {member["ID"]} {member["Lastname"]}')
        if 'detail' in e:
          print(e['detail'])
    elif e['title'] == 'Resource Not Found':
      print(f'{e["title"]} for {member["ID"]} {member["Lastname"]}')
    elif e['title'] == 'Member In Compliance State':
      print(f'{e["title"]} for {member["ID"]} {member["Lastname"]}')
      print(e['detail'])
    else:
      print(f'{e["title"]} for {member["ID"]} {member["Lastname"]}')
      if 'detail' in e:
        print(e['detail'])

def update_if_changed(client, list, email, member, old, audience_data):
  data = build_data(member, audience_data, list)
  changed, changes = has_changed(old, data)
  if changed:
    update_changed(client, list, email, member, data, changes)
  else:
    if '@oga.org.uk' in email:
      print('no change to member with GOLD ID', member['ID'])
      pass
    else:
      pass
      print('no change to', email)

def crud(client, list, member):
  email = member['Email'].lower().strip()
  if '@' not in email:
    return
  try:
    response = client.lists.get_list_member(list, mc_key(email))
  except ApiClientError as error:
    response = { 'status': 'missing' }
  audience_data = get_audience_data(list)
  if response['status'] in ['missing', 'archived']:
    if member['Status'] == 'Left OGA':
      pass
      # print('no change to ex member', email)
    else:
      add(list, email, member, audience_data)
  else:
    if member['Status'] == 'Left OGA':
      delete(list, email)
      # print(f'archive {email}')
    else:
      update_if_changed(client ,list, email, member, response, audience_data)
  delete_old_email(client, list, email, member)

def getlistid(client, name):
  r = client.lists.get_all_lists()
  for l in r['lists']:
    if l['name'] == name:
      return l['id']

def archive(client, list, member):
  if '@' in member['Email']:
    email = member['Email'].lower().strip()
  else:
    email = f"{member['ID']}'@oga.org.uk"
  hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
  try:
    r = client.lists.delete_list_member(list, hash)
    print('archive', email)
  except ApiClientError as error:
    print(f'Error: {error.text}')
