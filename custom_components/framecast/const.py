from datetime import timedelta

DOMAIN = "framecast"

CONF_URL = "url"
CONF_API_KEY = "api_key"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

PLATFORMS = ["button", "sensor"]

ATTR_DEVICE_ID = "device_id"
ATTR_IMAGE_ID = "image_id"
ATTR_RULE_ID = "rule_id"

SERVICE_SEND_IMAGE = "send_image"
SERVICE_WAKE_DEVICE = "wake_device"
SERVICE_TRIGGER_RULE = "trigger_rule"
