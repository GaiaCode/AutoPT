import json, collections, os, sys
fn = "results_react.jsonl"
if not os.path.exists(fn):
    fn = os.path.join("..","results_react.jsonl")
if not os.path.exists(fn):
    print("results_react.jsonl not found")
    sys.exit(1)

lines=open(fn).read().splitlines()
data=[json.loads(l) for l in lines]
dist = collections.Counter(d['action'] for d in data)
forms = sum(len(d['result_preview']) if isinstance(d['result_preview'], list) else 0
            for d in data if d['action']=='list_forms')
links = sum(len(d['result_preview']) if isinstance(d['result_preview'], list) else 0
            for d in data if d['action']=='extract_links')
print("total events:", len(data))
print("action dist:", dist)
print("forms found:", forms)
print("links found:", links)
