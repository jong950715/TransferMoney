d = {'key1': 'hi'}

try:
    print(d['noKey'])
except KeyError as e:
    key = (e.args[0])
    if key == 'noKey':
        print('yes')