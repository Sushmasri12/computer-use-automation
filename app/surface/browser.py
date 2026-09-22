from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)


class BrowserSurface:
    def __init__(self, headless: bool = False):
        self.headless = headless

        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()

        self.browser = await self._playwright.chromium.launch(
            headless=self.headless
        )

        self.context = await self.browser.new_context()

        self.page = await self.context.new_page()

    async def navigate(self, url: str) -> None:
        self._require_page()

        await self.page.goto(
            url,
            wait_until="domcontentloaded",
        )

    async def get_state(self) -> dict:
        self._require_page()

        elements = await self.page.locator(
            "input, button, [id]"
        ).evaluate_all(
            """
            elements => elements.map(element => ({
                tag: element.tagName.toLowerCase(),
                id: element.id || null,
                name: element.getAttribute("name"),
                type: element.getAttribute("type"),
                text: (
                    element.innerText ||
                    element.value ||
                    ""
                ).trim()
            }))
            """
        )

        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "visible_text": await self.page.locator("body").inner_text(),
            "elements": elements,
        }

    async def click_by_role(
        self,
        role: str,
        name: str,
    ) -> None:
        self._require_page()

        await self.page.get_by_role(
            role,
            name=name,
        ).click()

    async def fill_by_label(
        self,
        label: str,
        value: str,
    ) -> None:
        self._require_page()

        await self.page.get_by_label(label).fill(value)

    async def get_text(
        self,
        selector: str,
    ) -> str:
        self._require_page()

        text = await self.page.locator(selector).inner_text()

        return text.strip()

    async def screenshot(
        self,
        path: str,
    ) -> None:
        self._require_page()

        await self.page.screenshot(
            path=path,
            full_page=True,
        )

    async def close(self) -> None:
        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self._playwright:
            await self._playwright.stop()

    def _require_page(self) -> None:
        if self.page is None:
            raise RuntimeError(
                "Browser surface has not been started."
            )