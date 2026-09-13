from datetime import timedelta

DOMAIN = "framecast"

CONF_URL = "url"
CONF_API_KEY = "api_key"

# How often the coordinator polls FrameCast (devices, rules, announcements,
# companions and each device's current image). An option on the config
# entry: the default is a quiet 60 s, but an automation that reacts to the
# art changing — "when the Frame shows a new piece, retheme the dial" —
# waits on this poll, so 60 s meant a 0–60 s (average 30 s) lag between the
# push and the reaction while every other hop took under a second.
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL_S = 60
MIN_SCAN_INTERVAL_S = 5
MAX_SCAN_INTERVAL_S = 600
DEFAULT_SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL_S)

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
