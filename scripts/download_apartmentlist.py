#!/usr/bin/env python3
"""
Download Apartment List CSV data using headless browser automation.

This script uses Playwright to navigate to the Apartment List research page,
select a specific dataset from the dropdown, and download the CSV file.
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout


async def download_apartmentlist_csv(url: str, option_name: str, output_path: str) -> bool:
    """
    Download CSV from Apartment List using headless browser.
    
    Args:
        url: The Apartment List research page URL
        option_name: The dropdown option to select
        output_path: Where to save the downloaded CSV
        
    Returns:
        bool: True if successful, False otherwise
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                accept_downloads=True,
                user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/123 Safari/537.36")
            )
            page = await ctx.new_page()

            # Fallback capture of CSV responses if Download event doesn't fire
            csv_bytes = None
            def on_response(resp):
                nonlocal csv_bytes
                ct = (resp.headers or {}).get("content-type", "").lower()
                if ("text/csv" in ct) or resp.url.lower().endswith(".csv"):
                    # best-effort; we'll still prefer the official download event
                    try:
                        csv_bytes = resp.body()
                    except Exception:
                        pass
            page.on("response", on_response)

            print(f"Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_load_state("networkidle", timeout=30_000)

            # --- Select dropdown option (try exact id first, then ARIA role) ---
            print(f"Selecting option: {option_name}")
            option_pattern = re.compile(
                option_name.replace(" ", r"\s+").replace("-", r"[-–—]"), re.IGNORECASE
            )
            try:
                combo = page.locator("#mui-component-select-age")
                await combo.first.click(force=True, timeout=10_000)
            except Exception:
                try:
                    combo = page.get_by_role("combobox").first
                    await combo.click(timeout=10_000)
                except Exception:
                    pass

            try:
                opt = page.get_by_role("option", name=option_pattern)
                if await opt.count() > 0:
                    await opt.first.click()
                else:
                    # if already selected, continue
                    val = await combo.inner_text() if combo else ""
                    if not option_pattern.search(val or ""):
                        print("Warning: desired option not found/selected; continuing with current selection.")
            except Exception:
                pass

            # --- Click Download ---
            print("Clicking Download…")
            btn = page.get_by_role("button", name=re.compile(r"^Download$", re.I)).first
            if not await btn.count():
                print("Error: Download button not found")
                await browser.close()
                return False

            # Prefer official file download event
            try:
                async with page.expect_download(timeout=45_000) as dl_info:
                    await btn.click()
                dl = await dl_info.value
                path = await dl.path()
                if path:
                    output_file.write_bytes(Path(path).read_bytes())
                    print(f"Downloaded via download event: {dl.suggested_filename}")
                    await browser.close()
                    return True
            except PWTimeout:
                print("Download event not seen; trying response-capture fallback…")

            # Fallback: use captured CSV response
            if csv_bytes:
                # csv_bytes might be a coroutine (playwright>=1.47) — await if needed
                if callable(getattr(csv_bytes, "__await__", None)):
                    csv_bytes = await csv_bytes
                output_file.write_bytes(csv_bytes)
                print("Downloaded via response capture.")
                await browser.close()
                return True

            print("Error: Could not obtain CSV via download or response.")
            await browser.close()
            return False

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download Apartment List CSV using headless browser"
    )
    parser.add_argument(
        "--url",
        default="https://www.apartmentlist.com/research/category/data-rent-estimates",
        help="URL of the Apartment List research page"
    )
    parser.add_argument(
        "--option",
        default="Historic Rent Estimates (Jan 2017 - Present)",
        help="Dropdown option to select"
    )
    parser.add_argument(
        "--out",
        default="data/apartmentlist_raw.csv",
        help="Output file path for the downloaded CSV"
    )
    
    args = parser.parse_args()
    
    print(f"Starting download with:")
    print(f"  URL: {args.url}")
    print(f"  Option: {args.option}")
    print(f"  Output: {args.out}")
    
    success = asyncio.run(
        download_apartmentlist_csv(args.url, args.option, args.out)
    )
    
    if success:
        print("Download completed successfully!")
        sys.exit(0)
    else:
        print("Download failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()