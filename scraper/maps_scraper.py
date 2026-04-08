import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Optional, Set
from playwright.async_api import async_playwright, Page, Browser
from models.schemas import Lead
from services.job_store import update_job

logger = logging.getLogger(__name__)

# Stop flags keyed by job_id
_stop_flags: dict = {}


def request_stop(job_id: str):
    _stop_flags[job_id] = True


def clear_stop(job_id: str):
    _stop_flags.pop(job_id, None)


def should_stop(job_id: str) -> bool:
    return _stop_flags.get(job_id, False)


async def extract_leads(job_id: str, maps_url: str, city: Optional[str], scroll_delay: float, max_results: Optional[int]):
    clear_stop(job_id)
    leads = []
    seen_names: Set[str] = set()

    try:
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--window-size=1280,900",
                ],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page: Page = await context.new_page()

            update_job(job_id, status="running", progress_message="Opening Google Maps...")
            # Using domcontentloaded is more reliable for Google Maps as it has background network requests that can stay open
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await page.goto(maps_url, wait_until="domcontentloaded", timeout=60000)
                    # Wait for the main feed or search container to appear as a secondary check
                    await page.wait_for_selector('[role="feed"], .m6QErb, #searchbox', timeout=15000)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"[{job_id}] Attempt {attempt+1} failed ({e}). Retrying in 3s...")
                        await page.wait_for_timeout(3000)
                    else:
                        raise e
            
            await page.wait_for_timeout(4000)

            # Handle consent/cookie dialog
            try:
                consent_btn = page.locator('button:has-text("Accept all"), button:has-text("Reject all"), [aria-label="Accept all"]')
                if await consent_btn.first.is_visible(timeout=3000):
                    await consent_btn.first.click()
                    await page.wait_for_timeout(1500)
            except Exception:
                pass

            update_job(job_id, progress_message="Scrolling results panel...")

            # Find results panel
            results_panel = page.locator('[role="feed"], .m6QErb[aria-label], div[aria-label*="Results for"]')
            panel = None
            try:
                panel = results_panel.first
                await panel.wait_for(timeout=8000)
            except Exception:
                # Try alternate selector
                try:
                    panel = page.locator('div[role="main"] [role="feed"]').first
                    await panel.wait_for(timeout=5000)
                except Exception:
                    logger.warning(f"[{job_id}] Could not find results feed panel")

            # Scroll and collect listing links
            listing_urls: list = []
            seen_urls: Set[str] = set()
            no_new_count = 0
            max_no_new = 5

            while not should_stop(job_id):
                if max_results is not None and len(listing_urls) >= max_results:
                    break

                # Collect all current listing links
                links = await page.locator('a[href*="/maps/place/"]').all()
                new_found = 0
                for link in links:
                    href = await link.get_attribute("href")
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                        listing_urls.append(href)
                        new_found += 1

                update_job(
                    job_id,
                    progress_message=f"Collecting listings... found {len(listing_urls)} so far",
                    total_found=len(listing_urls),
                )

                if new_found == 0:
                    no_new_count += 1
                    if no_new_count >= max_no_new:
                        logger.info(f"[{job_id}] No new listings after {max_no_new} scrolls, stopping scroll")
                        break
                else:
                    no_new_count = 0

                # Scroll the panel
                if panel:
                    try:
                        await panel.evaluate("el => el.scrollBy(0, 600)")
                    except Exception:
                        await page.keyboard.press("PageDown")
                else:
                    await page.keyboard.press("PageDown")

                await page.wait_for_timeout(int(scroll_delay * 1000))

            # Now extract details from each listing
            logger.info(f"[{job_id}] Found {len(listing_urls)} listings, extracting details...")
            update_job(job_id, progress_message=f"Extracting details from {len(listing_urls)} listings...")

            for i, url in enumerate(listing_urls):
                if should_stop(job_id):
                    break
                if max_results is not None and len(leads) >= max_results:
                    break

                try:
                    lead = await _extract_listing_detail(page, url, city, job_id)
                    if lead and lead.name and lead.name not in seen_names:
                        seen_names.add(lead.name)
                        lead.extracted_at = datetime.now().isoformat()
                        leads.append(lead)
                        update_job(
                            job_id,
                            leads=leads.copy(),
                            total_found=len(leads),
                            progress_message=f"Extracted {len(leads)} leads... ({i+1}/{len(listing_urls)})",
                        )
                    await page.wait_for_timeout(800)
                except Exception as e:
                    logger.warning(f"[{job_id}] Error extracting {url}: {e}")
                    continue

            await browser.close()

        status = "stopped" if should_stop(job_id) else "completed"
        update_job(
            job_id,
            status=status,
            leads=leads,
            total_found=len(leads),
            completed_at=datetime.now().isoformat(),
            progress_message=f"Done! Extracted {len(leads)} leads.",
        )
        logger.info(f"[{job_id}] Extraction {status} with {len(leads)} leads")

    except Exception as e:
        logger.error(f"[{job_id}] Fatal extraction error: {e}", exc_info=True)
        update_job(
            job_id,
            status="failed",
            error=str(e),
            completed_at=datetime.now().isoformat(),
            progress_message=f"Error: {e}",
        )
    finally:
        clear_stop(job_id)


async def _extract_listing_detail(page: Page, url: str, city_override: Optional[str], job_id: str) -> Optional[Lead]:
    try:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        except Exception:
            # Fallback for very slow loads
            pass
        await page.wait_for_timeout(2000)

        lead = Lead()

        # Name
        try:
            name_el = page.locator('h1.DUwDvf, h1[data-attrid="title"], [data-item-id] h1').first
            lead.name = (await name_el.inner_text(timeout=3000)).strip()
        except Exception:
            try:
                lead.name = await page.title()
                lead.name = re.sub(r"\s*[-–|].*$", "", lead.name).strip()
            except Exception:
                pass

        # Address / City
        try:
            addr_el = page.locator('[data-item-id*="address"] .Io6YTe, button[data-item-id*="address"] .fontBodyMedium').first
            addr = (await addr_el.inner_text(timeout=3000)).strip()
            if city_override:
                lead.city = city_override
            else:
                lead.city = _extract_city(addr)
        except Exception:
            lead.city = city_override or ""

        # Phone
        try:
            phone_el = page.locator('[data-item-id*="phone"] .Io6YTe, [aria-label*="Phone"] .fontBodyMedium').first
            lead.phone = (await phone_el.inner_text(timeout=3000)).strip()
        except Exception:
            pass

        # Website
        try:
            website_el = page.locator('a[data-item-id*="authority"], a[href*="http"][aria-label*="website" i], [data-item-id="authority"] a').first
            lead.website = (await website_el.get_attribute("href", timeout=3000) or "").strip()
            if lead.website.startswith("https://www.google.com/url"):
                m = re.search(r"url=([^&]+)", lead.website)
                if m:
                    from urllib.parse import unquote
                    lead.website = unquote(m.group(1))
        except Exception:
            pass

        # About / Description
        try:
            about_el = page.locator('[data-attrid="description"] span, .PYvSYb, .HlvSq').first
            lead.about = (await about_el.inner_text(timeout=2000)).strip()[:300]
        except Exception:
            pass

        # Instagram (from website or social links)
        try:
            ig_links = page.locator('a[href*="instagram.com"]')
            if await ig_links.count() > 0:
                href = await ig_links.first.get_attribute("href") or ""
                m = re.search(r"instagram\.com/([^/?#]+)", href)
                if m:
                    lead.instagram = f"@{m.group(1)}"
        except Exception:
            pass

        return lead

    except Exception as e:
        logger.debug(f"[{job_id}] Skipping listing due to: {e}")
        return None


def _extract_city(address: str) -> str:
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    # City is usually second-to-last or third-to-last part
    if len(parts) >= 3:
        return parts[-3]
    elif len(parts) >= 2:
        return parts[-2]
    return ""
