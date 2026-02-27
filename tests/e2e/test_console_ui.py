"""End-to-end tests for Operator Console UI using Playwright."""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the console."""
    return "http://localhost:8007"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Extend browser context with viewport."""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
    }


def test_console_loads(page: Page, base_url: str):
    """Test that the console dashboard loads successfully."""
    page.goto(base_url)

    # Check page title
    expect(page).to_have_title("Project Chimera - Operator Console")

    # Check main sections are visible
    expect(page.locator("#service-status")).to_be_visible()
    expect(page.locator("#event-stream")).to_be_visible()
    expect(page.locator("#approvals")).to_be_visible()
    expect(page.locator("#overrides")).to_be_visible()


def test_service_status_display(page: Page, base_url: str):
    """Test that service status panel displays all 8 services."""
    page.goto(base_url)

    # Wait for service data to load
    page.wait_for_selector("#service-status .service-item", timeout=5000)

    # Check all 8 services are listed
    services = page.locator("#service-status .service-item")
    expect(services).to_have_count(8)

    # Verify service names
    expect(services.nth(0)).to_contain_text("OpenClaw Orchestrator")
    expect(services.nth(1)).to_contain_text("SceneSpeak Agent")
    expect(services.nth(2)).to_contain_text("Captioning Agent")
    expect(services.nth(3)).to_contain_text("BSL-Text2Gloss Agent")
    expect(services.nth(4)).to_contain_text("Sentiment Agent")
    expect(services.nth(5)).to_contain_text("Lighting Control")
    expect(services.nth(6)).to_contain_text("Safety Filter")
    expect(services.nth(7)).to_contain_text("Operator Console")


def test_approval_buttons(page: Page, base_url: str):
    """Test that approval buttons are functional."""
    page.goto(base_url)

    # Find approval section
    approvals = page.locator("#approvals")

    # Check approve button exists and is enabled
    approve_btn = approvals.locator("button#approve-btn")
    expect(approve_btn).to_be_visible()
    expect(approve_btn).to_be_enabled()

    # Check reject button exists and is enabled
    reject_btn = approvals.locator("button#reject-btn")
    expect(reject_btn).to_be_visible()
    expect(reject_btn).to_be_enabled()


def test_override_controls(page: Page, base_url: str):
    """Test that manual override controls work."""
    page.goto(base_url)

    # Find overrides section
    overrides = page.locator("#overrides")

    # Check emergency stop button
    emergency_btn = overrides.locator("button.emergency-stop")
    expect(emergency_btn).to_be_visible()

    # Check pause button
    pause_btn = overrides.locator("button.pause-btn")
    expect(pause_btn).to_be_visible()

    # Check resume button (may be disabled)
    resume_btn = overrides.locator("button.resume-btn")
    expect(resume_btn).to_be_visible()


def test_event_stream(page: Page, base_url: str):
    """Test that event stream displays events."""
    page.goto(base_url)

    # Find event stream section
    event_stream = page.locator("#event-stream")

    # Check that event stream container exists
    expect(event_stream.locator(".event-list")).to_be_visible()

    # Events may be empty initially, but container should exist
    expect(event_stream.locator("h2")).to_contain_text("Live Events")


def test_websocket_connection(page: Page, base_url: str):
    """Test that WebSocket connection for real-time events works."""
    page.goto(base_url)

    # Wait for page to fully load
    page.wait_for_load_state("networkidle")

    # Check for WebSocket connection indicator
    ws_indicator = page.locator("#ws-status")
    expect(ws_indicator).to_be_visible()

    # Should show "connected" after a moment
    page.wait_for_timeout(2000)
    expect(ws_indicator).to_contain_text("connected", timeout=10000)


def test_responsive_design(page: Page, base_url: str):
    """Test that console is responsive to different screen sizes."""
    page.goto(base_url)

    # Test mobile view
    page.set_viewport_size({"width": 375, "height": 667})
    expect(page.locator("#service-status")).to_be_visible()

    # Test tablet view
    page.set_viewport_size({"width": 768, "height": 1024})
    expect(page.locator("#service-status")).to_be_visible()

    # Test desktop view
    page.set_viewport_size({"width": 1920, "height": 1080})
    expect(page.locator("#service-status")).to_be_visible()


def test_approve_dialog_flow(page: Page, base_url: str):
    """Test the approval dialog flow."""
    page.goto(base_url)

    # Click approve button
    page.click("#approve-btn")

    # Check for confirmation dialog
    dialog = page.locator(".approval-dialog")
    expect(dialog).to_be_visible()

    # Check dialog content
    expect(dialog).to_contain_text("Approve Content")

    # Cancel the dialog
    page.click(".cancel-btn")
    expect(dialog).not_to_be_visible()


def test_emergency_stop_confirmation(page: Page, base_url: str):
    """Test emergency stop confirmation dialog."""
    page.goto(base_url)

    # Click emergency stop
    page.click("button.emergency-stop")

    # Check for confirmation dialog
    dialog = page.locator(".emergency-dialog")
    expect(dialog).to_be_visible()

    # Check warning text
    expect(dialog).to_contain_text("Emergency Stop")

    # Cancel for safety
    page.click(".cancel-btn")


def test_dark_mode_toggle(page: Page, base_url: str):
    """Test dark mode toggle if present."""
    page.goto(base_url)

    # Look for dark mode toggle
    toggle = page.locator("#dark-mode-toggle")

    if toggle.is_visible():
        # Click to toggle dark mode
        toggle.click()
        page.wait_for_timeout(500)

        # Check body has dark mode class
        expect(page.locator("body")).to_have_class(/dark/)

        # Toggle back
        toggle.click()
        page.wait_for_timeout(500)


def test_service_health_indicators(page: Page, base_url: str):
    """Test that service health indicators are color-coded."""
    page.goto(base_url)

    # Wait for services to load
    page.wait_for_selector("#service-status .service-item")

    # Check for health status indicators
    health_indicators = page.locator("#service-status .health-status")
    expect(health_indicators).to_have_count(8)

    # Each indicator should have a status class
    for i in range(8):
        indicator = health_indicators.nth(i)
        expect(indicator).to_have_attribute("class", /status-(healthy|unhealthy|warning)/)
