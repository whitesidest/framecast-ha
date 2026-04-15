# FrameCast for Home Assistant

Custom HACS integration that exposes a [FrameCast](https://github.com/whitesidest/palimpsest) server to Home Assistant.

## What you get

- **Buttons** — one per active `ContentRule` and per `Announcement`. Press to fire the rule / announcement.
- **Sensors** — one per Frame TV, surfacing status (`ONLINE` / `ART_MODE` / `OFF` / `UNREACHABLE`) plus IP, current content ID, brightness, and last-seen time.
- **Services**
  - `framecast.send_image` — push a specific image to a device (`device_id`, `image_id`)
  - `framecast.wake_device` — wake a Frame TV
  - `framecast.trigger_rule` — fire a rule by ID (alternative to the button entity)

## Installation (HACS custom repository)

1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/whitesidest/framecast-ha` as type **Integration**
3. Install **FrameCast**, restart Home Assistant
4. Settings → Devices & Services → **+ Add Integration** → search **FrameCast**
5. Enter your FrameCast URL (e.g. `http://192.168.1.163:8000`) and an API key

## Generating an API key

In FrameCast: **Integrations → API Keys → New**. Copy the plaintext shown once at creation — it's hashed in the DB and not retrievable later.

## Example automation

```yaml
automation:
  - alias: "Frame TV: morning artwork"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: framecast.send_image
        data:
          device_id: "f4c3b8a0-1234-5678-9abc-def012345678"
          image_id: 42
```

## Polling

Devices, rules, and announcements are refreshed every 60 seconds.
