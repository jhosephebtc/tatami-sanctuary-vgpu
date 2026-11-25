"""Baixa modelos CC0 reais do Poly Haven (1k glTF) para o jardim japones externo."""
import json
import os
import urllib.request

OUT_DIR = r"C:\Users\Administrador\.gemini\antigravity\scratch\sala-japonesa-blueprint\assets_polyhaven"
UA = {"User-Agent": "arquiteto-garden-fetch/1.0"}
MODELS = ["fern_02", "shrub_02", "rock_moss_set_01", "tree_small_02"]


def fetch_url(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    index = {}
    for mid in MODELS:
        req = urllib.request.Request(f"https://api.polyhaven.com/files/{mid}", headers=UA)
        files = json.loads(urllib.request.urlopen(req, timeout=60).read())
        gltf_block = files.get("gltf", {})
        res_key = "1k" if "1k" in gltf_block else ("2k" if "2k" in gltf_block else None)
        if not res_key or "gltf" not in gltf_block[res_key]:
            print(f"[SKIP] {mid} sem gltf")
            continue
        entry = gltf_block[res_key]["gltf"]
        mdir = os.path.join(OUT_DIR, mid)
        main_path = os.path.join(mdir, os.path.basename(entry["url"]))
        fetch_url(entry["url"], main_path)
        for rel, inc in entry.get("include", {}).items():
            fetch_url(inc["url"], os.path.join(mdir, rel))
        index[mid] = main_path
        print(f"[PolyHaven OK] {mid} ({res_key}) -> {main_path}")
    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


if __name__ == "__main__":
    main()
