def apply_stealth(driver):
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("window.navigator.chrome = {runtime: {}}")
    except:
        pass