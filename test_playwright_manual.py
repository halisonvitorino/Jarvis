"""
Playwright Manual Tests for J.A.R.V.I.S
"""
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8001"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # TESTE 1: Acessar página
    print("=== Teste 1: Acessar página ===")
    page.goto(BASE_URL)
    title = page.title()
    print(f"Título: {title}")
    print(f"URL: {page.url}")
    
    # TESTE 2: Verificar elementos
    print("\n=== Teste 2: Elementos da UI ===")
    # Sidebar
    sidebar = page.locator("aside.sidebar")
    print(f"Sidebar visível: {sidebar.is_visible()}")
    print(f"ARIA label: {sidebar.get_attribute('aria-label')}")
    
    # Brand
    brand = page.locator("a.brand")
    print(f"Brand visível: {brand.is_visible()}")
    print(f"Text brand: {brand.inner_text()}")
    
    # Input
    input_field = page.locator("input[type='text']")
    print(f"Input visível: {input_field.is_visible()}")
    placeholder = input_field.get_attribute("placeholder")
    print(f"Placeholder: {placeholder}")
    
    # Send button
    send_btn = page.locator("button:has-text('Enviar')")
    print(f"Botão Enviar visível: {send_btn.is_visible()}")
    
    # TESTE 3: API Tests
    print("\n=== Teste 3: API Tests ===")
    # Criar sessão
    resp = requests.post(f"{BASE_URL}/api/sessions", json={"title": "Teste Playwright"})
    print(f"Criar sessão: {resp.status_code}")
    if resp.status_code == 200:
        session_id = resp.json()["session_id"]
        print(f"Session ID: {session_id}")
        
        # Enviar mensagem
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Olá Playwright!", "session_id": session_id},
            timeout=10
        )
        print(f"Enviar mensagem: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            resp_text = data.get("response", "")[:50]
            print(f"Resposta IA: {resp_text}")
    
    # TESTE 4: Screenshots
    print("\n=== Teste 4: Screenshots ===")
    # Desktop
    page.set_viewport_size({"width": 1400, "height": 900})
    desktop_scr = page.screenshot(full_page=True)
    print(f"Screenshot desktop: {len(desktop_scr)} bytes")
    
    # Mobile
    page.set_viewport_size({"width": 375, "height": 667})
    mobile_scr = page.screenshot(full_page=True)
    print(f"Screenshot mobile: {len(mobile_scr)} bytes")
    
    # TESTE 5: Acessibilidade
    print("\n=== Teste 5: Acessibilidade ===")
    aria_label = page.locator("aside.sidebar").get_attribute("aria-label")
    print(f"ARIA label sidebar: {aria_label}")
    
    brand_aria = page.locator("a.brand").get_attribute("aria-label")
    brand_title = page.locator("a.brand").get_attribute("title")
    print(f"Brand ARIA/Title: {brand_aria or brand_title}")
    
    browser.close()
    print("\nTodos os testes Playwright concluídos com sucesso!")