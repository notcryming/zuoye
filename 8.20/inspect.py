import re

d = open('douluo_full.txt', encoding='utf-8').read()
print('total chars:', len(d))

chap_re = re.compile(r'^\s*(第[^。\n]{1,15}章[^\n]*)\s*$', re.M)
chapters = [(m.start(), m.group(1).strip()) for m in chap_re.finditer(d)]
print('chapter count:', len(chapters))
print('first titles:', [t for _, t in chapters[:15]])

dq = re.findall(r'“([^”]{4,80})”', d)
print('dialogue lines:', len(dq))
print('dialogue samples:')
for x in dq[:10]:
    print('  Q:', x)

iac = re.findall(r'[。！？；”]\s*[^。！？\n]{0,12}说[道曰]', d)
print('speaker markers:', len(iac))