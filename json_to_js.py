import json
import sys

# 사용법:
# python tools/json_to_js.py data/parsed_qa.json data/parsed_qa.js

in_path = sys.argv[1] if len(sys.argv) > 1 else "parsed_qa.json"
out_path = sys.argv[2] if len(sys.argv) > 2 else "parsed_qa.js"

with open(in_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 한글 유지: ensure_ascii=False [web:62][web:23]
js = "/* auto-generated */\n"
js += "window.__QA__ = " + json.dumps(data, ensure_ascii=False) + ";\n"

with open(out_path, "w", encoding="utf-8") as f:
    f.write(js)

print("OK:", out_path)
