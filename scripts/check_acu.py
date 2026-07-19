import json
data = json.load(open('data/knowledge_graph.json', encoding='utf-8'))
# check top-level keys
print("Keys:", list(data.keys())[:5])
# look for ACU nodes
if 'cognitive_nodes' in data:
    acu = [n for n in data['cognitive_nodes'] if n['id'].startswith('acu_')]
    print(f'ACU in cognitive_nodes: {len(acu)}')
    if acu:
        print('Sample:', acu[0])
        max_id = max(int(a['id'].split('_')[1]) for a in acu)
        print('Max ACU ID:', max_id)
# check nodes
nodes = data.get('nodes', [])
acu_nodes = [n for n in nodes if n.get('id','').startswith('acu_')]
print(f'ACU in nodes: {len(acu_nodes)}')
if acu_nodes:
    print('Sample:', acu_nodes[0])
    max_id = max(int(a['id'].split('_')[1]) for a in acu_nodes)
    print('Max ACU node ID:', max_id)
