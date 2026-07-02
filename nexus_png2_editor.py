#!/usr/bin/env python3
"""
nexus_png2_editor.py — NeXuS Character Card Editor
View and edit chara_card_v2 PNG files. Export to aichat roles.
"""

import base64
import json
import os
import struct
import zlib
from pathlib import Path
from flask import Flask, request, jsonify, send_file, redirect

# ── Config ────────────────────────────────────────────────────────────────────
CARDS_DIR   = Path(os.environ.get("CARDS_DIR", Path.home() / "01/ai-characters"))
ROLES_DIR   = Path(os.environ.get("ROLES_DIR", Path.home() / ".config/aichat/roles"))
PORT        = int(os.environ.get("PORT", 7420))

FIELDS = ["name", "description", "personality", "scenario",
          "system_prompt", "post_history_instructions", "first_mes",
          "mes_example", "creator", "creator_notes", "character_version", "tags"]

app = Flask(__name__)

# ── PNG helpers ───────────────────────────────────────────────────────────────

def _crc32(data: bytes) -> bytes:
    return struct.pack(">I", zlib.crc32(data) & 0xFFFFFFFF)

def png_read_chunks(data: bytes):
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    chunks, pos = [], 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos+4])[0]
        ctype  = data[pos+4:pos+8]
        cdata  = data[pos+8:pos+8+length]
        chunks.append((ctype, cdata))
        pos += 12 + length
    return chunks

def png_write_chunks(chunks) -> bytes:
    out = b"\x89PNG\r\n\x1a\n"
    for ctype, cdata in chunks:
        out += struct.pack(">I", len(cdata))
        out += ctype
        out += cdata
        out += _crc32(ctype + cdata)
    return out

def read_chara(path: Path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    for ctype, cdata in png_read_chunks(data):
        if ctype in (b"tEXt", b"iTXt"):
            null = cdata.find(b"\x00")
            if null > 0:
                key = cdata[:null].decode("utf-8", errors="ignore")
                if key == "chara":
                    val = cdata[null+1:].decode("utf-8", errors="ignore")
                    try:
                        return json.loads(base64.b64decode(val))
                    except Exception:
                        return None
    return None

def write_chara(path: Path, chara: dict):
    raw = path.read_bytes()
    chunks = png_read_chunks(raw)
    new_val = base64.b64encode(json.dumps(chara, ensure_ascii=False).encode()).decode()
    new_chunk = (b"tEXt", b"chara\x00" + new_val.encode())
    # Drop old chara chunk, keep everything else
    kept = [(ct, cd) for ct, cd in chunks if not (
        ct in (b"tEXt", b"iTXt") and cd.startswith(b"chara\x00")
    )]
    # Insert after IHDR
    kept.insert(1, new_chunk)
    path.write_bytes(png_write_chunks(kept))

def list_cards():
    cards = []
    for f in sorted(CARDS_DIR.glob("*.png")):
        chara = read_chara(f)
        if not chara:
            continue
        inner = chara.get("data", chara)
        cards.append({
            "file": f.name,
            "name": inner.get("name", f.stem),
            "tags": inner.get("tags", []),
            "description": (inner.get("description") or "")[:100],
        })
    return cards

def to_aichat_role(inner: dict) -> str:
    name = inner.get("name", "character")
    parts = []
    for field in ["description", "personality", "scenario", "system_prompt",
                  "post_history_instructions"]:
        val = (inner.get(field) or "").strip()
        if val:
            val = val.replace("{{char}}", name).replace("{{user}}", "the user")
            parts.append(val)
    return "\n\n".join(parts)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    cards = list_cards()
    cards_json = json.dumps(cards)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NeXuS PNG² Editor</title>
<style>
  :root {{
    --bg: #0a0e14; --surface: #0f1520; --surface2: #1a2233;
    --border: #1e3a5f; --primary: #00d4ff; --accent: #7c3aed;
    --green: #00ff88; --orange: #ff8c00; --red: #ff4444;
    --text: #c9d1d9; --muted: #6e7681; --white: #e6edf3;
    --mono: 'JetBrains Mono', 'Fira Code', monospace;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: var(--mono); min-height: 100vh; }}

  /* ── Header ── */
  header {{ background: var(--surface); border-bottom: 1px solid var(--border);
            padding: 12px 24px; display: flex; align-items: center; gap: 16px;
            position: sticky; top: 0; z-index: 100; }}
  header h1 {{ color: var(--primary); font-size: 18px; letter-spacing: 2px; text-transform: uppercase; }}
  header span {{ color: var(--muted); font-size: 12px; }}
  .search-box {{ margin-left: auto; background: var(--surface2); border: 1px solid var(--border);
                 color: var(--text); padding: 6px 12px; border-radius: 6px; font-family: var(--mono);
                 font-size: 13px; width: 220px; outline: none; }}
  .search-box:focus {{ border-color: var(--primary); }}

  /* ── Grid ── */
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
           gap: 16px; padding: 24px; }}
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
           cursor: pointer; overflow: hidden; transition: border-color 0.2s, transform 0.15s; }}
  .card:hover {{ border-color: var(--primary); transform: translateY(-2px); }}
  .card img {{ width: 100%; aspect-ratio: 1; object-fit: cover; display: block; background: var(--surface2); }}
  .card-info {{ padding: 10px 12px; }}
  .card-name {{ color: var(--white); font-size: 13px; font-weight: 700; margin-bottom: 4px;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .card-desc {{ color: var(--muted); font-size: 11px; line-height: 1.4;
                overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
  .card-tags {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }}
  .tag {{ background: var(--surface2); color: var(--primary); font-size: 10px;
          padding: 2px 6px; border-radius: 4px; border: 1px solid var(--border); }}

  /* ── Editor Panel ── */
  #editor {{ display: none; position: fixed; inset: 0; z-index: 200;
             background: rgba(0,0,0,0.85); backdrop-filter: blur(4px);
             overflow-y: auto; }}
  .editor-inner {{ max-width: 960px; margin: 40px auto; background: var(--surface);
                   border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
  .editor-header {{ background: var(--surface2); padding: 14px 20px;
                    display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--border); }}
  .editor-header h2 {{ color: var(--primary); font-size: 15px; flex: 1; }}
  .btn {{ padding: 7px 16px; border-radius: 6px; font-family: var(--mono); font-size: 12px;
          cursor: pointer; border: 1px solid; font-weight: 600; transition: all 0.15s; }}
  .btn-primary {{ background: var(--primary); color: #000; border-color: var(--primary); }}
  .btn-primary:hover {{ background: #00b8e0; }}
  .btn-accent  {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .btn-accent:hover  {{ background: #6d28d9; }}
  .btn-ghost   {{ background: transparent; color: var(--muted); border-color: var(--border); }}
  .btn-ghost:hover   {{ color: var(--text); border-color: var(--muted); }}
  .btn-green   {{ background: var(--green); color: #000; border-color: var(--green); }}
  .btn-green:hover {{ background: #00e07a; }}
  .btn-orange  {{ background: var(--orange); color: #000; border-color: var(--orange); }}
  .btn-orange:hover {{ background: #e07800; }}

  .editor-body {{ display: grid; grid-template-columns: 240px 1fr; }}
  .editor-portrait {{ padding: 20px; border-right: 1px solid var(--border); }}
  .editor-portrait img {{ width: 100%; border-radius: 8px; border: 1px solid var(--border); }}
  .portrait-meta {{ margin-top: 12px; font-size: 11px; color: var(--muted); line-height: 1.8; }}
  .portrait-meta strong {{ color: var(--text); }}

  .editor-fields {{ padding: 20px; display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }}
  .field-group {{ display: flex; flex-direction: column; gap: 6px; }}
  .field-label {{ font-size: 11px; color: var(--primary); text-transform: uppercase;
                  letter-spacing: 1px; font-weight: 700; }}
  .field-input, .field-textarea {{ background: var(--surface2); border: 1px solid var(--border);
    color: var(--text); padding: 8px 10px; border-radius: 6px; font-family: var(--mono);
    font-size: 12px; outline: none; width: 100%; resize: vertical; line-height: 1.5; }}
  .field-input:focus, .field-textarea:focus {{ border-color: var(--primary); }}
  .field-textarea {{ min-height: 80px; }}
  .field-textarea.tall {{ min-height: 140px; }}
  .tags-input {{ display: flex; flex-wrap: wrap; gap: 6px; background: var(--surface2);
                 border: 1px solid var(--border); padding: 6px 8px; border-radius: 6px; }}
  .tag-chip {{ background: var(--accent); color: #fff; padding: 2px 8px; border-radius: 4px;
               font-size: 11px; display: flex; align-items: center; gap: 4px; }}
  .tag-chip span {{ cursor: pointer; color: #ddd; }}
  .tag-add {{ background: none; border: none; color: var(--muted); font-family: var(--mono);
              font-size: 12px; cursor: text; flex: 1; min-width: 80px; padding: 0; outline: none; }}

  /* ── Toast ── */
  #toast {{ position: fixed; bottom: 24px; right: 24px; background: var(--surface2);
            border: 1px solid var(--green); color: var(--green); padding: 12px 20px;
            border-radius: 8px; font-size: 13px; display: none; z-index: 999; }}
  #toast.error {{ border-color: var(--red); color: var(--red); }}

  .no-cards {{ text-align: center; padding: 60px 20px; color: var(--muted); }}
  .no-cards h2 {{ color: var(--text); margin-bottom: 8px; }}
</style>
</head>
<body>

<header>
  <h1>⬡ NeXuS PNG² Editor</h1>
  <span id="count"></span>
  <input class="search-box" type="text" placeholder="Search characters..." oninput="filterCards(this.value)" />
</header>

<div class="grid" id="grid"></div>
<div class="no-cards" id="empty" style="display:none">
  <h2>No character cards found</h2>
  <p>Put PNG cards in: {CARDS_DIR}</p>
</div>

<!-- Editor Overlay -->
<div id="editor">
  <div class="editor-inner">
    <div class="editor-header">
      <h2 id="ed-title">Character</h2>
      <button class="btn btn-green"  onclick="saveCard()">💾 Save PNG</button>
      <button class="btn btn-accent" onclick="exportRole()">⬡ Export .md</button>
      <button class="btn btn-orange" onclick="exportJson()">&#123;&#125; Export JSON</button>
      <button class="btn btn-ghost"  onclick="closeEditor()">✕ Close</button>
    </div>
    <div class="editor-body">
      <div class="editor-portrait">
        <img id="ed-img" src="" alt="portrait" />
        <div class="portrait-meta">
          <div><strong>File:</strong> <span id="ed-file"></span></div>
          <div><strong>Spec:</strong> <span id="ed-spec"></span></div>
          <div><strong>Creator:</strong> <span id="ed-creator-meta"></span></div>
        </div>
      </div>
      <div class="editor-fields" id="ed-fields"></div>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
const CARDS = {cards_json};
let currentFile = null;
let currentData = null;
let tagList = [];

// ── Grid ──────────────────────────────────────────────────────────────────────
function renderGrid(cards) {{
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  document.getElementById('count').textContent = cards.length + ' cards';
  if (cards.length === 0) {{ grid.innerHTML=''; empty.style.display='block'; return; }}
  empty.style.display = 'none';
  grid.innerHTML = cards.map(c => `
    <div class="card" onclick="openCard('${{c.file}}')">
      <img src="/thumb/${{encodeURIComponent(c.file)}}" alt="${{c.name}}" loading="lazy"
           onerror="this.style.background='#1a2233';this.style.height='200px'" />
      <div class="card-info">
        <div class="card-name">${{c.name}}</div>
        <div class="card-desc">${{c.description}}</div>
        <div class="card-tags">${{(c.tags||[]).slice(0,4).map(t=>`<span class="tag">${{t}}</span>`).join('')}}</div>
      </div>
    </div>`).join('');
}}

function filterCards(q) {{
  q = q.toLowerCase();
  renderGrid(q ? CARDS.filter(c =>
    c.name.toLowerCase().includes(q) ||
    c.description.toLowerCase().includes(q) ||
    (c.tags||[]).some(t => t.toLowerCase().includes(q))
  ) : CARDS);
}}

// ── Editor ────────────────────────────────────────────────────────────────────
async function openCard(file) {{
  const res = await fetch('/card/' + encodeURIComponent(file));
  const d = await res.json();
  if (d.error) {{ toast(d.error, true); return; }}
  currentFile = file;
  currentData = d;
  const inner = d.data || d;
  tagList = [...(inner.tags || [])];

  document.getElementById('ed-title').textContent = inner.name || file;
  document.getElementById('ed-file').textContent = file;
  document.getElementById('ed-spec').textContent = (d.spec || '') + ' ' + (d.spec_version || '');
  document.getElementById('ed-creator-meta').textContent = inner.creator || '—';
  document.getElementById('ed-img').src = '/thumb/' + encodeURIComponent(file);

  const fields = document.getElementById('ed-fields');
  const TALL = ['description','personality','scenario','system_prompt','post_history_instructions','first_mes','mes_example'];
  fields.innerHTML = [
    ['name',        'Name',                       false],
    ['description', 'Description',                true],
    ['personality', 'Personality',                true],
    ['scenario',    'Scenario',                   true],
    ['system_prompt','System Prompt',             true],
    ['post_history_instructions','Post History Instructions', true],
    ['first_mes',   'First Message',              true],
    ['mes_example', 'Example Messages',           true],
    ['creator',     'Creator',                    false],
    ['creator_notes','Creator Notes',             false],
    ['character_version','Version',               false],
  ].map(([key, label, tall]) => `
    <div class="field-group">
      <div class="field-label">${{label}}</div>
      ${{tall
        ? `<textarea class="field-textarea ${{TALL.includes(key)?'tall':''}}" data-key="${{key}}" id="f-${{key}}">${{esc(inner[key]||'')}}</textarea>`
        : `<input class="field-input" data-key="${{key}}" id="f-${{key}}" value="${{esc(inner[key]||'')}}" />`
      }}
    </div>`).join('') + `
    <div class="field-group">
      <div class="field-label">Tags</div>
      <div class="tags-input" id="tags-container">
        ${{renderTagChips()}}
        <input class="tag-add" id="tag-input" placeholder="add tag..." onkeydown="tagKeydown(event)" />
      </div>
    </div>`;

  document.getElementById('editor').style.display = 'block';
  document.body.style.overflow = 'hidden';
}}

function renderTagChips() {{
  return tagList.map((t,i) =>
    `<span class="tag-chip">${{t}} <span onclick="removeTag(${{i}})">×</span></span>`
  ).join('');
}}

function removeTag(i) {{
  tagList.splice(i, 1);
  document.getElementById('tags-container').innerHTML =
    renderTagChips() + '<input class="tag-add" id="tag-input" placeholder="add tag..." onkeydown="tagKeydown(event)" />';
}}

function tagKeydown(e) {{
  if (e.key === 'Enter' || e.key === ',') {{
    e.preventDefault();
    const val = e.target.value.trim();
    if (val) {{ tagList.push(val); e.target.value = ''; }}
    document.getElementById('tags-container').innerHTML =
      renderTagChips() + '<input class="tag-add" id="tag-input" placeholder="add tag..." onkeydown="tagKeydown(event)" />';
    document.getElementById('tag-input').focus();
  }}
}}

function collectFields() {{
  const inner = currentData.data || currentData;
  document.querySelectorAll('[data-key]').forEach(el => {{
    inner[el.dataset.key] = el.value;
  }});
  inner.tags = [...tagList];
  if (currentData.data) currentData.data = inner;
  return currentData;
}}

async function saveCard() {{
  const payload = collectFields();
  const res = await fetch('/save/' + encodeURIComponent(currentFile), {{
    method: 'POST', headers: {{'Content-Type':'application/json'}},
    body: JSON.stringify(payload)
  }});
  const d = await res.json();
  d.ok ? toast('Saved to PNG ✓') : toast(d.error, true);
}}

async function exportRole() {{
  const payload = collectFields();
  const res = await fetch('/export/' + encodeURIComponent(currentFile), {{
    method: 'POST', headers: {{'Content-Type':'application/json'}},
    body: JSON.stringify(payload)
  }});
  const d = await res.json();
  d.ok ? toast('Exported → ' + d.role_file + ' ✓') : toast(d.error, true);
}}

function exportJson() {{
  const payload = collectFields();
  const inner = payload.data || payload;
  const name = (inner.name || 'character').toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{type: 'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name + '.json';
  a.click();
  URL.revokeObjectURL(a.href);
  toast('Downloaded ' + name + '.json ✓');
}}

function closeEditor() {{
  document.getElementById('editor').style.display = 'none';
  document.body.style.overflow = '';
  currentFile = null; currentData = null;
}}

function esc(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function toast(msg, err=false) {{
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = err ? 'error' : '';
  t.style.display = 'block';
  setTimeout(() => t.style.display='none', 3000);
}}

document.getElementById('editor').addEventListener('click', e => {{
  if (e.target === document.getElementById('editor')) closeEditor();
}});

renderGrid(CARDS);
</script>
</body>
</html>"""

@app.route("/thumb/<filename>")
def thumb(filename):
    path = CARDS_DIR / filename
    if not path.exists() or not path.suffix.lower() == ".png":
        return "", 404
    return send_file(path, mimetype="image/png")

@app.route("/card/<filename>")
def card(filename):
    path = CARDS_DIR / filename
    if not path.exists():
        return jsonify({"error": "File not found"})
    chara = read_chara(path)
    if chara is None:
        return jsonify({"error": "No chara data in this PNG"})
    return jsonify(chara)

@app.route("/save/<filename>", methods=["POST"])
def save(filename):
    path = CARDS_DIR / filename
    if not path.exists():
        return jsonify({"error": "File not found"})
    try:
        chara = request.get_json()
        write_chara(path, chara)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/export/<filename>", methods=["POST"])
def export_role(filename):
    try:
        chara = request.get_json()
        inner = chara.get("data", chara)
        name  = inner.get("name", Path(filename).stem)
        role_name = name.lower().replace(" ", "-").replace(".", "").replace("_", "-")
        role_name = "".join(c for c in role_name if c.isalnum() or c == "-")
        prompt = to_aichat_role(inner)
        if not prompt.strip():
            return jsonify({"error": "No content to export"})
        ROLES_DIR.mkdir(parents=True, exist_ok=True)
        role_file = ROLES_DIR / f"{role_name}.md"
        role_file.write_text(prompt.strip() + "\n")
        return jsonify({"ok": True, "role_file": str(role_file)})
    except Exception as e:
        return jsonify({"error": str(e)})

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"⬡ NeXuS PNG² Editor")
    print(f"  Cards dir : {CARDS_DIR}")
    print(f"  Roles dir : {ROLES_DIR}")
    print(f"  Open      : http://localhost:{PORT}")
    app.run(host="127.0.0.1", port=PORT, debug=False)
