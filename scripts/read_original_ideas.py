import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

fpath = r'C:\Users\86187\.qoder\cache\projects\Socrates-Cube-306233d5\conversation-history\d841528f\d841528f.jsonl'
with open(fpath, encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# 找第一条user消息（包含28个idea）
obj = json.loads(lines[0])
text = obj['message']['content'][0]['text']
# 只打印用户原始查询部分
if '<user_query>' in text:
    start = text.index('<user_query>') + len('<user_query>')
    end = text.index('</user_query>') if '</user_query>' in text else start + 5000
    print(text[start:end])
else:
    print(text[:6000])
