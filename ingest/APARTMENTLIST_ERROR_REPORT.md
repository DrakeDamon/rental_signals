# ApartmentList Scraper Error Report

**Date:** 2025-10-26  
**Script:** `ingest/apartmentlist_pull.py`  
**Target URL:** https://www.apartmentlist.com/research/category/data-rent-estimates

---

## 🔴 CURRENT ERROR

```
ERROR: No CSV links found on ApartmentList page.
The page structure may have changed.
```

**Full Terminal Output:**

```bash
$ python3 ingest/apartmentlist_pull.py

=== TESTING UPDATED APARTMENTLIST SCRAPER ===

Fetching ApartmentList research page...
ERROR: No CSV links found on ApartmentList page.
The page structure may have changed.
```

---

## 📋 WHAT WE TRIED

### Attempt 1: Playwright Browser Automation (FAILED)

- **Approach:** Used headless Chromium to click dropdown and download button
- **Error:** `Error: Download button not found`
- **Issue:** Page structure didn't match expected selectors

### Attempt 2: BeautifulSoup Scraping of `data-value` Attributes (CURRENT)

- **Approach:** Based on manual inspection showing `<li role="option">` elements with `data-value` attributes containing CSV URLs
- **Expected Structure:**
  ```html
  <li
    role="option"
    data-value="//assets.ctfassets.net/.../Apartment_List_Rent_Estimates_2025_09.csv"
  >
    Historic Rent Estimates (Jan 2017 – Present)
  </li>
  ```
- **Expected URL Format:** `//assets.ctfassets.net/jeox55pd4d8n/2mcLafGxVQOROBubXMVmBr/ec5a603f24c8545b24c48897d4978d15/Apartment_List_Rent_Estimates_2025_09.csv`
- **Error:** Script cannot find any `<li role="option">` elements with `.csv` in `data-value`

---

## 🔍 CURRENT SCRIPT LOGIC

```python
def discover_csv_urls(html: str) -> List[tuple]:
    """Parse the ApartmentList page to find CSV URLs in data-value attributes."""
    soup = BeautifulSoup(html, "html.parser")
    csv_links = []

    # Find all <li role="option"> elements
    options = soup.find_all("li", {"role": "option"})

    for option in options:
        data_value = option.get("data-value", "")
        if data_value and ".csv" in data_value.lower():
            # Convert relative URL to absolute
            if data_value.startswith("//"):
                url = "https:" + data_value
            elif data_value.startswith("/"):
                url = "https://www.apartmentlist.com" + data_value
            else:
                url = data_value

            # Get the option label
            label = option.get_text(strip=True)

            # Only keep historic rent estimates
            if "rent estimate" in label.lower() or "historic" in label.lower():
                csv_links.append((label, url))
                print(f"Found CSV: {label} -> {url[:80]}...")

    return csv_links
```

**Issue:** `options = soup.find_all("li", {"role": "option"})` is returning an empty list.

---

## 💡 POSSIBLE REASONS FOR FAILURE

1. **JavaScript-Rendered Content**

   - The dropdown options may be dynamically loaded via JavaScript
   - BeautifulSoup only sees the initial HTML, not JavaScript-rendered content
   - The page may use React/Vue/Next.js which renders content client-side

2. **Different Page Structure**

   - The `data-value` attributes may be in a different element type
   - The options may be nested differently in the DOM
   - The page may have changed since the manual inspection

3. **Lazy Loading**

   - The CSV links may only appear after user interaction (clicking the dropdown)
   - The options may be loaded via AJAX after initial page load

4. **Anti-Scraping Measures**
   - The page may detect automated requests and serve different content
   - User-Agent or headers may need adjustment
   - Cloudflare or similar protection may be blocking our requests

---

## 🎯 DEBUGGING SUGGESTIONS

### Option A: Add Debug Output to See What BeautifulSoup Finds

```python
def discover_csv_urls(html: str) -> List[tuple]:
    soup = BeautifulSoup(html, "html.parser")

    # DEBUG: Print all <li> elements
    all_li = soup.find_all("li")
    print(f"DEBUG: Found {len(all_li)} total <li> elements")

    # DEBUG: Print all elements with role attribute
    all_roles = soup.find_all(attrs={"role": True})
    print(f"DEBUG: Found {len(all_roles)} elements with 'role' attribute")
    for elem in all_roles[:5]:  # Show first 5
        print(f"  - <{elem.name} role='{elem.get('role')}'> {elem.get_text(strip=True)[:50]}")

    # DEBUG: Search for any CSV URLs anywhere in the page
    import re
    csv_pattern = re.compile(r'https?://[^\s"\'<>]+\.csv', re.IGNORECASE)
    csv_matches = csv_pattern.findall(str(soup))
    print(f"DEBUG: Found {len(csv_matches)} .csv URLs anywhere in HTML:")
    for url in csv_matches[:3]:
        print(f"  - {url}")

    # Original logic...
```

### Option B: Use Selenium Instead of Playwright

- Selenium is more mature and may handle the page better
- Can wait for JavaScript to fully render before scraping

### Option C: Try Different Selectors

```python
# Try finding the combobox div and extracting options from it
combobox = soup.find("div", {"role": "combobox"})
if combobox:
    # Look for nested elements
    ...

# Try finding any element with data-value containing .csv
csv_elements = soup.find_all(attrs={"data-value": re.compile(r'.*\.csv', re.I)})
```

### Option D: Inspect the Actual Network Response

Save the HTML to a file to inspect what BeautifulSoup is actually seeing:

```python
with open("debug_apartmentlist_page.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("Saved HTML to debug_apartmentlist_page.html")
```

---

## 📝 WORKING REFERENCE: Zillow Scraper (Success)

For comparison, here's how the Zillow scraper successfully finds CSV links:

```python
def discover_zori_csv_links(html: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Look for ZORI CSVs - they can be in different formats
        if "zori" in href.lower() and ".csv" in href.lower():
            # Ensure absolute URL
            csv_url = href if href.startswith("http") else f"https://www.zillow.com{href}"
            anchor_text = (a.get_text() or "").strip()
            # ... determine type from filename ...
            links.append((anchor_text, csv_url))
    return links
```

**Key Difference:** Zillow uses traditional `<a>` anchor tags with `href` attributes, not JavaScript-driven dropdowns.

---

## 🚀 NEXT STEPS FOR CHATGPT ATLAS

1. **Add debug output** to see what HTML structure is actually present
2. **Determine if JavaScript rendering** is required (if so, use Selenium/Playwright with proper waits)
3. **Test different selectors** based on the actual HTML structure
4. **Consider alternative approaches:**
   - Direct URL construction if the CSV URLs follow a predictable pattern
   - API endpoint discovery (check Network tab in browser DevTools)
   - Contact ApartmentList for official data access

---

## 📎 REFERENCE FILES

- **Current Script:** `/Users/daviddamon/Desktop/tampa rental signals/tampa-rent-signals/ingest/apartmentlist_pull.py`
- **Working Zillow Script:** `/Users/daviddamon/Desktop/tampa rental signals/tampa-rent-signals/ingest/zillow_zori_pull.py`
- **Previous Playwright Attempt:** See git history or `APARTMENTLIST_TEST.md`

---

## 🎯 SUCCESS CRITERIA

The script should:

1. ✅ Successfully fetch the ApartmentList research page
2. ❌ **FAILING:** Discover CSV download URLs (currently returns 0 links)
3. ⏸️ Download the historic rent estimates CSV
4. ⏸️ Filter data to Tampa metro area
5. ⏸️ Create bronze layer (raw CSV)
6. ⏸️ Create silver layer (tidy Parquet)

---

**Status:** Script can fetch the page but cannot find the CSV links in the HTML. Need to debug the actual page structure.

