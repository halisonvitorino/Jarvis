#!/usr/bin/env python
"""Run Phase 1 tests with Playwright"""
import subprocess
import sys
import time
import json
import os
import requests
from playwright.sync_api import sync_playwright

def main():
    print("=" * 60)
    print("J.A.R.V.I.S - Phase 1 Regression Tests with Playwright")
    print("=" * 60)
    
    # Start the server
    print("\n[1/5] Iniciando servidor J.A.R.V.I.S...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "jarvis.core:app", "--host", "127.0.0.1", "--port", "8001"],
        cwd="C:\\Users\\halis\\Desenvolvimento\\Jarvis",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("   Aguardando servidor iniciar...")
    time.sleep(5)
    
    # Check if server is up
    server_up = False
    for attempt in range(10):
        try:
            resp = requests.get("http://127.0.0.1:8001/api/sessions", timeout=3)
            if resp.status_code == 200:
                server_up = True
                print("  OK Servidor J.A.R.V.I.S inicializado com sucesso na porta 8001")
                break
        except:
            time.sleep(1)
    
    if not server_up:
        print("  X Servidor nao inicializou. Encerrando.")
        server_proc.terminate()
        return 1
    
    # Run Playwright tests
    print("\n[2/5] Executando testes Playwright...")
    test_file = "tests/test_browser_qa.py"
    
    # Run specific test categories
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v", "-k", "api or smoke"],
        cwd="C:\\Users\\halis\\Desenvolvimento\\Jarvis",
        capture_output=True,
        text=True
    )
    
    print("\n" + "=" * 60)
    print("RESULTADOS DOS TESTES")
    print("=" * 60)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Make screenshots with Playwright
    print("\n[3/5] Fazendo capturadas de tela com Playwright...")
    
    BASE_URL = "http://localhost:8001"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Test 1: Navigate and check page
        page = browser.new_page()
        print("   - Navegando ate pagina inicial...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        title = page.title()
        print(f"     Titulo: {title}")
        print(f"     URL: {page.url}")
        
        # Test 2: Check UI elements
        print("   - Verificando elementos da UI...")
        sidebar = page.locator("aside.sidebar")
        sb_vis = sidebar.is_visible()
        print(f"     Sidebar visivel: {sb_vis}")
        sb_aria = sidebar.get_attribute('aria-label')
        print(f"     ARIA label: {sb_aria}")
        
        brand = page.locator("a.brand")
        b_vis = brand.is_visible()
        print(f"     Brand visivel: {b_vis}")
        b_text = brand.inner_text()
        print(f"     Text brand: {b_text}")
        
        # Test 3: Take screenshots
        print("   - Capturando print de tela...")
        
        # Desktop
        page.set_viewport_size({"width": 1400, "height": 900})
        desktop_scr = page.screenshot(full_page=True)
        print(f"     Desktop: {len(desktop_scr)} bytes")
        
        # Mobile
        page.set_viewport_size({"width": 375, "height": 667})
        mobile_scr = page.screenshot(full_page=True)
        print(f"     Mobile: {len(mobile_scr)} bytes")
        
        # Test: Accessibility
        print("   - Verificando acessibilidade...")
        aria_label = page.locator("aside.sidebar").get_attribute("aria-label")
        print(f"     ARIA label sidebar: {aria_label}")
        
        brand_aria = page.locator("a.brand").get_attribute("aria-label")
        brand_title = page.locator("a.brand").get_attribute("title")
        ba = brand_aria or brand_title
        print(f"     Brand ARIA/Title: {ba}")
        
        browser.close()
    
    # Stop server
    print("\n[4/5] Encerrando servidor...")
    server_proc.terminate()
    server_proc.wait(timeout=5)
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUIDOS")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())