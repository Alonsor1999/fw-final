import requests
import time
import config

def solve_with_2captcha(image_bytes):
    resp = requests.post(
        'http://2captcha.com/in.php',
        files={'file': ('captcha.png', image_bytes)},
        data={'key': config.CAPTCHA_API_KEY, 'method': 'post'}
    )
    if "OK|" not in resp.text:
        raise Exception("Captcha not accepted by 2Captcha: " + resp.text)

    captcha_id = resp.text.split('|')[1]

    for _ in range(20):
        r = requests.get(f"http://2captcha.com/res.php?key={config.CAPTCHA_API_KEY}&action=get&id={captcha_id}")
        if r.text == "CAPCHA_NOT_READY":
            time.sleep(5)
            continue
        if "OK|" in r.text:
            return r.text.split('|')[1]
        break
    raise Exception("Failed to get captcha solution")
