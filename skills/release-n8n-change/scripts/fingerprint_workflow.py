#!/usr/bin/env python3
import argparse, json
from common import fingerprint, load_json

p = argparse.ArgumentParser()
p.add_argument("workflow")
p.add_argument("--json", action="store_true")
a = p.parse_args()
fp = fingerprint(load_json(a.workflow))
print(json.dumps({"fingerprint": fp}) if a.json else fp)
