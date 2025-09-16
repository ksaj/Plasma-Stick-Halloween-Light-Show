# Halloween Plasma Stick 2040 W – Spooky Lights + Lightning

This project runs on the Pimoroni Plasma Stick 2040 W (RP2040 with WS2812/NeoPixel LED support).
It produces a slowly shifting spooky color fade with a warped, uneasy speed, and adds random lightning bursts.
You can also press the BOOT/SEL button to trigger lightning immediately.

## Features

- Spooky color palette crossfade
  - Any number of colors supported (RGB tuples in the `HALLOWEEN_COLORS` list).
  - Fade speed is uneasy: it speeds up and slows down cyclically for an unsettling effect.
- Random lightning storms
  - Flashes happen on average every ~18 seconds.
  - Each burst has 2–5 flashes with noisy decay and occasional extra flickers.
  - Bright, cold blue-white lightning overrides the ambient palette.
- Interactive control
  - Short press BOOT/SEL -> trigger lightning instantly.
  - (Long press is unused for now, but can be extended.)
- Safe exit
  - Press Ctrl+C in Thonny (or REPL) to stop the program; LEDs will clear.

## Installation Steps

1) Set up the Plasma Stick
   - Plug in the Plasma Stick 2040 W via USB.
   - If it does not show up in Thonny, hold down BOOT/SEL while plugging in to enter UF2 bootloader mode.
   - Install MicroPython for Pimoroni Plasma Stick (download from Pimoroni or the Raspberry Pi UF2 firmware page).

2) Install Thonny IDE
   - Download Thonny from https://thonny.org.
   - Open Thonny, select Interpreter -> MicroPython (Raspberry Pi RP2040).
   - Choose the COM/serial port for the Plasma Stick.

3) Copy the code
   - Save the program as `main.py`.
   - In Thonny, use File -> Save As... -> Raspberry Pi Pico and name it `main.py`.
   - This ensures the script auto-runs on boot.

4) Connect the LED strip
   - Connect your WS2812/NeoPixel strip to the Plasma Stick JST-SM output (or GPIO pin if using breakout wiring).
   - Ensure GND is common between board and LEDs.
   - Power the LEDs — for more than ~50 LEDs, consider an external 5V supply.

5) Reboot and enjoy
   - Reset or power-cycle the Plasma Stick.
   - The LEDs will fade through spooky colors with occasional lightning strikes.
   - Press BOOT/SEL for instant lightning.

## Configuration

Inside `main.py`, you can adjust:

- LED count
  ```python
  NUM_LEDS = 50
  ```

- Spooky palette (add or remove as many colors as you like)
  ```python
  HALLOWEEN_COLORS = [
      (170, 255, 80),   # toxic green
      (120, 10, 150),   # deep purple
      (255, 225, 90),   # lantern yellow
      (255, 90, 20),    # blood orange
      (30, 180, 60),    # swamp green
      (190, 40, 140),   # bruise magenta
      (255, 190, 40),   # pumpkin glow
      (80, 0, 110),     # midnight violet
  ]
  ```
  The fade engine automatically cycles through the list.
  The full cycle length equals `len(HALLOWEEN_COLORS) * FADE_MS`.

- Fade behavior
  ```python
  FADE_MS = 30000          # ms per transition between palette colors
  UNEASY_PERIOD_MS = 15000 # how often speed cycles (faster/slower)
  UNEASY_DEPTH = 0.6       # 0..1, strength of the speed modulation
  ```

- Lightning behavior
  ```python
  MEAN_INTERVAL_S = 18.0      # average seconds between random bursts
  FLASHES_MIN_MAX = (2, 5)    # flashes per burst
  FLASH_MS_MIN_MAX = (22, 58) # ms per hard flash
  DECAY_MS = 140              # decay tail length
  POST_FLICKER_PROB = 0.35    # chance of an extra flicker
  ```

- Brightness
  ```python
  BASE_BRIGHT = 0.28  # overall ambient brightness
  ```

## Tips

- Want denser lightning storms? Lower `MEAN_INTERVAL_S`.
- Want shorter fades? Reduce `FADE_MS`.
- Want the palette to feel calmer? Set `UNEASY_DEPTH = 0.2`.
- Need to disable lightning? Comment out calls to `lightning.maybe_trigger()` and `lightning.render()`.

## Safety Notes

- At higher brightness, a long LED strip can draw significant current.
  - Example: 50 LEDs at full white can draw up to about 3A.
  - Use an external 5V supply for large strips.
- Always share GND between Plasma Stick and LED strip.
- Keep USB-powered brightness moderate (BASE_BRIGHT <= 0.3 is generally safe).

## License

This project is released under the Unlicense / Public Domain.
Use, modify, and share freely.
