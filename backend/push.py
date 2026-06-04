import json
import os
from pywebpush import webpush, WebPushException

# The private key is stored in .env with literal \n for newlines.
# We convert them back here so pywebpush sees a real PEM string.
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "").replace("\\n", "\n")
VAPID_EMAIL = os.getenv("VAPID_EMAIL", "mailto:srinikp2@gmail.com")


def send_push(subscription_json: str, title: str, body: str) -> bool:
    """Send a Web Push notification. Returns True on success."""
    if not VAPID_PRIVATE_KEY:
        print("[Push] VAPID_PRIVATE_KEY not set — skipping send")
        return False

    subscription = json.loads(subscription_json)
    payload = json.dumps({"title": title, "body": body})

    try:
        webpush(
            subscription_info=subscription,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_EMAIL},
        )
        return True
    except WebPushException as e:
        print(f"[Push] Send failed: {e}")
        return False
