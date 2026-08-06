"""
BeeNavi – Trợ lý tự động sinh Checklist Du lịch cá nhân hóa.
Tối ưu bởi Antigravity | v2.0
"""

from __future__ import annotations

import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from api_services import calculate_distance, get_location_coordinates, get_realtime_weather
from rule_engine import BeeNaviRuleEngine

# ─────────────────────────────────────────────
# ANSI Color helpers (tắt tự động nếu không hỗ trợ terminal)
# ─────────────────────────────────────────────
_USE_COLOR = sys.stdout.isatty() or os.name == "nt"

def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

RED    = lambda t: _c("91", t)
GREEN  = lambda t: _c("92", t)
YELLOW = lambda t: _c("93", t)
CYAN   = lambda t: _c("96", t)
BOLD   = lambda t: _c("1",  t)
DIM    = lambda t: _c("2",  t)

PRIORITY_COLOR = {
    "Bắt buộc":       RED,
    "Khuyến khích":   YELLOW,
    "Không bắt buộc": GREEN,
}
PRIORITY_ICON = {
    "Bắt buộc":       "🔴",
    "Khuyến khích":   "🟡",
    "Không bắt buộc": "🟢",
}

# ─────────────────────────────────────────────
# Input helpers
# ─────────────────────────────────────────────

def _prompt(msg: str, default: str = "") -> str:
    """Nhắc người dùng nhập. Nếu bỏ trống trả về default."""
    result = input(CYAN(f"  ▸ {msg}")).strip()
    return result if result else default


def _choose(msg: str, options: dict[str, str], default_key: str) -> str:
    """Hiển thị menu lựa chọn, trả về value tương ứng."""
    print(CYAN(f"  ▸ {msg}"))
    for key, label in options.items():
        marker = BOLD("→") if key == default_key else " "
        print(f"      {marker} [{key}] {label}")
    choice = input(CYAN(f"    Chọn ({'/'.join(options.keys())}), mặc định [{default_key}]: ")).strip()
    return options.get(choice, options[default_key])


def _input_int(msg: str, default: int = 2, min_val: int = 1, max_val: int = 30) -> int:
    """Nhập số nguyên với validation."""
    while True:
        raw = _prompt(msg, str(default))
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(RED(f"    ⚠ Vui lòng nhập số từ {min_val} đến {max_val}."))
        except ValueError:
            print(RED("    ⚠ Vui lòng nhập một số nguyên."))


# ─────────────────────────────────────────────
# Terminal Output
# ─────────────────────────────────────────────

def _print_header():
    print()
    print(BOLD(CYAN("  ╔══════════════════════════════════════════════════════════╗")))
    print(BOLD(CYAN("  ║      🧳  BEENAVI – CHECKLIST DU LỊCH CÁ NHÂN HÓA       ║")))
    print(BOLD(CYAN("  ╚══════════════════════════════════════════════════════════╝")))
    print()


def _print_context(dest_name: str, dist_km: float | None,
                   weather: dict, vehicle: str, trip_type: str, days: int):
    sep = DIM("  " + "─" * 58)
    print(sep)
    print(f"  📍 Điểm đến   : {BOLD(dest_name.split(',')[0])}")
    if dist_km:
        print(f"  🛣️  Khoảng cách: ~{BOLD(str(dist_km))} km")
    print(f"  🌤️  Thời tiết  : {weather['temp']}°C, ẩm {weather['humidity']}%  ▸  {BOLD(weather['description'])}")
    _wtag = weather['weather_tag']
    print(f"  🏷️  Tag xác định: {BOLD(YELLOW(f'[{_wtag}]'))}")
    print(f"  🚗 Phương tiện : {vehicle}")
    print(f"  🗺️  Loại hình  : {trip_type}")
    print(f"  📅 Thời gian   : {days} ngày {days - 1} đêm")
    print(sep)
    print()


def _print_checklist(groups: dict, total: int):
    print(BOLD(f"  🎒 DANH SÁCH ĐỒ CẦN CHUẨN BỊ  ({total} món)\n"))
    for category, items in groups.items():
        print(BOLD(f"  📂 {category}"))
        print(DIM("  " + "─" * 56))
        for item in items:
            icon  = PRIORITY_ICON.get(item["priority"], "⚪")
            color = PRIORITY_COLOR.get(item["priority"], lambda x: x)
            name  = item["name"]
            qty   = f"×{item['quantity']}"
            pri   = color(f"[{item['priority']}]")
            print(f"    {icon}  {name:<38} {DIM(qty):<6}  {pri}")
        print()
    print(DIM("  " + "─" * 58))
    bbb = sum(1 for g in groups.values() for i in g if i["priority"] == "Bắt buộc")
    kk  = sum(1 for g in groups.values() for i in g if i["priority"] == "Khuyến khích")
    kbb = sum(1 for g in groups.values() for i in g if i["priority"] == "Không bắt buộc")
    print(f"  {RED('🔴 Bắt buộc')}: {bbb}    {YELLOW('🟡 Khuyến khích')}: {kk}    {GREEN('🟢 Không bắt buộc')}: {kbb}")
    print(f"  ✅ Tổng cộng: {BOLD(str(total))} món đồ cần chuẩn bị.")
    print()


# ─────────────────────────────────────────────
# HTML Output
# ─────────────────────────────────────────────

_PRIORITY_BADGE = {
    "Bắt buộc":       ("badge-required",     "🔴 Bắt buộc"),
    "Khuyến khích":   ("badge-recommended",  "🟡 Khuyến khích"),
    "Không bắt buộc": ("badge-optional",     "🟢 Không bắt buộc"),
}


def _build_html(
    groups: dict,
    total: int,
    weather: dict,
    vehicle: str,
    trip_type: str,
    days: int,
    dest_name: str,
    dist_km: float | None,
    start_name: str,
) -> str:
    generated_at = datetime.now().strftime("%H:%M  %d/%m/%Y")

    # ── Category accordion items ──
    category_html = ""
    cat_icons = {
        "Giấy tờ cá nhân":        "🪪",
        "Thiết bị công nghệ":     "📱",
        "Trang phục":             "👕",
        "Vệ sinh cá nhân":        "🧴",
        "Y tế & Mỹ phẩm":        "💊",
        "Hành lý & Đóng gói":    "🧳",
        "Ăn uống & Thực phẩm":   "🍱",
        "Camping & Trekking":     "⛺",
        "Đồ dùng theo phương tiện": "🔧",
        "Khác":                   "🎲",
    }

    for category, items in groups.items():
        icon = cat_icons.get(category, "📦")
        required_count = sum(1 for i in items if i["priority"] == "Bắt buộc")
        badge_info = f'<span class="cat-badge">{len(items)} món</span>'
        if required_count:
            badge_info += f'<span class="cat-badge required-count">{required_count} bắt buộc</span>'

        rows = ""
        for item in items:
            badge_cls, badge_label = _PRIORITY_BADGE.get(
                item["priority"], ("badge-optional", item["priority"])
            )
            rows += f"""
            <tr class="item-row" data-priority="{item['priority']}">
              <td class="col-check">
                <label class="checkbox-wrap">
                  <input type="checkbox" id="item-{item['id']}" class="item-checkbox">
                  <span class="checkmark"></span>
                </label>
              </td>
              <td class="col-name"><label for="item-{item['id']}">{item['name']}</label></td>
              <td class="col-qty">×{item['quantity']}</td>
              <td class="col-badge"><span class="badge {badge_cls}">{badge_label}</span></td>
            </tr>"""

        category_html += f"""
      <div class="category-block">
        <button class="cat-header" onclick="toggleCat(this)" aria-expanded="true">
          <span class="cat-title">{icon} {category}</span>
          <span class="cat-meta">{badge_info}</span>
          <span class="cat-arrow">▼</span>
        </button>
        <div class="cat-body">
          <table class="checklist-table">
            <tbody>{rows}
            </tbody>
          </table>
        </div>
      </div>"""

    dist_html = f"<span>🛣️ ~{dist_km} km từ {start_name.split(',')[0]}</span>" if dist_km else ""

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>BeeNavi Checklist – {dest_name.split(',')[0]}</title>
  <meta name="description" content="Checklist du lịch cá nhân hóa do BeeNavi tạo tự động dựa trên thời tiết, phương tiện và loại hình chuyến đi."/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
  <style>
    /* ── Reset & Base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg:          #0f1117;
      --surface:     #1a1d27;
      --surface2:    #22263a;
      --border:      #2e3250;
      --accent:      #6c63ff;
      --accent2:     #a78bfa;
      --text:        #e2e8f0;
      --text-muted:  #7a829a;
      --required:    #f87171;
      --recommended: #fbbf24;
      --optional:    #34d399;
      --radius:      14px;
      --shadow:      0 4px 32px rgba(0,0,0,.45);
    }}
    body {{
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 0 0 60px;
    }}

    /* ── Hero header ── */
    .hero {{
      background: linear-gradient(135deg, #1e1b4b 0%, #312e81 45%, #1e40af 100%);
      padding: 40px 24px 32px;
      text-align: center;
      border-bottom: 1px solid #3730a3;
    }}
    .hero-logo {{ font-size: 48px; margin-bottom: 8px; }}
    .hero h1 {{
      font-size: clamp(1.5rem, 4vw, 2.4rem);
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(90deg, #c4b5fd, #818cf8, #60a5fa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 6px;
    }}
    .hero-sub {{ color: #a5b4fc; font-size: .95rem; }}

    /* ── Context card ── */
    .context-bar {{
      max-width: 860px;
      margin: 28px auto 0;
      background: rgba(255,255,255,.06);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: var(--radius);
      padding: 18px 24px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px 24px;
      font-size: .875rem;
      color: #c7d2fe;
    }}
    .context-bar span {{ display: flex; align-items: center; gap: 6px; }}

    /* ── Summary chips ── */
    .summary-chips {{
      max-width: 860px;
      margin: 20px auto 0;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      padding: 0 4px;
    }}
    .chip {{
      display: flex; align-items: center; gap: 6px;
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 99px;
      padding: 5px 14px;
      font-size: .8rem;
      font-weight: 600;
    }}
    .chip.req  {{ border-color: var(--required);    color: var(--required);    }}
    .chip.rec  {{ border-color: var(--recommended); color: var(--recommended); }}
    .chip.opt  {{ border-color: var(--optional);    color: var(--optional);    }}
    .chip.total{{ border-color: var(--accent2);     color: var(--accent2);     }}

    /* ── Progress bar ── */
    .progress-wrap {{
      max-width: 860px;
      margin: 20px auto 0;
      padding: 0 4px;
    }}
    .progress-label {{
      display: flex; justify-content: space-between;
      font-size: .8rem; color: var(--text-muted); margin-bottom: 6px;
    }}
    .progress-bar-bg {{
      height: 8px; background: var(--surface2);
      border-radius: 99px; overflow: hidden;
    }}
    .progress-bar-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      border-radius: 99px;
      transition: width .4s ease;
      width: 0%;
    }}

    /* ── Toolbar ── */
    .toolbar {{
      max-width: 860px; margin: 20px auto 0;
      display: flex; flex-wrap: wrap; gap: 10px;
      padding: 0 4px;
    }}
    .toolbar input[type=text] {{
      flex: 1; min-width: 200px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-family: inherit;
      font-size: .875rem;
      padding: 8px 14px;
      outline: none;
      transition: border-color .2s;
    }}
    .toolbar input[type=text]:focus {{ border-color: var(--accent); }}
    .toolbar select {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      font-family: inherit;
      font-size: .875rem;
      padding: 8px 14px;
      outline: none;
      cursor: pointer;
    }}
    .btn {{
      padding: 8px 18px;
      border-radius: 8px;
      border: none;
      font-family: inherit;
      font-size: .875rem;
      font-weight: 600;
      cursor: pointer;
      transition: all .2s;
    }}
    .btn-primary {{
      background: var(--accent);
      color: #fff;
    }}
    .btn-primary:hover {{ background: #5b52e6; transform: translateY(-1px); }}
    .btn-ghost {{
      background: var(--surface2);
      color: var(--text-muted);
      border: 1px solid var(--border);
    }}
    .btn-ghost:hover {{ color: var(--text); border-color: var(--accent2); }}

    /* ── Main content ── */
    .main {{
      max-width: 860px;
      margin: 28px auto 0;
      padding: 0 4px;
    }}

    /* ── Category block ── */
    .category-block {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      margin-bottom: 16px;
      overflow: hidden;
      transition: box-shadow .2s;
    }}
    .category-block:hover {{ box-shadow: 0 0 0 1px var(--accent); }}
    .cat-header {{
      width: 100%;
      display: flex; align-items: center; gap: 10px;
      background: var(--surface2);
      border: none;
      color: var(--text);
      font-family: inherit;
      font-size: .95rem;
      font-weight: 700;
      padding: 14px 18px;
      cursor: pointer;
      transition: background .2s;
      text-align: left;
    }}
    .cat-header:hover {{ background: #282c44; }}
    .cat-title {{ flex: 1; }}
    .cat-meta {{ display: flex; gap: 8px; }}
    .cat-badge {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 99px;
      font-size: .75rem;
      font-weight: 600;
      padding: 2px 10px;
      color: var(--text-muted);
    }}
    .cat-badge.required-count {{
      border-color: rgba(248,113,113,.4);
      color: var(--required);
    }}
    .cat-arrow {{ font-size: .75rem; color: var(--text-muted); transition: transform .25s; }}
    .cat-header.collapsed .cat-arrow {{ transform: rotate(-90deg); }}
    .cat-body {{ padding: 0 12px 12px; }}
    .cat-body.hidden {{ display: none; }}

    /* ── Checklist table ── */
    .checklist-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }}
    .checklist-table tbody tr {{
      border-bottom: 1px solid var(--border);
      transition: background .15s;
    }}
    .checklist-table tbody tr:last-child {{ border-bottom: none; }}
    .checklist-table tbody tr:hover {{ background: var(--surface2); }}
    .checklist-table td {{ padding: 10px 8px; vertical-align: middle; }}

    .col-check {{ width: 44px; text-align: center; }}
    .col-name  {{ font-size: .9rem; cursor: pointer; }}
    .col-qty   {{ width: 50px; text-align: center; color: var(--text-muted); font-size: .8rem; font-weight: 600; }}
    .col-badge {{ width: 150px; text-align: right; }}

    /* ── Custom checkbox ── */
    .checkbox-wrap {{
      display: inline-flex; align-items: center; justify-content: center;
      cursor: pointer; width: 24px; height: 24px;
    }}
    .checkbox-wrap input {{ display: none; }}
    .checkmark {{
      width: 20px; height: 20px;
      border: 2px solid var(--border);
      border-radius: 6px;
      display: flex; align-items: center; justify-content: center;
      transition: all .2s;
    }}
    .checkbox-wrap input:checked + .checkmark {{
      background: var(--accent);
      border-color: var(--accent);
    }}
    .checkbox-wrap input:checked + .checkmark::after {{
      content: '✓';
      color: white;
      font-size: 13px;
      font-weight: 700;
    }}

    /* Checked item style */
    .item-row.checked .col-name label {{
      text-decoration: line-through;
      color: var(--text-muted);
    }}

    /* Badge */
    .badge {{
      display: inline-block;
      border-radius: 99px;
      padding: 3px 10px;
      font-size: .72rem;
      font-weight: 700;
      letter-spacing: .3px;
    }}
    .badge-required    {{ background: rgba(248,113,113,.15); color: var(--required);    border: 1px solid rgba(248,113,113,.3); }}
    .badge-recommended {{ background: rgba(251,191,36,.12); color: var(--recommended); border: 1px solid rgba(251,191,36,.3); }}
    .badge-optional    {{ background: rgba(52,211,153,.12);  color: var(--optional);    border: 1px solid rgba(52,211,153,.3); }}

    /* ── Hidden item (filter) ── */
    .item-row.hidden-filter {{ display: none; }}

    /* ── Footer ── */
    .footer {{
      max-width: 860px; margin: 32px auto 0;
      text-align: center; color: var(--text-muted); font-size: .8rem;
      padding: 0 4px;
    }}

    /* ── Print ── */
    @media print {{
      body {{ background: #fff; color: #111; }}
      .hero {{ background: #3730a3; -webkit-print-color-adjust: exact; }}
      .toolbar, .btn, .progress-wrap {{ display: none; }}
      .category-block {{ border: 1px solid #ddd; break-inside: avoid; }}
      .cat-body.hidden {{ display: block !important; }}
      .badge-required    {{ background: #fee2e2; color: #b91c1c; }}
      .badge-recommended {{ background: #fef3c7; color: #b45309; }}
      .badge-optional    {{ background: #d1fae5; color: #065f46; }}
    }}

    @media (max-width: 600px) {{
      .hero h1 {{ font-size: 1.4rem; }}
      .col-badge {{ display: none; }}
    }}
  </style>
</head>
<body>

<!-- ── Hero ── -->
<div class="hero">
  <div class="hero-logo">🧳</div>
  <h1>BeeNavi Checklist</h1>
  <p class="hero-sub">Danh sách đồ cần mang – được tạo tự động theo bối cảnh chuyến đi của bạn</p>

  <div class="context-bar">
    <span>📍 <strong>{dest_name.split(',')[0]}</strong></span>
    {dist_html}
    <span>🌤️ {weather['temp']}°C · {weather['description']} · ẩm {weather['humidity']}%</span>
    <span>🏷️ <strong>{weather['weather_tag']}</strong></span>
    <span>🚗 {vehicle}</span>
    <span>🗺️ {trip_type}</span>
    <span>📅 {days} ngày {days - 1} đêm</span>
  </div>
</div>

<!-- ── Summary ── -->
<div class="summary-chips" id="summaryChips">
  <!-- filled by JS -->
</div>

<!-- ── Progress ── -->
<div class="progress-wrap">
  <div class="progress-label">
    <span>Tiến độ chuẩn bị</span>
    <span id="progressText">0 / {total} món</span>
  </div>
  <div class="progress-bar-bg">
    <div class="progress-bar-fill" id="progressFill"></div>
  </div>
</div>

<!-- ── Toolbar ── -->
<div class="toolbar">
  <input type="text" id="searchInput" placeholder="🔍  Tìm kiếm đồ dùng..." oninput="filterItems()"/>
  <select id="priorityFilter" onchange="filterItems()">
    <option value="all">Tất cả mức độ</option>
    <option value="Bắt buộc">🔴 Bắt buộc</option>
    <option value="Khuyến khích">🟡 Khuyến khích</option>
    <option value="Không bắt buộc">🟢 Không bắt buộc</option>
  </select>
  <button class="btn btn-ghost" onclick="expandAll()">Mở rộng tất cả</button>
  <button class="btn btn-ghost" onclick="collapseAll()">Thu gọn tất cả</button>
  <button class="btn btn-ghost" onclick="uncheckAll()">Bỏ tick tất cả</button>
  <button class="btn btn-primary" onclick="window.print()">🖨️ In / Xuất PDF</button>
</div>

<!-- ── Main content ── -->
<div class="main" id="mainContent">
{category_html}
</div>

<div class="footer">
  Tạo bởi BeeNavi lúc {generated_at} &nbsp;·&nbsp;
  🔴 Bắt buộc &nbsp;🟡 Khuyến khích &nbsp;🟢 Không bắt buộc
</div>

<script>
  const TOTAL = {total};
  const checkboxes = () => document.querySelectorAll('.item-checkbox');

  // ── Progress ──
  function updateProgress() {{
    const checked = document.querySelectorAll('.item-checkbox:checked').length;
    const visible = document.querySelectorAll('.item-row:not(.hidden-filter)').length;
    document.getElementById('progressText').textContent = checked + ' / ' + TOTAL + ' món';
    const pct = TOTAL > 0 ? (checked / TOTAL * 100).toFixed(1) : 0;
    document.getElementById('progressFill').style.width = pct + '%';

    // Summary chips
    const req  = document.querySelectorAll('[data-priority="Bắt buộc"]').length;
    const rec  = document.querySelectorAll('[data-priority="Khuyến khích"]').length;
    const opt  = document.querySelectorAll('[data-priority="Không bắt buộc"]').length;
    document.getElementById('summaryChips').innerHTML =
      `<div class="chip total">📦 ${{TOTAL}} món tổng cộng</div>` +
      `<div class="chip req">🔴 ${{req}} Bắt buộc</div>` +
      `<div class="chip rec">🟡 ${{rec}} Khuyến khích</div>` +
      `<div class="chip opt">🟢 ${{opt}} Không bắt buộc</div>` +
      `<div class="chip total">✅ ${{checked}} đã chuẩn bị</div>`;
  }}

  // ── Checkbox events ──
  checkboxes().forEach(cb => {{
    cb.addEventListener('change', () => {{
      cb.closest('.item-row').classList.toggle('checked', cb.checked);
      updateProgress();
    }});
  }});

  // ── Accordion ──
  function toggleCat(btn) {{
    const body  = btn.nextElementSibling;
    const isCol = btn.classList.contains('collapsed');
    btn.classList.toggle('collapsed', !isCol);
    body.classList.toggle('hidden', !isCol);
  }}
  function expandAll()  {{
    document.querySelectorAll('.cat-header').forEach(b => {{
      b.classList.remove('collapsed');
      b.nextElementSibling.classList.remove('hidden');
    }});
  }}
  function collapseAll() {{
    document.querySelectorAll('.cat-header').forEach(b => {{
      b.classList.add('collapsed');
      b.nextElementSibling.classList.add('hidden');
    }});
  }}
  function uncheckAll() {{
    checkboxes().forEach(cb => {{
      cb.checked = false;
      cb.closest('.item-row').classList.remove('checked');
    }});
    updateProgress();
  }}

  // ── Search & Filter ──
  function filterItems() {{
    const q   = document.getElementById('searchInput').value.toLowerCase();
    const pri = document.getElementById('priorityFilter').value;
    document.querySelectorAll('.item-row').forEach(row => {{
      const name    = row.querySelector('.col-name').textContent.toLowerCase();
      const rowPri  = row.dataset.priority;
      const matchQ  = !q || name.includes(q);
      const matchP  = pri === 'all' || rowPri === pri;
      row.classList.toggle('hidden-filter', !(matchQ && matchP));
    }});
  }}

  // Init
  updateProgress();
</script>
</body>
</html>"""


def _save_and_open_html(html: str, dest_short: str) -> Path:
    """Lưu file HTML ra thư mục hiện tại và mở trong browser."""
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in dest_short)
    filename = Path(f"beenavi_checklist_{safe_name}.html")
    filename.write_text(html, encoding="utf-8")
    webbrowser.open(filename.resolve().as_uri())
    return filename


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    _print_header()

    # ── 1. Thu thập input ──────────────────────────────────────────────
    print(BOLD("  [ THÔNG TIN CHUYẾN ĐI ]\n"))

    start_place = _prompt("Điểm xuất phát (VD: Hà Nội): ", "Hà Nội")
    dest_place  = _prompt("Điểm đến      (VD: Đà Lạt):  ", "Đà Lạt")

    print()
    user_vehicle = _choose(
        "Phương tiện di chuyển:",
        {"1": "Xe máy", "2": "Ô tô", "3": "Máy bay", "4": "Xe khách", "5": "Tàu hỏa"},
        default_key="1",
    )

    print()
    user_trip_type = _choose(
        "Loại hình chuyến đi:",
        {"1": "Phượt", "2": "Nghỉ dưỡng", "3": "Camping", "4": "Trekking", "5": "Đô thị"},
        default_key="1",
    )

    print()
    days = _input_int("Số ngày đi (1–30, VD: 3): ", default=3)

    # ── 2. Gọi API ────────────────────────────────────────────────────
    print(f"\n{DIM('  ─' * 29)}")
    print(f"  {CYAN('⟳')} Đang truy vấn dữ liệu vị trí & thời tiết...\n")

    dest_coords  = get_location_coordinates(dest_place)
    start_coords = get_location_coordinates(start_place)

    if not dest_coords:
        print(RED(f"  [!] Không định vị được '{dest_place}'. Dùng tọa độ Hà Nội."))
        dest_coords = {"name": dest_place, "lat": 21.0285, "lon": 105.8542}

    weather  = get_realtime_weather(dest_coords["lat"], dest_coords["lon"])
    dist_km  = calculate_distance(start_coords, dest_coords) if start_coords else None
    dest_name  = dest_coords["name"]
    start_name = start_coords["name"] if start_coords else start_place

    _print_context(dest_name, dist_km, weather, user_vehicle, user_trip_type, days)

    # ── 3. Rule Engine ────────────────────────────────────────────────
    engine  = BeeNaviRuleEngine("dataset_checklist.txt")
    results = engine.filter_checklist(
        weather_tag=weather["weather_tag"],
        vehicle=user_vehicle,
        trip_type=user_trip_type,
        days=days,
    )
    groups = engine.group_by_category(results)

    # ── 4. Terminal output ────────────────────────────────────────────
    _print_checklist(groups, len(results))

    # ── 5. HTML output ────────────────────────────────────────────────
    html = _build_html(
        groups=groups,
        total=len(results),
        weather=weather,
        vehicle=user_vehicle,
        trip_type=user_trip_type,
        days=days,
        dest_name=dest_name,
        dist_km=dist_km,
        start_name=start_name,
    )
    dest_short = dest_place.replace(" ", "_")
    html_file  = _save_and_open_html(html, dest_short)
    print(GREEN(f"  🌐 Checklist tương tác đã mở trong trình duyệt!"))
    print(DIM  (f"     File: {html_file.resolve()}\n"))


if __name__ == "__main__":
    main()