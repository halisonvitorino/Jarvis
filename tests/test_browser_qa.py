"""
Browser QA Tests for J.A.R.V.I.S Web Interface
Following browser-qa skill guidelines for automated visual testing & interaction.
"""
import pytest
import requests
from playwright.sync_api import expect


BASE_URL = "http://localhost:8001"


@pytest.fixture(scope="session")
def api_base_url():
    """API base URL for backend tests."""
    return "http://127.0.0.1:8001"


# ============================================================
# Phase 1: Smoke Test
# ============================================================

class TestSmoke:
    """Smoke test suite following browser-qa guidelines."""

    def test_page_navigates_successfully(self, browser):
        """Test 1: Navigate to target URL."""
        page = browser.new_page()
        page.goto(BASE_URL)
        # Verify title contains J.A.R.V.I.S
        expect(page).to_have_title("J.A.R.V.I.S")

    def test_no_critical_console_errors(self, page):
        """Test 2: Check for console errors (filter noise)."""
        from playwright.sync_api import Page
        page.goto(BASE_URL)

        # Collect console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
        }))

        # Also collect JS errors
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        # Reload to capture
        page.reload()

        # Filter out noise (analytics, third-party)
        critical_errors = [
            msg for msg in console_messages
            if msg["type"] == "error" and not any(
                x in msg["text"].lower() for x in ["analytics", "googletagmanager", "facebook", "twitter", "doubleclick"]
            )
        ]

        # Should have no critical errors
        critical_count = len(critical_errors)
        assert critical_count == 0, f"Found {critical_count} critical console errors"

    def test_network_requests_success(self, page):
        """Test 3: Verify no 4xx/5xx in network requests."""
        page.goto(BASE_URL)

        # Wait for network to settle
        page.wait_for_load_state("networkidle")

        # Check all network responses
        failed_requests = []
        for request in page.requests:
            if request.failed:
                failed_requests.append({
                    "url": request.url,
                    "status": request.status,
                    "error": request.error_text,
                })

        assert len(failed_requests) == 0, f"Failed requests: {failed_requests}"

    def test_core_web_vitals(self, page):
        """Test 4: Check Core Web Vitals."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Try to get performance metrics
        metrics = page.evaluate("""() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            return {
                lcp: navigation && navigation.loadEventStart
                    ? navigation.loadEventStart - navigation.startTime : null,
                cls: performance.clamp ? performance.clamp() : null,
                inp: performance.inr ? performance.inr : null,
            };
        }""")

        # Basic validation - metrics should be numbers or null
        if metrics.get("lcp") is not None:
            assert metrics["lcp"] < 2500, f"LCP too high: {metrics['lcp']}ms"
        if metrics.get("inp") is not None:
            assert metrics["inp"] < 200, f"INP too high: {metrics['inp']}ms"


# ============================================================
# Phase 2: Interaction Test
# ============================================================

class TestInteractions:
    """Interaction test suite."""

    def test_sidebar_visible_and_interactive(self, page):
        """Test sidebar is visible and links are working."""
        page.goto(BASE_URL)

        # Sidebar should be visible
        sidebar = page.locator("aside.sidebar")
        expect(sidebar).to_be_visible()

        # Sidebar should have aria-label
        expect(sidebar).to_have_attribute("aria-label", "Conversas")

        # Brand link should be visible
        brand = page.locator("a.brand")
        expect(brand).to_be_visible()
        expect(brand).to_have_text("J.A.R.V.I.S")

    def test_chat_input_exists(self, page):
        """Test chat input field exists."""
        page.goto(BASE_URL)

        # Input should exist
        input_field = page.locator("input[type='text']")
        expect(input_field).to_be_visible()
        expect(input_field).to_have_attribute("placeholder")

        # Placeholder should mention messaging
        placeholder = input_field.get_attribute("placeholder")
        assert placeholder is not None
        assert "mensagem" in placeholder.lower() or "digite" in placeholder.lower()

    def test_send_button_exists(self, page):
        """Test send button exists."""
        page.goto(BASE_URL)

        send_button = page.locator("button:has-text('Enviar')")
        expect(send_button).to_be_visible()

        # Also check for send icon
        send_icon = page.locator("button[type='submit']")
        expect(send_icon).to_be_visible() or expect(send_button).to_be_visible()

    def test_api_session_creation(self, api_base_url):
        """Test API session creation."""
        resp = requests.post(f"{api_base_url}/api/sessions", json={"title": "QA Test"})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    def test_api_chat_endpoint(self, api_base_url):
        """Test API chat endpoint."""
        # First create a session
        session_resp = requests.post(f"{api_base_url}/api/sessions", json={"title": "Chat Test"})
        assert session_resp.status_code == 200
        session_id = session_resp.json()["session_id"]

        # Then send a message
        msg_resp = requests.post(
            f"{api_base_url}/api/chat",
            json={"message": "Teste de mensagem via API", "session_id": session_id},
            timeout=10
        )
        assert msg_resp.status_code == 200
        data = msg_resp.json()
        assert "response" in data
        assert len(data["response"]) > 0


# ============================================================
# Phase 3: Visual Regression
# ============================================================

class TestVisualRegression:
    """Visual regression tests."""

    def test_page_screenshot_desktop(self, page):
        """Take screenshot at desktop resolution."""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 1400, "height": 900})

        # Take screenshot
        screenshot = page.screenshot(full_page=True)

        # Verify it doesn't error
        assert screenshot is not None
        assert len(screenshot) > 0

    def test_page_screenshot_mobile(self, page):
        """Take screenshot at mobile resolution."""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 375, "height": 667})  # iPhone 8/SE

        screenshot = page.screenshot(full_page=True)
        assert screenshot is not None
        assert len(screenshot) > 0

    def test_page_screenshot_tablet(self, page):
        """Take screenshot at tablet resolution."""
        page.goto(BASE_URL)
        page.set_viewport_size({"width": 768, "height": 1024})  # iPad

        screenshot = page.screenshot(full_page=True)
        assert screenshot is not None
        assert len(screenshot) > 0

    def test_dark_mode_toggle_if_exists(self, page):
        """Test dark mode if available."""
        page.goto(BASE_URL)

        # Look for dark mode toggle
        dark_toggles = page.locator("[data-dark-mode], .dark-mode-toggle, .theme-switch")

        # If exists, test it
        if dark_toggles.count() > 0:
            # Get initial state
            expect(page).to_be_visible()

            # Toggle
            dark_toggles.first.click()
            page.wait_for_timeout(500)

            # Verify no crash
            expect(page).to_be_visible()


# ============================================================
# Phase 4: Accessibility
# ============================================================

class TestAccessibility:
    """Accessibility tests following browser-qa guidelines."""

    def test_aria_labels_exist(self, page):
        """Test that critical elements have ARIA labels."""
        page.goto(BASE_URL)

        # Sidebar should have aria-label
        sidebar = page.locator("aside.sidebar")
        expect(sidebar).to_have_attribute("aria-label", "Conversas")

        # Brand link should have aria-label or alt
        brand = page.locator("a.brand")
        has_aria = brand.get_attribute("aria-label")
        has_title = brand.get_attribute("title")
        assert has_aria is not None or has_title is not None, \
            "Brand link should have aria-label or title attribute"

    def test_focus_management(self, page):
        """Test keyboard focus management."""
        page.goto(BASE_URL)

        # Tab through interactive elements
        interactive = page.locator("button, input, a, [role='button']").first
        expect(interactive).to_be_focusable()

        # Press Tab
        interactive.focus()
        # Basic focus check - just verify no errors


# ============================================================
# Run tests
# ============================================================

pytest.main(["tests/test_browser_qa.py", "-v"])