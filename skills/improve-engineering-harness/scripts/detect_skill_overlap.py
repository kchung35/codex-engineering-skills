from __future__ import annotations
import argparse, re, json
from pathlib import Path

def desc(path):
    t=path.read_text(encoding='utf-8'); m=re.search(r'^description:\s*["\']?(.*?)["\']?\s*$',t,re.M); return m.group(1) if m else ''
def toks(s):
    stop={'the','a','an','and','or','to','of','for','with','when','use','this','do','not','is','in','on','from','before'}
    return {w for w in re.findall(r'[a-z0-9-]{3,}',s.lower()) if w not in stop}
def main():
    p=argparse.ArgumentParser(); p.add_argument('skills_dir'); p.add_argument('--threshold',type=float,default=.45); a=p.parse_args()
    rows=[]; skills=[]
    for s in sorted(Path(a.skills_dir).iterdir()):
        f=s/'SKILL.md'
        if f.exists(): skills.append((s.name,toks(desc(f))))
    for i,(n1,t1) in enumerate(skills):
        for n2,t2 in skills[i+1:]:
            union=t1|t2; score=len(t1&t2)/len(union) if union else 0
            if score>=a.threshold: rows.append({'skill_a':n1,'skill_b':n2,'jaccard':round(score,3),'shared':sorted(t1&t2)})
    print(json.dumps({'threshold':a.threshold,'flags':rows,'note':'Lexical signal only; inspect semantic intent/procedure before changing boundaries.'},indent=2))
    raise SystemExit(2 if rows else 0)
if __name__=='__main__': main()
