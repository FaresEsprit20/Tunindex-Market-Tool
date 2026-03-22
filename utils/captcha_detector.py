def has_captcha(html):
    if not html:
        return False

    triggers = ["captcha", "verify you are human", "recaptcha"]
    html_lower = html.lower()

    return any(t in html_lower for t in triggers)