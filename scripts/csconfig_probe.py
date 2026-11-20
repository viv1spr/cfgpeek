"""Пробный сбор: карта сайта cs-config.com и несколько страниц как есть — чтобы написать разборщик."""
import os, re, time, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (compatible; cfgpeek.com settings index; +https://cfgpeek.com)"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return f"ERR {e}"
os.makedirs("data/_cs_probe", exist_ok=True)
log = []
for u in ["https://cs-config.com/robots.txt", "https://cs-config.com/sitemap.xml", "https://cs-config.com/sitemap_index.xml"]:
    t = get(u); log.append(f"{u} {len(t)} {t[:200]!r}")
    open("data/_cs_probe/" + re.sub(r"\W", "_", u.split("/")[-1]) + ".txt", "w").write(t)
    time.sleep(1)
for slug in ["r1nkle", "donk", "fallen"]:
    t = get(f"https://cs-config.com/{slug}-cfg-csgo"); log.append(f"{slug} {len(t)}")
    open(f"data/_cs_probe/{slug}.html", "w").write(t); time.sleep(1.5)
open("data/_cs_probe/log.txt", "w").write("\n".join(log))
print("\n".join(log))
