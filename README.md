# ⬡ NeXuS PNG² Editor

> View, edit, and export AI character cards — straight from your desktop.

A lightweight web app for reading and editing **chara_card_v2** PNG files (TavernAI / SillyTavern / Character Card Architect format). Built for the NeXuS stack — runs locally, no cloud, no tracking.

---

## ✨ Features

- 🖼️ **Visual card browser** — grid of all your PNG character cards with portraits
- ✏️ **Full field editor** — name, description, personality, scenario, system prompt, first message, tags, and more
- 💾 **Save back to PNG** — writes edits into the PNG `tEXt` chunk non-destructively (image unchanged)
- ⬡ **Export as .md** — one-click aichat role export to `~/.config/aichat/roles/`
- `{}` **Export as JSON** — download full character data as a `.json` file
- 🔍 **Live search** — filter by name, description, or tag
- 🏴 **100% local** — no API keys, no telemetry, runs on `localhost:7420`

---

## 🚀 Quick Start

```bash
git clone https://github.com/hackenstacks/NeXuS-png2-editor
cd NeXuS-png2-editor
pip install flask pillow
python3 nexus_png2_editor.py
```

Open **http://localhost:7420** in your browser.

---

## ⚙️ Configuration

Override defaults with environment variables:

```bash
CARDS_DIR=~/my-cards PORT=8080 python3 nexus_png2_editor.py
```

| Variable   | Default                        | Description                        |
|------------|--------------------------------|------------------------------------|
| `CARDS_DIR`| `~/01/ai-characters`           | Directory containing PNG card files|
| `ROLES_DIR`| `~/.config/aichat/roles`       | aichat roles output directory      |
| `PORT`     | `7420`                         | Local server port                  |

---

## 📦 Card Format

Supports the **chara_card_v2** spec — the standard used by:
- [TavernAI](https://github.com/TavernAI/TavernAI)
- [SillyTavern](https://github.com/SillyTavern/SillyTavern)
- [The Card Architect](https://aicharactercards.com)
- [aicharactercards.com](https://aicharactercards.com)

Character data is stored as base64-encoded JSON in the PNG `tEXt` chunk under the key `chara`.

---

## ⬡ aichat Integration

### Installing aichat

**From GitHub releases (recommended — pre-built binary):**
```bash
# Check latest release at https://github.com/sigoden/aichat/releases
wget https://github.com/sigoden/aichat/releases/latest/download/aichat-x86_64-unknown-linux-musl.tar.gz
tar xzf aichat-*.tar.gz
mv aichat ~/.local/bin/
```

**From Cargo (build from source):**
```bash
cargo install aichat
```

**Alpine Linux:**
```bash
# musl build — no extra libs needed
wget https://github.com/sigoden/aichat/releases/latest/download/aichat-x86_64-unknown-linux-musl.tar.gz
tar xzf aichat-*.tar.gz && mv aichat ~/.local/bin/
```

### Configure aichat

Create `~/.config/aichat/config.yaml` with your provider:

```yaml
model: mistral:mistral-medium-latest
clients:
  - type: openai-compatible
    name: mistral
    api_base: https://api.mistral.ai/v1
    api_key: YOUR_KEY_HERE
```

Or use Ollama locally (no API key needed):

```yaml
model: ollama:llama3.2
clients:
  - type: ollama
```

### Starting the aichat web playground

```bash
aichat --serve
# Default port: 8000
# Open: http://localhost:8000/playground
```

Custom port:
```bash
aichat --serve 0.0.0.0:3030
```

Once running, exported `.md` roles appear instantly in the **Role** dropdown in the playground.

---

## 🌐 Running without aichat

The PNG editor works fully standalone — you don't need aichat at all to view, edit, or export cards.

**Export JSON** downloads the full `chara_card_v2` data as a `.json` file you can use with any tool.

**Export .md** still writes the role file to disk — useful even without aichat if you want a plain-text version of the character prompt.

If you want a simple web server just to serve the playground UI without aichat, you can use Python's built-in server for static files:

```bash
# Serve a directory of files on port 8080
python3 -m http.server 8080 --directory ~/my-static-dir
```

Or run this editor itself — it's a self-contained web app that needs no external services:

```bash
python3 nexus_png2_editor.py
# That's it. No database, no config required.
```

---

## 📤 Export Options

| Button | Output | Description |
|--------|--------|-------------|
| 💾 **Save PNG** | Updates the source `.png` | Writes edits back into the PNG metadata — image pixel data untouched |
| ⬡ **Export .md** | `~/.config/aichat/roles/<name>.md` | Merges all prompt fields into one aichat role file |
| `{}` **Export JSON** | Browser download `<name>.json` | Full `chara_card_v2` JSON — compatible with SillyTavern, TavernAI, etc. |

---

## 🏛️ NeXuS

Part of the **NeXuS** sovereign desktop stack — *Sane • Simple • Secure • Stealthy • Beautiful*

> Together Everyone Achieves More

---

## 📬 Contact

Questions, issues, character cards to share?

- **GitHub:** [@hackenstacks](https://github.com/hackenstacks)
- **Email:** [hackenstacks@gmail.com](mailto:hackenstacks@gmail.com)
