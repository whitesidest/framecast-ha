# FrameCast for Home Assistant

Custom HACS integration that exposes a [FrameCast](https://github.com/whitesidest/palimpsest) server to Home Assistant.

## What you get

- **Buttons**
  - Per Frame TV: **Wake**, **Sleep**, and a disabled-by-default **Poll** (enable from the entity registry if you want a manual status refresh)
  - One per active `ContentRule`
  - One per `Announcement`
- **Sensors**
  - One per Frame TV, surfacing status (`ONLINE` / `ART_MODE` / `OFF` / `UNREACHABLE`) plus IP, MAC, current artwork metadata (title, artist, year, medium, description), brightness (0–10), matte, **quiet-hours config** (enabled, start, end, dim brightness, active flag), and last-seen
  - One per paired CompanionScreen (e-ink tiny_canvas), surfacing power mode + last-sync timestamps
- **Services**
  - `framecast.send_image` — push a specific image to a device (`device_id`, `image_id`)
  - `framecast.wake_device` — wake a Frame (Art Mode + brightness restore; server-side issues a KEY_POWER cycle to physically light the panel)
  - `framecast.sleep_device` — put a Frame into a dim Art-Mode rest state
  - `framecast.trigger_rule` — fire a `ContentRule` by ID (alternative to the button entity)
  - `framecast.poll_device` — queue an immediate status poll
  - `framecast.sync_source` — queue a sync of a `ContentSource`

## Naming a device in a service call

Every service that takes `device_id` accepts three forms:

| `device_id` | Means |
| --- | --- |
| `Living Room` | The device with that name, case-insensitively (`living room` works too) |
| `f4c3b8a0-…` | That device UUID — the original form, still supported |
| `all` | Every device on every configured FrameCast server |

Names come from the device's **Name** in FrameCast, so renaming there changes
what automations should say. A UUID is always matched before a name, so an
automation written against an ID can't be redirected by a rename.

If two devices share a name, the call fails with both listed rather than
guessing — use the UUID for that one. With `all`, each device is attempted
independently: one unreachable Frame doesn't stop the rest, and the call still
reports as failed afterwards, naming which devices errored.

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
          device_id: "Living Room"
          image_id: 42

  - alias: "Frame TVs: all to sleep at bedtime"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: framecast.sleep_device
        data:
          device_id: all
```

## Polling

Devices, rules, and announcements are refreshed every 60 seconds.
