import json
data = json.load(open('data/misconceptions.json', encoding='utf-8'))
if isinstance(data, list):
    print(f'Total (list): {len(data)}')
    import pprint
    pprint.pprint(data[0])
else:
    print(f'Keys: {list(data.keys())}')
    first_key = list(data.keys())[0]
    items = data[first_key]
    print(f'Total: {len(items)}')
    import pprint
    pprint.pprint(items[0])
