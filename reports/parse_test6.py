import json
with open(r'G:\streaming app\reports\test6_stream_jawan.json','r',encoding='utf-8') as f:
    d = json.load(f)
status = d.get('status')
streamUrl = d.get('streamUrl')
streams = d.get('streams', [])
print('status:', status)
print('streamUrl:', streamUrl)
print('streams count:', len(streams))
print('stream labels:', [s.get('label') for s in streams])
print('VERDICT:', 'PASS' if status == 'success' and isinstance(streams, list) and len(streams) > 0 else 'FAIL')
