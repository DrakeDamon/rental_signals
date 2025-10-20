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
            print(f"Launching headless Chromium...")
            browser = await p.chromium.launch(headless=True)
            
            context = await browser.new_context(
                accept_downloads=True,
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                )
            )
            
            page = await context.new_page()
            
            print(f"Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for page to be interactive
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Try to select the dropdown option
            print(f"Looking for dropdown option: '{option_name}'")
            try:
                # Find and click the combobox
                combo = page.get_by_role("combobox").first
                await combo.wait_for(state="visible", timeout=10000)
                await combo.click()
                
                # Look for the option with flexible matching
                option_pattern = re.compile(
                    option_name.replace(" ", r"\s+").replace("-", r"[-–—]"),
                    re.IGNORECASE
                )
                
                option = page.get_by_role("option", name=option_pattern)
                if await option.count() > 0:
                    print(f"Found and selecting option: '{option_name}'")
                    await option.first.click()
                else:
                    print(f"Option '{option_name}' not found, checking if already selected...")
                    # Check if the option is already selected by default
                    current_value = await combo.inner_text()
                    if option_pattern.search(current_value):
                        print(f"Option already selected: '{current_value}'")
                    else:
                        print(f"Warning: Could not find or select option '{option_name}'")
                        print(f"Current dropdown value: '{current_value}'")
                        print("Proceeding with current selection...")
                        
            except PWTimeout:
                print("Timeout selecting dropdown option, proceeding with default selection...")
            except Exception as e:
                print(f"Error selecting dropdown option: {e}")
                print("Proceeding with current selection...")
            
            # Find and click the Download button
            print("Looking for Download button...")
            download_btn = page.get_by_role("button", name=re.compile(r"^Download$", re.I))
            
            if await download_btn.count() == 0:
                print("Error: Download button not found")
                await browser.close()
                return False
            
            print("Clicking Download button...")
            
            # Set up download handler and click
            async with page.expect_download(timeout=45000) as download_info:
                await download_btn.first.click()
            
            download = await download_info.value
            
            # Save the downloaded file
            download_path = await download.path()
            if download_path and Path(download_path).exists():
                output_file.write_bytes(Path(download_path).read_bytes())
                print(f"Successfully downloaded: {download.suggested_filename}")
                print(f"Saved to: {output_file}")
                
                # Verify file was saved and has content
                if output_file.exists() and output_file.stat().st_size > 0:
                    print(f"File size: {output_file.stat().st_size:,} bytes")
                    await browser.close()
                    return True
                else:
                    print("Error: Downloaded file is empty or missing")
                    await browser.close()
                    return False
            else:
                print("Error: Failed to get download path")
                await browser.close()
                return False
                
    except PWTimeout as e:
        print(f"Timeout error: {e}")
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