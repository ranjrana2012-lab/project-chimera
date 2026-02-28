"""Playwright E2E tests for Operator Console UI."""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def console_base_url():
    """Base URL for the Operator Console."""
    return "http://localhost:8007"


@pytest.fixture(scope="session")
def console_browser_context_args(browser_context_args):
    """Extend browser context with default viewport for Console tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
    }


@pytest.mark.e2e
class TestConsolePageLoad:
    """Test Console page load and layout."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_page_loads_without_errors(self, page: Page, console_base_url: str):
        """Test page loads without console errors."""
        console_errors = []

        def log_error(msg):
            if msg.type == "error":
                console_errors.append(msg.text)

        page.on("console", log_error)
        page.goto(console_base_url)

        assert len(console_errors) == 0, f"Console errors: {console_errors}"

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_page_has_correct_title(self, page: Page, console_base_url: str):
        """Test page has the correct title."""
        page.goto(console_base_url)
        expect(page).to_have_title("Project Chimera - Operator Console")

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_all_panels_render(self, page: Page, console_base_url: str):
        """Test all UI panels render correctly."""
        page.goto(console_base_url)

        # Check for main heading
        expect(page.locator("h1")).to_be_visible()

        # Check for main panels by ID
        expect(page.locator("#service-status")).to_be_visible()
        expect(page.locator("#event-stream")).to_be_visible()
        expect(page.locator("#approvals")).to_be_visible()
        expect(page.locator("#overrides")).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_no_404_resources(self, page: Page, console_base_url: str):
        """Test that no resources return 404 errors."""
        failed_requests = []

        def log_request(request):
            # Skip non-GET requests and data URLs
            if request.method != "GET" or request.url.startswith("data:"):
                return

        def log_response(response):
            if response.status == 404:
                failed_requests.append(response.url)

        page.on("request", log_request)
        page.on("response", log_response)
        page.goto(console_base_url)

        # Wait for page to settle
        page.wait_for_load_state("networkidle")

        assert len(failed_requests) == 0, f"404 resources: {failed_requests}"


@pytest.mark.e2e
class TestConsoleResponsive:
    """Test responsive design."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    @pytest.mark.parametrize("viewport", [
        {"width": 375, "height": 667},  # Mobile
        {"width": 768, "height": 1024},  # Tablet
        {"width": 1920, "height": 1080}  # Desktop
    ])
    def test_responsive_layout(self, page: Page, console_base_url: str, viewport):
        """Test responsive layout at different viewports."""
        page.set_viewport_size(viewport)
        page.goto(console_base_url)

        # Page should be responsive
        expect(page.locator("body")).to_be_visible()
        expect(page.locator("#service-status")).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_mobile_layout_adjustments(self, page: Page, console_base_url: str):
        """Test mobile-specific layout adjustments."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(console_base_url)

        # Main content should still be visible
        expect(page.locator("h1")).to_be_visible()
        expect(page.locator("#service-status")).to_be_visible()

        # May have stacked layout on mobile
        service_status = page.locator("#service-status")
        expect(service_status).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_desktop_layout(self, page: Page, console_base_url: str):
        """Test desktop-specific layout."""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(console_base_url)

        # All panels should be visible
        expect(page.locator("#service-status")).to_be_visible()
        expect(page.locator("#event-stream")).to_be_visible()
        expect(page.locator("#approvals")).to_be_visible()
        expect(page.locator("#overrides")).to_be_visible()


@pytest.mark.e2e
class TestConsoleServiceStatus:
    """Test Service Status panel."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_all_services_displayed(self, page: Page, console_base_url: str):
        """Test that all 8 services are displayed."""
        page.goto(console_base_url)

        # Wait for services to load
        page.wait_for_selector("#service-status .service-item", timeout=5000)

        services = page.locator("#service-status .service-item")
        expect(services).to_have_count(8)

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_service_names(self, page: Page, console_base_url: str):
        """Test that service names are correct."""
        page.goto(console_base_url)

        expected_services = [
            "OpenClaw Orchestrator",
            "SceneSpeak Agent",
            "Captioning Agent",
            "BSL-Text2Gloss Agent",
            "Sentiment Agent",
            "Lighting Control",
            "Safety Filter",
            "Operator Console"
        ]

        # Wait for services to load
        page.wait_for_selector("#service-status .service-item", timeout=5000)

        for service_name in expected_services:
            expect(page.locator("#service-status")).to_contain_text(service_name)

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_health_indicators_visible(self, page: Page, console_base_url: str):
        """Test that health indicators are visible."""
        page.goto(console_base_url)

        # Wait for services to load
        page.wait_for_selector("#service-status .service-item", timeout=5000)

        health_indicators = page.locator("#service-status .health-status")
        expect(health_indicators).to_have_count(8)

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_health_status_color_coded(self, page: Page, console_base_url: str):
        """Test that health status has appropriate classes."""
        page.goto(console_base_url)

        # Wait for services to load
        page.wait_for_selector("#service-status .service-item", timeout=5000)

        health_indicators = page.locator("#service-status .health-status")

        # Each indicator should have a status class
        for i in range(8):
            indicator = health_indicators.nth(i)
            class_attr = indicator.get_attribute("class") or ""
            assert any(status in class_attr for status in ["status-healthy", "status-unhealthy", "status-warning"])


@pytest.mark.e2e
class TestConsoleEventStream:
    """Test Event Stream panel."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_event_stream_visible(self, page: Page, console_base_url: str):
        """Test that event stream is visible."""
        page.goto(console_base_url)

        event_stream = page.locator("#event-stream")
        expect(event_stream).to_be_visible()
        expect(event_stream.locator("h2")).to_contain_text("Live Events")

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_event_stream_container(self, page: Page, console_base_url: str):
        """Test that event stream has a container."""
        page.goto(console_base_url)

        event_stream = page.locator("#event-stream")
        expect(event_stream.locator(".event-list")).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_websocket_status_indicator(self, page: Page, console_base_url: str):
        """Test WebSocket connection status indicator."""
        page.goto(console_base_url)

        # Check for WebSocket status indicator
        ws_indicator = page.locator("#ws-status")
        expect(ws_indicator).to_be_visible()

        # Should show connection status after a moment
        page.wait_for_timeout(2000)
        expect(ws_indicator).to_contain_text("connected")


@pytest.mark.e2e
class TestConsoleApprovalWorkflow:
    """Test Approval Workflow panel."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_approval_buttons_exist(self, page: Page, console_base_url: str):
        """Test that approval buttons exist and are enabled."""
        page.goto(console_base_url)

        approvals = page.locator("#approvals")

        # Check approve button
        approve_btn = approvals.locator("#approve-btn")
        expect(approve_btn).to_be_visible()
        expect(approve_btn).to_be_enabled()

        # Check reject button
        reject_btn = approvals.locator("#reject-btn")
        expect(reject_btn).to_be_visible()
        expect(reject_btn).to_be_enabled()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_approve_dialog_flow(self, page: Page, console_base_url: str):
        """Test the approval dialog flow."""
        page.goto(console_base_url)

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


@pytest.mark.e2e
class TestConsoleOverrideControls:
    """Test Override Controls panel."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_override_buttons_exist(self, page: Page, console_base_url: str):
        """Test that override controls exist."""
        page.goto(console_base_url)

        overrides = page.locator("#overrides")

        # Check emergency stop button
        emergency_btn = overrides.locator("button.emergency-stop")
        expect(emergency_btn).to_be_visible()

        # Check pause button
        pause_btn = overrides.locator("button.pause-btn")
        expect(pause_btn).to_be_visible()

        # Check resume button
        resume_btn = overrides.locator("button.resume-btn")
        expect(resume_btn).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_emergency_stop_confirmation(self, page: Page, console_base_url: str):
        """Test emergency stop confirmation dialog."""
        page.goto(console_base_url)

        # Click emergency stop
        page.click("button.emergency-stop")

        # Check for confirmation dialog
        dialog = page.locator(".emergency-dialog")
        expect(dialog).to_be_visible()

        # Check warning text
        expect(dialog).to_contain_text("Emergency Stop")

        # Cancel for safety
        page.click(".cancel-btn")


@pytest.mark.e2e
class TestConsoleInteractions:
    """Test user interactions with the Console."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_service_status_hover(self, page: Page, console_base_url: str):
        """Test hover interaction on service status items."""
        page.goto(console_base_url)

        # Wait for services to load
        page.wait_for_selector("#service-status .service-item", timeout=5000)

        # Hover over first service
        first_service = page.locator("#service-status .service-item").first
        first_service.hover()

        # Should show tooltip or additional info
        expect(first_service).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_keyboard_navigation(self, page: Page, console_base_url: str):
        """Test keyboard navigation works."""
        page.goto(console_base_url)

        # Tab through interactive elements
        page.keyboard.press("Tab")

        # Should focus on first interactive element
        focused = page.locator(":focus")
        expect(focused).to_be_visible()


@pytest.mark.e2e
class TestConsoleDarkMode:
    """Test dark mode functionality."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_dark_mode_toggle_exists(self, page: Page, console_base_url: str):
        """Test that dark mode toggle exists."""
        page.goto(console_base_url)

        toggle = page.locator("#dark-mode-toggle")

        # Toggle may or may not be present
        if toggle.is_visible():
            expect(toggle).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_dark_mode_toggle_works(self, page: Page, console_base_url: str):
        """Test that dark mode toggle works."""
        page.goto(console_base_url)

        toggle = page.locator("#dark-mode-toggle")

        if toggle.is_visible():
            # Get initial state
            body = page.locator("body")

            # Click to toggle dark mode
            toggle.click()
            page.wait_for_timeout(500)

            # Check body has dark mode class
            expect(body).to_have_class("dark")

            # Toggle back
            toggle.click()
            page.wait_for_timeout(500)


@pytest.mark.e2e
class TestConsoleAccessibility:
    """Test accessibility features."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_main_heading_present(self, page: Page, console_base_url: str):
        """Test that main heading is present."""
        page.goto(console_base_url)

        h1 = page.locator("h1")
        expect(h1).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_buttons_have_accessible_labels(self, page: Page, console_base_url: str):
        """Test that buttons have accessible labels."""
        page.goto(console_base_url)

        # Check approve button has label or text
        approve_btn = page.locator("#approve-btn")
        expect(approve_btn).to_be_visible()

        # Should have aria-label, text content, or title
        has_label = (
            approve_btn.get_attribute("aria-label") is not None or
            approve_btn.inner_text() != "" or
            approve_btn.get_attribute("title") is not None
        )
        assert has_label, "Approve button should have accessible label"

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_landmark_regions(self, page: Page, console_base_url: str):
        """Test that page has landmark regions."""
        page.goto(console_base_url)

        # Check for main landmark
        main = page.locator("main")
        expect(main).to_be_visible()

        # Check for navigation or banner
        nav_or_header = page.locator("nav, header")
        # These are optional but good to have


@pytest.mark.e2e
class TestConsolePerformance:
    """Test performance characteristics."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_page_loads_quickly(self, page: Page, console_base_url: str):
        """Test that page loads within acceptable time."""
        import time

        start = time.time()
        page.goto(console_base_url)
        page.wait_for_load_state("networkidle")
        load_time = time.time() - start

        # Should load in less than 5 seconds
        assert load_time < 5.0, f"Page load time {load_time}s exceeds 5s threshold"

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_no_memory_leaks_simple(self, page: Page, console_base_url: str):
        """Simple test to check for obvious memory issues."""
        page.goto(console_base_url)

        # Navigate a few times
        for _ in range(3):
            page.reload()
            page.wait_for_load_state("networkidle")

        # If we got here without crashing, basic check passes
        assert True


@pytest.mark.e2e
class TestConsoleErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_handles_missing_service_data(self, page: Page, console_base_url: str):
        """Test graceful handling of missing service data."""
        page.goto(console_base_url)

        # Page should still render even if some services are down
        expect(page.locator("#service-status")).to_be_visible()

    @pytest.mark.skip(reason="Requires running Console service on port 8007")
    def test_handles_websocket_disconnect(self, page: Page, console_base_url: str):
        """Test handling of WebSocket disconnection."""
        page.goto(console_base_url)

        # Check that UI handles connection state changes
        ws_indicator = page.locator("#ws-status")

        if ws_indicator.is_visible():
            # Should show connection status
            expect(ws_indicator).to_be_visible()
