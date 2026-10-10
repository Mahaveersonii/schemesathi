"""Screenshots of the running app for the report and slides (needs: pip install playwright; app on :8510).

    python docs/take_screens.py            # add --chat to also ask the agent one question (uses Groq)
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "screens"
OUT.mkdir(exist_ok=True)
URL = "http://localhost:8510"


def ready(page):
    page.wait_for_selector(".hero", timeout=60000)
    page.wait_for_timeout(2500)


def persona(page, name):
    page.get_by_role("button", name=name).first.click() if page.get_by_role("button", name=name).count() else \
        page.get_by_text(name, exact=True).first.click()
    page.wait_for_timeout(2500)


def tab(page, label):
    page.get_by_role("tab", name=label).click()
    page.wait_for_timeout(2000)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    page.goto(URL)
    ready(page)
    page.screenshot(path=OUT / "home.png")
    persona(page, "Sunita")
    page.screenshot(path=OUT / "sunita.png")
    page.get_by_text("Not eligible (and why)").click()
    page.wait_for_timeout(2000)
    page.mouse.wheel(0, 700)
    page.wait_for_timeout(800)
    page.screenshot(path=OUT / "why_not.png")
    page.mouse.wheel(0, -3000)
    persona(page, "Fatima")
    tab(page, "📋 Document checklist")
    page.mouse.wheel(0, 600)
    page.wait_for_timeout(800)
    page.screenshot(path=OUT / "documents.png")
    page.mouse.wheel(0, -3000)
    tab(page, "🔎 Explore all schemes")
    page.get_by_label("Search the official text of all schemes").fill("loan without collateral for street vendors")
    page.keyboard.press("Enter")
    page.wait_for_timeout(4000)
    page.mouse.wheel(0, 600)
    page.wait_for_timeout(800)
    page.screenshot(path=OUT / "explore.png")
    page.mouse.wheel(0, -3000)
    tab(page, "⚙️ Under the hood")
    page.mouse.wheel(0, 650)
    page.wait_for_timeout(1500)
    page.screenshot(path=OUT / "hood.png")
    if "--chat" in sys.argv:
        page.mouse.wheel(0, -3000)
        persona(page, "Ramesh")
        tab(page, "💬 Ask SchemeSathi")
        page.get_by_placeholder("Ask about any scheme, in English or Hindi").fill(
            "Which schemes should I apply for first, and what documents do I need?")
        page.keyboard.press("Enter")
        page.wait_for_selector(".meta", timeout=240000)
        page.wait_for_timeout(1500)
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(800)
        page.screenshot(path=OUT / "chat.png")
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(800)
        page.screenshot(path=OUT / "chat2.png")
    b.close()
print("saved to", OUT)
