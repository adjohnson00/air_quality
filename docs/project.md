**Final Project Summary**

### What you want it to do
You want a **local, battery-powered air quality monitor** for fire season in the Boise/Meridian, Idaho area. The main goal is to track particulate matter (especially PM2.5 from wildfire smoke) using the Adafruit PMSA003I laser sensor.  

Key requirements that emerged:
- ESP32-based (upgraded to S3 for better performance and PSRAM)
- E-ink display for low power and outdoor readability
- Battery powered with charging support
- Prefer an all-Adafruit (or Adafruit-sold) parts list for simplicity and support
- Plug-and-play STEMMA QT connections where possible

### Final Recommended Hardware (BOM)

| Qty | Item | Adafruit ID | Price |
|-----|------|-------------|-------|
| 1 | **FeatherS3[D] ESP32-S3** (Unexpected Maker) | 6399 | $24.95 |
| 1 | **2.9" Grayscale eInk FeatherWing** | 4777 | $22.50 |
| 1 | **PMSA003I Air Quality Breakout** | 4632 | $44.95 |
| 1 | **STEMMA QT cable** (50 mm or 100 mm) | 4399 / 4210 | ~$0.95 |
| 1 | **400 mAh LiPo battery** (Feather-sized) | 3898 | $6.95 |

**Approximate total: ~$100**

### Key design notes
- The FeatherS3[D] gives you 8 MB PSRAM, dual STEMMA QT ports, built-in LiPo charging + fuel gauge, and full FeatherWing compatibility.
- The 2.9" grayscale e-ink display stacks directly on top and stays readable in sunlight while drawing almost no power when static.
- The PMSA003I plugs in via STEMMA QT and reports PM1.0 / PM2.5 / PM10 + particle counts.
- The 400 mAh battery tucks under the stack and charges when USB-C is connected.

This setup prioritizes low power, outdoor usability, and straightforward assembly for monitoring Idaho wildfire smoke.
