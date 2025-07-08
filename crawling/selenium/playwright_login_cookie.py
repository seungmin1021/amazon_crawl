from playwright.sync_api import sync_playwright
import json

def save_amazon_cookies_manually():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("➡️ 브라우저가 열렸습니다. Amazon에 로그인한 후 Enter를 눌러주세요.")
        page.goto("https://www.amazon.com/")
        
        input("🛑 로그인 완료 후 여기서 Enter를 누르세요...")

        cookies = context.cookies()
        with open("amazon_cookies.json", "w") as f:
            json.dump(cookies, f)

        print("✅ 쿠키 저장 완료.")
        browser.close()



if __name__ == '__main__':
    save_amazon_cookies_manually()
    