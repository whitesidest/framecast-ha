from datetime import timedelta

DOMAIN = "framecast"

CONF_URL = "url"
CONF_API_KEY = "api_key"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

PLATFORMS = ["button", "sensor"]

ATTR_DEVICE_ID = "device_id"
ATTR_IMAGE_ID = "image_id"
ATTR_RULE_ID = "rule_id"
ATTR_SOURCE_ID = "source_id"

# Value accepted by the device_id service field to mean "every known device".
# Matched case-insensitively; a device literally named "all" would shadow it,
# which is why the error text always offers the UUID as the unambiguous form.
DEVICE_TARGET_ALL = "all"

SERVICE_SEND_IMAGE = "send_image"
SERVICE_WAKE_DEVICE = "wake_device"
SERVICE_SLEEP_DEVICE = "sleep_device"
SERVICE_TRIGGER_RULE = "trigger_rule"
SERVICE_POLL_DEVICE = "poll_device"
SERVICE_SYNC_SOURCE = "sync_source"
