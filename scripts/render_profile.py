"""Render repository-owned SVG profile assets; only the portrait needs Pillow."""

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
INK, PANEL, LINE = "#0d141b", "#121e28", "#293b48"
WHITE, MUTED, LIME, CYAN = "#edf3ee", "#95aab5", "#ccfa73", "#76d9e3"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def text(x, y, value, size=16, color=WHITE, extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" {extra}>{html.escape(value)}</text>'


def svg(width, height, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">{html.escape(title)}</title>
<style>
text{{font-family:{FONT}}}
.reveal{{animation:reveal 1.5s ease-out both}}
.portrait-row{{animation:reveal .5s ease-out both;animation-delay:var(--delay)}}
@keyframes reveal{{from{{opacity:0}}to{{opacity:1}}}}
@media(prefers-reduced-motion:reduce){{.reveal,.portrait-row{{animation:none}}}}
</style>
<rect width="{width}" height="{height}" rx="20" fill="{INK}"/>
{body}
</svg>'''


def write(name, content):
    (ASSETS / name).write_text(content, encoding="utf-8")


def portrait_rows(source):
    from PIL import Image, ImageDraw, ImageOps

    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("L")
        w, h = image.size
        # A hand-traced silhouette for this particular avatar, not a general
        # background-removal algorithm. Update the trace when replacing it.
        mask = Image.new("L",image.size)
        outline = [(235,45),(287,36),(334,48),(351,80),(354,132),(344,163),
                   (343,198),(386,225),(423,268),(438,331),(180,331),
                   (185,290),(214,237),(233,217),(252,211),(247,196),
                   (235,178),(226,151),(229,125),(228,95)]
        ImageDraw.Draw(mask).polygon([(round(x*w/460),round(y*h/460)) for x,y in outline],fill=255)
        crop = (round(w*.37),round(h*.05),round(w*.97),round(h*.73))
        image = ImageOps.autocontrast(image.crop(crop)).resize((78,58),Image.Resampling.LANCZOS)
        mask = mask.crop(crop).resize((78,58),Image.Resampling.NEAREST)
        ramp = " .,:;irsXA253hMHGS#9B&@"
        return ["".join(ramp[min(len(ramp)-1, round((image.getpixel((x, y))/255)**.85*(len(ramp)-1)))] if mask.getpixel((x,y)) else " " for x in range(78)) for y in range(58)]


def portrait(x, y, rows):
    parts = [f'<g transform="translate({x} {y})">', f'<rect width="430" height="486" rx="12" fill="{PANEL}" stroke="{LINE}"/>', text(20, 29, "portrait.render()", 13, MUTED)]
    for i, row in enumerate(rows):
        parts.append(text(20, 54+i*6.8, row, 7.9, CYAN if i < 36 else MUTED, f'class="portrait-row" style="--delay:{i*.018:.3f}s" xml:space="preserve" textLength="390" lengthAdjust="spacingAndGlyphs"'))
    parts += [text(20, 463, "MXNR / A PERSON BEHIND THE CODE", 11, LIME), "</g>"]
    return "\n".join(parts)


def identity(x, y, mobile=False):
    parts = [f'<g transform="translate({x} {y})" class="reveal">', text(0, 0, "$ whoami", 16, LIME), text(0, 61, "Dmitry", 47, WHITE, 'font-weight="700"'), text(0, 115, "Siemenov.", 47, WHITE, 'font-weight="700"'), text(0, 152, "@mxnr / AI-augmented engineering", 15, CYAN)]
    parts += [f'<path d="M0 179H{460 if mobile else 610}" stroke="{LINE}"/>']
    for offset, label, value in [(218,"WORKFLOW", "Human intent → agents → verified code"), (257,"STACK", "Rust / JavaScript / PostgreSQL"), (296,"FOCUS", "Architecture · security · UX")]:
        parts += [text(0, offset, label, 12, MUTED), text(0 if mobile else 80, offset+23 if mobile else offset, value, 14, WHITE)]
    parts += [text(0, 366 if mobile else 352, "$ ship something useful_", 17, LIME), "</g>"]
    return "\n".join(parts)


def console(rows, mobile=False):
    w, h = (600, 1130) if mobile else (1200, 670)
    body = f'<path d="M0 59H{w}" stroke="{LINE}"/>'
    for x, color in [(28,"#ff826c"),(48,"#f6cb75"),(68,LIME)]:
        body += f'<circle cx="{x}" cy="30" r="5" fill="{color}"/>'
    body += text(94,35,"mxnr / builder’s console",14,MUTED)
    body += text(32,104,"EXPLORE → BUILD → VERIFY → SHIP",13,LIME)
    body += portrait(85 if mobile else 32, 133, rows)
    body += identity(70 if mobile else 510, 678 if mobile else 181, mobile)
    body += text(32,h-28,"HUMAN JUDGMENT. AGENT LEVERAGE.",12,MUTED)
    return svg(w,h,"Dmitry Siemenov — builder’s console",body)


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-date" in attrs and "data-level" in attrs:
            day = dt.date.fromisoformat(attrs["data-date"])
            level = int(attrs["data-level"])
            if not 0 <= level <= 4:
                raise ValueError("unexpected contribution level")
            self.days[day.isoformat()] = level


def fetch_activity():
    request = urllib.request.Request("https://github.com/users/mxnr/contributions", headers={"User-Agent":"mxnr-profile-renderer"})
    with urllib.request.urlopen(request, timeout=30) as response:
        parser = Calendar()
        parser.feed(response.read().decode("utf-8"))
    if len(parser.days) < 300:
        raise ValueError("incomplete public calendar; keeping existing assets")
    data = {"fetched":dt.datetime.now(dt.timezone.utc).date().isoformat(),"days":parser.days}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "activity.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")


def activity():
    data = json.loads((ROOT / "data" / "activity.json").read_text())
    end = min(dt.date.fromisoformat(max(data["days"])),dt.date.fromisoformat(data["fetched"]))
    start = end - dt.timedelta(days=363+((end.weekday()+1)%7))
    body = text(32,41,"PUBLIC SIGNAL / THE BUILD RHYTHM",16,LIME)
    body += text(32,72,"One building per week. Windows follow daily contribution intensity.",14,MUTED)
    colors = ["#23323b","#35504c","#50785b","#8ac66d",LIME]
    for week in range(53):
        levels = [data["days"].get((start+dt.timedelta(days=week*7+day)).isoformat(),0) for day in range(7)]
        height = 32 + round(math.sqrt(sum(levels)/28)*130)
        x = 33+week*21.4
        top = 272-height
        body += f'<rect x="{x:.1f}" y="{top}" width="17" height="{height}" rx="2" fill="{PANEL}" stroke="{LINE}"/>'
        for day, level in enumerate(levels):
            body += f'<rect x="{x+5:.1f}" y="{top+9+day*(height-17)/7:.1f}" width="7" height="5" rx="1" fill="{colors[level]}"/>'
    body += f'<path d="M32 273H1168" stroke="{LINE}"/>'
    body += text(32,310,start.strftime("%b %Y"),12,MUTED)
    body += text(945,310,"UPDATED "+data["fetched"],12,MUTED)
    write("activity.svg",svg(1200,336,"Public GitHub activity skyline; not a productivity metric",body))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--portrait",action="store_true")
    parser.add_argument("--fetch",action="store_true")
    args = parser.parse_args()
    ASSETS.mkdir(exist_ok=True)
    if args.portrait:
        rows = portrait_rows(ASSETS / "portrait-source.jpg")
        for mobile in [False,True]:
            write("console-mobile.svg" if mobile else "console.svg",console(rows,mobile))
    if args.fetch:
        fetch_activity()
    activity()


if __name__ == "__main__":
    main()
