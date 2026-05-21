"""Streamlit UI - «Сверка», генератор контрольных. Дизайн v2: alpine signal."""
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

import streamlit as st

from backend.exporters.docx_exporter import students_docx_bytes, teacher_docx_bytes
from backend.llm.generator import GenerationError, generate_worksheet, regenerate_task
from backend.models import GenerationRequest, WorkSheet
from backend.storage import save_worksheet
from backend.validators.math_validator import validate_task_math

st.set_page_config(
    page_title="Сверка - генератор контрольных",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- стили ----------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500&display=swap');

:root {
  --green: #21A038;
  --green-dark: #0F8A29;
  --green-soft: #E8F7EC;
  --amber: #C77A0F;
  --amber-soft: #FEF3C7;
  --ink: #0A0B0E;
  --ink-2: #3F4147;
  --muted: #5B6470;
  --hint: #C9CDD3;
  --line: #E8EAEC;
  --hair: #F1F3F5;
  --surface: #FFFFFF;
}

html, body, .stApp, [class*="css"], button, input, textarea, select {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  color: var(--ink);
}

/* всё, что хром Streamlit */
#MainMenu, header[data-testid="stHeader"], footer { display:none !important; }
.stDeployButton { display:none !important; }

.stApp { background: var(--surface); }
.main .block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* мини-каркас main */
.app-main {
  padding: 48px 64px 64px;
  max-width: 1400px;
  margin: 0 auto;
}
@media (max-width: 1100px) {
  .app-main { padding: 32px 28px 48px; }
}

/* типографика */
.mono-caps {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.mono-caps.ink { color: var(--ink); }
.mono { font-family: 'JetBrains Mono', monospace; font-weight: 500; }

.eyebrow {
  display:flex; align-items:center; gap:10px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500; font-size: 11px;
  color: var(--ink); letter-spacing: 0.18em; text-transform: uppercase;
}
.eyebrow::before {
  content:""; display:block; width:24px; height:1px; background: var(--ink);
}

/* шапка приложения */
.topbar {
  display:flex; align-items:center; justify-content:space-between;
  padding: 28px 64px;
  border-bottom: 1px solid var(--line);
}
.topbar .left { display:flex; align-items:baseline; gap:14px; }
.brand {
  font-family: 'Inter'; font-weight: 900; font-size: 22px;
  letter-spacing: -0.04em; color: var(--ink);
}
.brand-sub {
  font-family: 'JetBrains Mono', monospace; font-weight: 500;
  font-size: 10px; color: var(--muted); letter-spacing: 0.16em;
  text-transform: uppercase;
}
.topbar .right { display:flex; align-items:center; gap:18px; }
.status-saved {
  display:flex; align-items:center; gap:6px;
  font-family: 'JetBrains Mono', monospace; font-weight: 500;
  font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase;
}
.status-saved .dot {
  width:5px; height:5px; border-radius:50%; background: var(--green);
}
.status-saved.warn { color: var(--amber); }
.status-saved.warn .dot { background: var(--amber); }
.topbar .who {
  font-family: 'Inter'; font-weight: 500; font-size: 13px; color: var(--ink);
}
.topbar .div {
  width:1px; height:14px; background: var(--line);
}

/* ------- HERO (empty state) ------- */
.hero-headline {
  font-family: 'Inter'; font-weight: 900;
  font-size: 76px; line-height: 80px; letter-spacing: -0.045em;
  color: var(--ink);
  margin: 32px 0 36px;
}
@media (max-width: 1100px) {
  .hero-headline { font-size: 52px; line-height: 56px; }
}
.hero-headline .row { display:flex; align-items:flex-start; gap:22px; flex-wrap:wrap; }
.hero-mark { display:flex; flex-direction:column; position:relative; }
.hero-mark svg {
  margin-top:-6px; width:100%; height:14px;
  display:block;
}
.hero-lede {
  font-family: 'Inter'; font-weight: 400;
  font-size: 18px; line-height: 30px;
  color: var(--ink-2);
  max-width: 580px;
}

/* ------- topics list (empty state) ------- */
.topics {
  margin-top: 64px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
}
.topics-head {
  display:flex; align-items:baseline; justify-content:space-between;
  margin-bottom: 12px;
}
.topics-head .hint {
  font-family: 'Inter'; font-weight: 400; font-size: 12px; color: var(--muted);
}
.topic {
  display:flex; align-items:center; gap:24px;
  padding: 18px 0;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
}
.topic .num {
  font-family: 'JetBrains Mono', monospace; font-weight: 500;
  font-size: 12px; color: var(--muted); letter-spacing: 0.04em;
  width: 36px; flex-shrink: 0;
}
.topic .title {
  font-family: 'Inter'; font-weight: 500;
  font-size: 20px; color: var(--ink); letter-spacing: -0.015em;
  flex: 1; line-height: 28px;
}
.topic .grade, .topic .book {
  font-family: 'Inter'; font-weight: 500;
  font-size: 12px; color: var(--muted);
  flex-shrink: 0;
}
.topic .grade { width: 80px; }
.topic .book { width: 140px; text-align: right; }
.topic .arrow {
  width:14px; height:14px; flex-shrink:0;
}

/* ------- метрики (results) ------- */
.metrics {
  display:flex; align-items:flex-end; justify-content:space-between;
  gap: 64px;
  padding: 32px 0;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--line);
}
.metric-quality {
  display:flex; align-items:flex-end; gap: 24px;
}
.metric-quality .num {
  display:flex; align-items:baseline;
  font-family: 'Inter'; font-weight: 900;
  font-size: 140px; line-height: 120px;
  letter-spacing: -0.06em; color: var(--ink);
}
.metric-quality .num .pct {
  font-family: 'Inter'; font-weight: 700; font-size: 48px;
  letter-spacing: -0.04em;
}
.metric-quality .label {
  display:flex; flex-direction:column; gap:6px; padding-bottom: 8px;
}
.metric-quality .label .sub {
  font-family: 'Inter'; font-weight: 500; font-size: 14px;
  color: var(--ink-2); max-width: 240px; line-height: 20px;
}
.metric-stats {
  display:flex; flex-direction:column; gap: 14px;
  flex-shrink:0;
}
.metric-stats .row {
  display:flex; align-items:baseline; gap:16px;
  padding-bottom: 14px; border-bottom: 1px solid var(--line);
}
.metric-stats .row:last-child { border-bottom: none; padding-bottom: 0; }
.metric-stats .num {
  font-family: 'Inter'; font-weight: 700; font-size: 22px;
  color: var(--ink); width: 90px;
}
.metric-stats .num .unit {
  font-family: 'Inter'; font-weight: 500; font-size: 13px; color: var(--muted);
}
.metric-stats .desc {
  font-family: 'Inter'; font-weight: 500; font-size: 14px;
  color: var(--ink-2); width: 240px;
}

/* ------- results heading ------- */
.results-heading {
  margin-top: 12px;
}
.results-heading .title {
  font-family: 'Inter'; font-weight: 900;
  font-size: 44px; line-height: 48px; letter-spacing: -0.03em;
  color: var(--ink); margin-top: 14px;
}
@media (max-width: 1100px) {
  .results-heading .title { font-size: 34px; line-height: 38px; }
}

/* ------- задачи (results) ------- */
.task-row {
  display:flex; align-items:flex-start; gap: 32px;
  padding: 24px 0; border-bottom: 1px solid var(--line);
}
.task-row .num-slot {
  display:flex; flex-direction:column; gap:2px;
  width: 48px; flex-shrink: 0; padding-top: 4px;
}
.task-row .num-slot .lbl {
  font-family: 'JetBrains Mono', monospace; font-weight: 500;
  font-size: 10px; color: var(--muted); letter-spacing: 0.16em;
}
.task-row .num-slot .num {
  font-family: 'Inter'; font-weight: 900;
  font-size: 24px; letter-spacing: -0.04em; color: var(--ink);
}
.task-row.active .num-slot .num,
.task-row.active .num-slot .lbl {
  color: var(--green);
}
.task-row .body {
  display:flex; flex-direction:column; gap:8px; flex:1; min-width:0;
}
.task-row .stmt {
  font-family: 'Inter'; font-weight: 500;
  font-size: 18px; line-height: 26px; color: var(--ink);
  letter-spacing: -0.005em;
}
.task-row .meta {
  display:flex; align-items:baseline; gap: 18px; flex-wrap:wrap;
}
.task-row .meta .pair {
  display:flex; align-items:baseline; gap: 8px;
}
.task-row .meta .k {
  font-family: 'JetBrains Mono', monospace; font-weight: 500;
  font-size: 10px; color: var(--muted); letter-spacing: 0.16em;
  text-transform: uppercase;
}
.task-row .meta .v {
  font-family: 'Inter'; font-weight: 700; font-size: 15px; color: var(--ink);
}
.task-row .meta .v.mono {
  font-family: 'JetBrains Mono', monospace; font-weight: 500;
  font-size: 13px; color: var(--ink-2);
}
.task-row .meta .pair.warn .k, .task-row .meta .pair.warn .v.mono {
  color: var(--amber);
}
.task-row .status-slot {
  display:flex; align-items:center; gap:8px;
  width: 140px; flex-shrink:0; justify-content:flex-end; padding-top: 8px;
}
.task-row .status-slot .dot {
  width:6px; height:6px; border-radius:50%; background: var(--green);
}
.task-row .status-slot .text {
  font-family: 'Inter'; font-weight: 600; font-size: 13px; color: var(--green);
}
.task-row .status-slot.warn .dot { background: var(--amber); }
.task-row .status-slot.warn .text { color: var(--amber); }
.task-row .expand {
  padding: 0 0 24px 80px;
  display:flex; gap: 32px; align-items:flex-start;
  border-bottom: 1px solid var(--line);
}
.task-row .expand .solution {
  display:flex; flex-direction:column; gap: 10px; flex:1;
}
.task-row .expand .criteria {
  display:flex; flex-direction:column; gap: 10px;
  width: 360px; flex-shrink: 0;
  padding-left: 32px; border-left: 1px solid var(--line);
}
.task-row .expand .body {
  font-family: 'Inter'; font-weight: 400;
  font-size: 14px; line-height: 22px; color: var(--ink);
}

/* действия (кнопки-иконки в строке) */
.action-slot {
  display:flex; align-items:center; gap:4px;
  width: 72px; flex-shrink:0; justify-content:flex-end; padding-top: 6px;
}

/* ------- варианты-табы ------- */
.stTabs [data-baseweb="tab-list"] {
  gap: 36px;
  background: transparent;
  padding: 0;
  border-bottom: 1px solid var(--line);
  margin-top: 8px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0 0 14px 0 !important;
  margin-bottom: -1px;
  font-family: 'Inter' !important;
  height: auto !important;
}
.stTabs [data-baseweb="tab"] p {
  font-family: 'Inter' !important;
  font-weight: 600 !important;
  font-size: 28px !important;
  letter-spacing: -0.04em !important;
  color: var(--hint) !important;
  margin: 0 !important;
}
.stTabs [aria-selected="true"] {
  border-bottom: 2px solid var(--ink) !important;
}
.stTabs [aria-selected="true"] p {
  color: var(--ink) !important;
  font-weight: 900 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
  display: none !important;
}
.stTabs [data-baseweb="tab-panel"] {
  padding-top: 8px !important;
}

/* ------- кнопки ------- */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--green) !important;
  border: none !important;
  color: white !important;
  font-family: 'Inter' !important;
  font-weight: 700 !important;
  font-size: 15px !important;
  border-radius: 6px !important;
  padding: 14px 22px !important;
  letter-spacing: -0.01em !important;
  box-shadow: none !important;
  transition: background 0.12s ease !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--green-dark) !important;
}

.stButton > button[kind="secondary"],
.stButton > button[data-testid="stBaseButton-secondary"] {
  background: var(--surface) !important;
  border: 1px solid var(--line) !important;
  color: var(--ink) !important;
  font-family: 'Inter' !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  border-radius: 6px !important;
  padding: 10px 16px !important;
  box-shadow: none !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--ink) !important;
}

[data-testid="stDownloadButton"] button,
.stDownloadButton button {
  background: var(--surface) !important;
  border: 1px solid var(--ink) !important;
  color: var(--ink) !important;
  font-family: 'Inter' !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  border-radius: 6px !important;
  padding: 14px 18px !important;
  box-shadow: none !important;
}
[data-testid="stDownloadButton"] button:hover,
.stDownloadButton button:hover {
  background: var(--ink) !important;
  color: var(--surface) !important;
}
.dl-teacher + [data-testid="stDownloadButton"] button,
.dl-teacher ~ * [data-testid="stDownloadButton"] button,
.dl-teacher [data-testid="stDownloadButton"] button {
  background: var(--ink) !important;
  color: var(--surface) !important;
  font-weight: 600 !important;
}

/* ------- сайдбар: ничего лишнего, всё на белом ------- */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--line) !important;
}
section[data-testid="stSidebar"] > div { padding: 28px 32px; }

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
  font-family: 'Inter' !important;
  font-weight: 700 !important;
  font-size: 22px !important;
  letter-spacing: -0.02em !important;
  color: var(--ink) !important;
  margin: 0 !important;
}

section[data-testid="stSidebar"] label p {
  font-family: 'Inter' !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  color: var(--muted) !important;
  margin-bottom: 4px !important;
}

/* инпуты */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  border-radius: 6px !important;
  border: 1px solid var(--line) !important;
  background: var(--surface) !important;
  font-family: 'Inter' !important;
  font-size: 14px !important;
  color: var(--ink) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 3px rgba(33,160,56,0.10) !important;
}

/* слайдер - графитовый */
.stSlider [data-baseweb="slider"] [role="slider"] {
  background-color: var(--ink) !important;
  border: 2px solid var(--ink) !important;
  box-shadow: none !important;
}
.stSlider [data-baseweb="slider"] > div > div > div > div {
  background: var(--ink) !important;
}

/* radio */
.stRadio label p { font-size: 14px !important; color: var(--ink) !important; font-weight: 500 !important; }

/* alerts */
.stAlert {
  border-radius: 6px !important;
  border: 1px solid var(--line) !important;
  background: var(--surface) !important;
}

/* expander как строка задачи */
.stExpander {
  border: none !important;
  border-bottom: 1px solid var(--line) !important;
  border-radius: 0 !important;
  background: transparent !important;
  margin: 0 !important;
  box-shadow: none !important;
}
.stExpander summary {
  padding: 0 !important;
  font-family: 'Inter' !important;
}
.stExpander summary:hover {
  background: transparent !important;
}
.stExpander [data-testid="stExpanderDetails"] {
  padding: 0 0 24px 80px !important;
}

/* убрать stHorizontalBlock white-space */
hr { border-color: var(--line) !important; margin: 0 !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------- состояние ----------
if "worksheet" not in st.session_state:
    st.session_state.worksheet = None
if "stats" not in st.session_state:
    st.session_state.stats = None
if "active_variant_idx" not in st.session_state:
    st.session_state.active_variant_idx = 0


# ---------- SIDEBAR (форма параметров) ----------
with st.sidebar:
    st.markdown(
        '<div class="mono-caps ink" style="margin-bottom:4px">Параметры</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Опишите контрольную")
    st.markdown(
        '<div style="height:24px;border-bottom:1px solid #E8EAEC;margin-bottom:18px"></div>',
        unsafe_allow_html=True,
    )

    subject = st.selectbox("Предмет", ["математика"])
    grade = st.number_input("Класс", min_value=1, max_value=11, value=5)
    topic = st.text_input("Тема", "Сложение и вычитание десятичных дробей")
    variants_count = st.slider("Вариантов", 1, 8, 4)
    tasks_per_variant = st.slider("Задач в варианте", 1, 10, 5)
    difficulty = st.slider("Сложность", 1, 5, 3)
    audience_label = st.radio(
        "Аудитория",
        ["Стандартный класс", "Базовый - для отстающих", "Продвинутый - для сильных"],
        index=0,
    )
    audience = {
        "Стандартный класс": "standard",
        "Базовый - для отстающих": "weak",
        "Продвинутый - для сильных": "strong",
    }[audience_label]
    notes = st.text_area("Уточнения", "", height=68, placeholder="Например: только текстовые задачи")
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    generate_btn = st.button("Сгенерировать", type="primary", use_container_width=True)
    st.markdown(
        '<div style="margin-top:12px;font-family:Inter;font-weight:400;font-size:12px;'
        'color:#5B6470;line-height:18px">~28&nbsp;секунд работы GigaChat. Каждый ответ '
        'перепроверит sympy - задачи с&nbsp;ошибками не&nbsp;попадут в&nbsp;файл.</div>',
        unsafe_allow_html=True,
    )


# ---------- TOPBAR ----------
ws: WorkSheet | None = st.session_state.worksheet
stats = st.session_state.stats

now_str = datetime.now(timezone.utc).strftime("%H:%M")
saved_html = (
    f'<div class="status-saved"><div class="dot"></div>сохранено · {now_str}</div>'
    if ws else
    f'<div class="status-saved" style="color:var(--muted)"><div class="dot" style="background:var(--hint)"></div>черновик</div>'
)
sheet_label = f"контрольная № {abs(hash(ws.topic)) % 900 + 100}" if ws else "новый документ"

topbar_html = (
    '<div class="topbar">'
    '<div class="left">'
    '<div class="brand">Сверка</div>'
    f'<div class="brand-sub">{sheet_label}</div>'
    '</div>'
    '<div class="right">'
    f'{saved_html}'
    '<div class="div"></div>'
    '<div class="who">Школа № 57, Мария&nbsp;К.</div>'
    '</div></div>'
)
st.markdown(topbar_html, unsafe_allow_html=True)


st.markdown('<div class="app-main">', unsafe_allow_html=True)


# ---------- GENERATE ----------
if generate_btn:
    req = GenerationRequest(
        subject=subject,
        grade=grade,
        topic=topic,
        variants_count=variants_count,
        tasks_per_variant=tasks_per_variant,
        difficulty=difficulty,
        audience=audience,
        notes=notes or None,
    )
    with st.spinner("Генерируем и сверяем…"):
        try:
            ws_new, stats_new = generate_worksheet(req)
        except GenerationError as e:
            st.error(f"Не получилось сгенерировать: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.stop()
    name = f"{ws_new.subject}_{ws_new.grade}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    save_worksheet(ws_new, name)
    st.session_state.worksheet = ws_new
    st.session_state.stats = stats_new
    st.session_state.active_variant_idx = 0
    ws = ws_new
    stats = stats_new
    st.rerun()


# =====================================================
#                  EMPTY STATE
# =====================================================
if ws is None:
    arrow_svg = ('<svg class="arrow" viewBox="0 0 14 14" fill="none">'
                 '<path d="M3 7h8M7 3l4 4-4 4" stroke="#0A0B0E" stroke-width="1.5" '
                 'stroke-linecap="round" stroke-linejoin="round"/></svg>')
    topics_data = [
        ("Действия с десятичными дробями", 5, 28),
        ("Умножение десятичных дробей", 5, 34),
        ("Сравнение обыкновенных дробей", 6, 10),
        ("Линейные уравнения с одной переменной", 6, 43),
    ]
    topics_html = "".join(
        f'<div class="topic"><div class="num">{n:02d}</div>'
        f'<div class="title">{title}</div>'
        f'<div class="grade">{grade_}&nbsp;класс</div>'
        f'<div class="book">Виленкин · §{para}</div>{arrow_svg}</div>'
        for n, (title, grade_, para) in enumerate(topics_data, 1)
    )

    hero_html = (
        '<div class="eyebrow" style="margin-top:32px">'
        'Генератор контрольных · математика, 5-6 класс</div>'
        '<div class="hero-headline">Четыре варианта, сверенных по&nbsp;числу.</div>'
        '<div class="hero-lede">Учитель тратит на&nbsp;четыре варианта около сорока '
        'минут. Мы&nbsp;собираем их за&nbsp;полминуты: GigaChat пишет, sympy '
        'перепроверяет, в&nbsp;печать не&nbsp;уходит ничего с&nbsp;ошибкой.</div>'
        '<div class="topics">'
        '<div class="topics-head">'
        '<div class="mono-caps ink">Готовые темы</div>'
        '<div class="hint">или впишите свою в&nbsp;поле слева</div>'
        '</div>'
        f'{topics_html}'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# =====================================================
#                  RESULTS STATE
# =====================================================

# downloads row (right-aligned, above heading)
_, dl_col = st.columns([3, 2])
with dl_col:
    dlcol1, dlcol2 = st.columns(2)
    fname_base = f"{ws.subject}_{ws.grade}_{ws.topic[:30]}"
    with dlcol1:
        st.download_button(
            "⬇  Варианты .docx",
            data=students_docx_bytes(ws),
            file_name=f"{fname_base}_варианты.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with dlcol2:
        st.markdown('<div class="dl-teacher">', unsafe_allow_html=True)
        st.download_button(
            "⬇  Ключи учителя .docx",
            data=teacher_docx_bytes(ws),
            file_name=f"{fname_base}_ключи.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

# heading - full width
heading_html = (
    '<div class="eyebrow" style="margin-top:8px">'
    f'{ws.subject}, {ws.grade}&nbsp;класс · вариантов&nbsp;{len(ws.variants)} '
    f'· задач&nbsp;{stats.total_tasks}'
    '</div>'
    '<div class="results-heading">'
    f'<div class="title">{ws.topic}</div>'
    '</div>'
)
st.markdown(heading_html, unsafe_allow_html=True)


# метрики
quality_pct = int(round(stats.first_pass_rate * 100))
regen_word = 'задача регенерирована' if stats.regenerated == 1 else 'задач регенерировано'
metrics_html = (
    '<div class="metrics">'
    '<div class="metric-quality">'
    f'<div class="num">{quality_pct}<span class="pct">%</span></div>'
    '<div class="label">'
    '<div class="mono-caps ink">Качество</div>'
    '<div class="sub">Задач, прошедших проверку sympy с&nbsp;первого раза</div>'
    '</div></div>'
    '<div class="metric-stats">'
    '<div class="row">'
    f'<div class="num">{stats.elapsed_seconds:.0f}&nbsp;<span class="unit">сек</span></div>'
    '<div class="desc">время генерации</div>'
    '</div>'
    '<div class="row">'
    f'<div class="num">{stats.regenerated}</div>'
    f'<div class="desc">{regen_word}</div>'
    '</div>'
    '<div class="row">'
    f'<div class="num">{stats.total_tasks}</div>'
    f'<div class="desc">всего задач, {len(ws.variants)} × {len(ws.variants[0].tasks)}</div>'
    '</div></div></div>'
)
st.markdown(metrics_html, unsafe_allow_html=True)


# варианты - табы
tab_labels = [f"Вариант  {v.number:02d}" for v in ws.variants]
tabs = st.tabs(tab_labels)
for tab, variant in zip(tabs, ws.variants):
    with tab:
        # сводка варианта
        ok_count = sum(1 for t in variant.tasks if not validate_task_math(t))
        warn_count = len(variant.tasks) - ok_count
        if warn_count == 0:
            summary = f'<span style="color:var(--muted)">{ok_count}/{len(variant.tasks)} верно</span>'
        else:
            summary = (
                f'<span style="color:var(--amber);font-weight:600">{warn_count} на проверке</span> · '
                f'<span style="color:var(--muted)">{ok_count} верно</span>'
            )
        st.markdown(
            f'<div class="mono-caps" style="margin:14px 0 4px">'
            f'Задач в&nbsp;варианте: {len(variant.tasks)} · {summary}'
            f'</div>',
            unsafe_allow_html=True,
        )

        for idx, task in enumerate(variant.tasks):
            issues = validate_task_math(task)
            status_class = "warn" if issues else ""
            status_text = "На&nbsp;проверке" if issues else "Сверено"
            expr_class = "warn" if issues else ""
            key_base = f"v{variant.number}_t{idx}"

            expr_text = task.expression or '-'
            if issues:
                expr_text = f"{expr_text} · {issues[0]}"
            row_html = (
                f'<div class="task-row {status_class}">'
                '<div class="num-slot">'
                '<div class="lbl">№</div>'
                f'<div class="num">{idx + 1:02d}</div>'
                '</div>'
                '<div class="body">'
                f'<div class="stmt">{task.statement}</div>'
                '<div class="meta">'
                '<div class="pair">'
                '<div class="k">Ответ</div>'
                f'<div class="v">{task.answer}</div>'
                '</div>'
                f'<div class="pair {expr_class}">'
                '<div class="k">sympy</div>'
                f'<div class="v mono">{expr_text}</div>'
                '</div></div></div>'
                f'<div class="status-slot {status_class}">'
                '<div class="dot"></div>'
                f'<div class="text">{status_text}</div>'
                '</div></div>'
            )
            st.markdown(row_html, unsafe_allow_html=True)

            # editor inline
            with st.expander("Открыть редактор", expanded=False):
                ec1, ec2 = st.columns([1, 2])
                with ec1:
                    new_answer = st.text_input("Ответ", task.answer, key=f"{key_base}_an")
                    new_expression = st.text_input(
                        "Выражение для sympy", task.expression or "", key=f"{key_base}_ex"
                    )
                with ec2:
                    new_statement = st.text_area(
                        "Условие", task.statement, key=f"{key_base}_st", height=80
                    )
                    new_solution = st.text_area(
                        "Решение", task.solution, key=f"{key_base}_sol", height=100
                    )
                new_criteria = st.text_area(
                    "Критерии оценки", task.grading_criteria, key=f"{key_base}_cr", height=68
                )

                bcol1, bcol2, _ = st.columns([1, 1, 4])
                with bcol1:
                    if st.button("Сохранить", key=f"{key_base}_save", use_container_width=True):
                        task.statement = new_statement
                        task.answer = new_answer
                        task.expression = new_expression or None
                        task.solution = new_solution
                        task.grading_criteria = new_criteria
                        st.rerun()
                with bcol2:
                    if st.button(
                        "Перегенерировать",
                        key=f"{key_base}_regen",
                        use_container_width=True,
                    ):
                        with st.spinner("Запрашиваем замену у GigaChat…"):
                            try:
                                regenerate_task(
                                    ws,
                                    variant_number=variant.number,
                                    task_index=idx,
                                    reason="ручной запрос пользователя",
                                )
                                st.rerun()
                            except GenerationError as e:
                                st.error(str(e))


st.markdown('</div>', unsafe_allow_html=True)  # /.app-main
