# main.py
# Plasma Stick 2040 W (MicroPython, Pimoroni `plasma` API)
# Spooky slow palette crossfade + random lightning bursts.
# Short-press BOOT/SEL => trigger lightning immediately.
# NEW: Palette speed warps up and down for uneasy effect.

import time, math, random
import plasma

# ---------------------- Config ----------------------
NUM_LEDS      = 50
FPS           = 60
COLOR_ORDER   = plasma.COLOR_ORDER_RGB

BASE_BRIGHT   = 0.28
FADE_MS       = 30000         # base ms per palette transition

# Uneasy time warp
UNEASY_PERIOD_MS = 15000      # one full speed-up/slow-down cycle (15s)
UNEASY_DEPTH     = 0.6        # 0..1 (how much the speed swings; 0.6 = ±60%)

HALLOWEEN_COLORS = [
    (170, 255, 80),   # toxic green
    (120, 10, 150),   # deep purple
    (255, 225, 90),   # lantern yellow
    (255, 90, 20),    # blood orange
    (30, 180, 60),    # swamp green
    (190, 40, 140),   # bruise magenta
    (255, 190, 40),   # pumpkin glow
    (80, 0, 110),     # midnight violet
    (255, 60, 0),     # fiery red
    (20, 40, 255),    # electric blue
    (255, 130, 200),  # ghostly pink
    (100, 255, 200),  # ectoplasm teal
]

# Lightning
MEAN_INTERVAL_S   = 18.0
FLASHES_MIN_MAX   = (2, 5)
FLASH_MS_MIN_MAX  = (22, 58)
DECAY_MS          = 140
POST_FLICKER_PROB = 0.35
POST_FLICKER_MS   = 90

LIGHTNING_H       = 220/360.0
LIGHTNING_S       = 0.08
LIGHTNING_V_PEAK  = 1.0

# Button
LONGPRESS_MS      = 700
BUTTON_GPIO       = None

# ---------------------- Strip -----------------------
led_strip = plasma.WS2812(NUM_LEDS, color_order=COLOR_ORDER)
led_strip.start()

# ---------------------- Utils -----------------------
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x

def ease(t):
    return t*t*t*(t*(t*6 - 15) + 10)

def _now_ms():
    return time.ticks_ms()

def _fade_palette(t_ms, B, colors, fade_ms):
    n = len(colors)
    if n < 1:
        return
    cycle_ms = max(1, n * fade_ms)

    for idx in range(NUM_LEDS):
        offset = (idx / max(1, NUM_LEDS - 1)) * fade_ms
        t = (t_ms + offset) % cycle_ms
        fade_pos = t / fade_ms
        i = int(fade_pos) % n
        j = (i + 1) % n
        f = fade_pos - int(fade_pos)
        ff = ease(f)

        r1, g1, b1 = [c/255.0 for c in colors[i]]
        r2, g2, b2 = [c/255.0 for c in colors[j]]
        r = (r1 + (r2 - r1) * ff) * B
        g = (g1 + (g2 - g1) * ff) * B
        b = (b1 + (b2 - b1) * ff) * B

        led_strip.set_rgb(idx,
                          int(255 * clamp(r)),
                          int(255 * clamp(g)),
                          int(255 * clamp(b)))

# ---------------------- Button ----------------------
def _noop_bootsel(): return False
read_bootsel = _noop_bootsel
_bootsel_available = False

try:
    from machine import bootsel_button as _bootsel_button
    def read_bootsel():
        try: return bool(_bootsel_button())
        except: return False
    _bootsel_available = True
except Exception:
    try:
        from rp2 import bootsel_button as _rp2_bootsel_button
        def read_bootsel():
            try: return bool(_rp2_bootsel_button())
            except: return False
        _bootsel_available = True
    except Exception:
        pass

try:
    from machine import Pin
except Exception:
    Pin = None

_btn_pin = None
if BUTTON_GPIO is not None and Pin is not None:
    try: _btn_pin = Pin(BUTTON_GPIO, Pin.IN, Pin.PULL_UP)
    except Exception: _btn_pin = None

def _read_button_fallback():
    if _btn_pin is None: return False
    try: return _btn_pin.value() == 0
    except Exception: return False

def read_button():
    return read_bootsel() if _bootsel_available else _read_button_fallback()

def _poll_button(now_ms, state):
    pressed = read_button()
    if pressed and not state["down"]:
        state["down"] = True
        state["t0"] = now_ms
    elif not pressed and state["down"]:
        dt = time.ticks_diff(now_ms, state["t0"] or now_ms)
        state["down"] = False
        return "long" if dt >= LONGPRESS_MS else "short"
    return None

# ---------------------- Lightning -------------------
def _rand_exp_ms(mean_ms):
    u = 1.0 - random.random()
    return int(-mean_ms * math.log(u))

def _burst_origin_seed(plan):
    if not plan:
        return random.randint(0, max(0, NUM_LEDS - 1))
    seed = plan[0][0] & 0xFFFFFFFF
    seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
    return seed % max(1, NUM_LEDS)

class Lightning:
    def __init__(self):
        self.active = False
        self.next_ms = _now_ms() + _rand_exp_ms(MEAN_INTERVAL_S * 1000.0)
        self.plan = []

    def _make_burst(self, start_ms):
        n_flashes = random.randint(*FLASHES_MIN_MAX)
        gap_ms    = 40 + random.randint(0, 160)
        t = start_ms
        plan = []
        for _ in range(n_flashes):
            d_flash = random.randint(*FLASH_MS_MIN_MAX)
            t_start = t
            t_end   = t_start + d_flash
            t_decay = t_end + DECAY_MS
            plan.append((t_start, t_end, t_decay))
            t = t_end + gap_ms + random.randint(-20, 60)
        if random.random() < POST_FLICKER_PROB:
            d_flash = 14 + random.randint(0, POST_FLICKER_MS)
            t_start = t + random.randint(60, 220)
            t_end   = t_start + d_flash
            t_decay = t_end + int(DECAY_MS * 0.6)
            plan.append((t_start, t_end, t_decay))
        return plan

    def maybe_trigger(self, now):
        if self.active or now < self.next_ms:
            return
        self.plan = self._make_burst(now)
        self.active = True

    def trigger_now(self, now):
        self.plan = self._make_burst(now)
        self.active = True
        self.next_ms = now + _rand_exp_ms(MEAN_INTERVAL_S * 1000.0)

    def render(self, now):
        if not self.active:
            return False

        intensity = 0.0
        any_alive = False
        for (t0, t1, t2) in self.plan:
            if now < t0:
                any_alive = True
                continue
            if now <= t1:
                any_alive = True
                ph = (now - t0) / max(1, (t1 - t0))
                intensity = max(intensity, 0.85 + 0.15 * math.sin(ph * math.pi))
            elif now <= t2:
                any_alive = True
                d = (now - t1) / max(1, (t2 - t1))
                noise = (random.random() - 0.5) * 0.12
                intensity = max(intensity, clamp(1.0 - d*1.1 + noise, 0.0, 1.0))

        if not any_alive:
            self.active = False
            self.plan = []
            self.next_ms = now + _rand_exp_ms(MEAN_INTERVAL_S * 1000.0)
            return False

        if intensity <= 0.001:
            return False

        v = clamp(LIGHTNING_V_PEAK * intensity, 0.0, 1.0)
        origin = _burst_origin_seed(self.plan)
        for i in range(NUM_LEDS):
            dx = abs(i - origin)
            fall = 1.0 / (1.0 + 0.06 * (dx*dx))
            vv = clamp(v * (0.85 + 0.15 * random.random()) * fall, 0.0, 1.0)
            led_strip.set_hsv(i, LIGHTNING_H, LIGHTNING_S, vv)
        return True

# ---------------------- Runtime ----------------------
def run():
    lightning = Lightning()
    state = {"down": False, "t0": None}
    warped_time = 0  # accumulator for uneasy fade timing

    print("[halloween] spooky fade + uneasy speed + lightning. LEDs:", NUM_LEDS)

    last_ms = _now_ms()
    while True:
        now = _now_ms()
        dt = time.ticks_diff(now, last_ms)
        last_ms = now

        # Uneasy time warp factor
        ph = (now % UNEASY_PERIOD_MS) / UNEASY_PERIOD_MS
        speed = 1.0 + UNEASY_DEPTH * math.sin(ph * 2*math.pi)
        warped_time += dt * speed

        # Ambient palette
        _fade_palette(int(warped_time), BASE_BRIGHT, HALLOWEEN_COLORS, FADE_MS)

        # Lightning
        lightning.maybe_trigger(now)
        lightning.render(now)

        # Button
        ev = _poll_button(now, state)
        if ev == "short":
            lightning.trigger_now(now)

        # FPS pacing
        if FPS > 0:
            elapsed = time.ticks_diff(_now_ms(), now)
            delay = max(0, int(1000/FPS) - elapsed)
            if delay:
                time.sleep_ms(delay)

# ---------------------- Main -------------------------
try:
    run()
except KeyboardInterrupt:
    for i in range(NUM_LEDS):
        led_strip.set_hsv(i, 0, 0, 0)
    print("\n[halloween] stopped; LEDs off.")

