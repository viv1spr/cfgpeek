"""Раз в неделю: настройки игроков с cs-config.com (прицел, мышь, экран, viewmodel, параметры запуска) -> data/csconfig.json.
Берём только факты-значения. Темп ~1 запрос в 1.3 с, robots.txt разрешает эти страницы."""
import html, json, os, re, time, urllib.request, urllib.error
UA = {"User-Agent": "Mozilla/5.0 (compatible; cfgpeek.com settings index; +https://cfgpeek.com)"}
def get(u):
    for i in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410): return e.code, ""
            time.sleep(5)
        except Exception:
            time.sleep(5)
    return 0, ""
def txt(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
def parse(t):
    d = {}
    for lab, val in re.findall(r'<span class="page-player-label">(.*?)</span>\s*<span class="page-player-val">(.*?)</span>', t, re.S):
        d[txt(lab).rstrip(":")] = txt(val)
    m = re.search(r'id="secondTarget">\s*<div class="code-console">\s*(CS[A-Za-z0-9]{44})\s*<', t)
    code = m.group(1) if m else None
    if not code:
        m = re.search(r'\b(CS[A-Za-z0-9]{44})\b', t); code = m.group(1) if m else None
    vm = re.search(r'<div class="code-console[^"]*">\s*(viewmodel_fov[^<]+)<', t)
    ln = re.search(r'Параметры запуска</div>\s*<div class="aim-page-code">.*?<div class="code-console[^"]*">([^<]*)<', t, re.S)
    up = re.search(r'Обновлено:\s*([^<]+)<', t)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    return {"params": d, "code": code, "vm": txt(vm.group(1)) if vm else None, "launch": txt(ln.group(1)) if ln else None,
            "updated": up.group(1).strip() if up else None, "h1": txt(h1.group(1)) if h1 else None}
def main():
    prof = json.load(open("data/profiles.json", encoding="utf-8"))
    out = json.load(open("data/csconfig.json", encoding="utf-8")) if os.path.exists("data/csconfig.json") else {}
    miss = 0
    for q in prof:
        slug, nick = q.get("slug"), (q.get("nick") or "")
        if not slug: continue
        cands = []
        for c in [slug, re.sub(r"[^a-z0-9]", "", nick.lower()), nick.lower().replace(" ", "-")]:
            if c and c not in cands: cands.append(c)
        got = None
        for c in cands:
            url = f"https://cs-config.com/{c}-cfg-csgo"
            st, t = get(url); time.sleep(1.3)
            if st == 200 and "page-player-val" in t:
                got = dict(parse(t), url=url); break
        if got and (got["code"] or got["params"]):
            out[slug] = got
        else:
            miss += 1
    json.dump(out, open("data/csconfig.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"найдено: {len(out)}, нет на сайте: {miss}")
if __name__ == "__main__":
    main()
