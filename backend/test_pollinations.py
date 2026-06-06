"""Quick test: Pollinations.ai free image generation"""
import httpx

url = (
    "https://image.pollinations.ai/prompt/"
    "Professional%20minimal%20flat%20logo%20icon%20for%20tiffin%20"
    "service%20orange%20cream%20vector%20art%20white%20background%20"
    "no%20text?width=400&height=400&nologo=true"
)

print("Testing Pollinations.ai...")
print(f"URL: {url[:80]}...")

r = httpx.head(url, follow_redirects=True, timeout=30)
print(f"Status: {r.status_code}")
ct = r.headers.get("content-type", "N/A")
print(f"Content-Type: {ct}")
print(f"Works: {r.status_code == 200}")

if r.status_code == 200:
    # Download the actual image
    print("\nDownloading full image...")
    img = httpx.get(url, follow_redirects=True, timeout=30)
    with open("test_pollinations_logo.png", "wb") as f:
        f.write(img.content)
    print(f"Saved: test_pollinations_logo.png ({len(img.content)} bytes)")
