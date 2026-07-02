# ⬡ NeXuS PNG² Editor

> View, edit, and export AI character cards — straight from your desktop.

A lightweight web app for reading and editing **chara_card_v2** PNG files (TavernAI / SillyTavern / Character Card Architect format). Built for the NeXuS stack — runs locally, no cloud, no tracking.

---

## ✨ Features

- 🖼️ **Visual card browser** — grid of all your PNG character cards with portraits
- ✏️ **Full field editor** — name, description, personality, scenario, system prompt, first message, tags, and more
- 💾 **Save back to PNG** — writes edits into the PNG `tEXt` chunk non-destructively (image unchanged)
- ⬡ **One-click aichat export** — exports any card as a role to `~/.config/aichat/roles/`
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

Then open **http://localhost:7420** in your browser.

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

## 🔗 aichat Integration

Clicking **Export → aichat Role** writes a `.md` role file to your aichat roles directory. The role merges `description`, `personality`, `scenario`, `system_prompt`, and `post_history_instructions` into a single coherent system prompt.

Start the aichat server and your character appears in the Role dropdown immediately:

```bash
aichat --serve
# open http://localhost:8000/playground → Role dropdown
```

---

## 🏛️ NeXuS

Part of the **NeXuS** sovereign desktop stack — *Sane • Simple • Secure • Stealthy • Beautiful*

> Together Everyone Achieves More
