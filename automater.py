# automator.py
"""
Automator: dry-run and replay workflows produced by analyzer.py
- Prefer anchor/template matching when available (more robust than absolute coords)
- Fall back to relative/absolute coordinates
- Wait for observable post-conditions (anchor/window/process/ocr) instead of blind sleeps
- Safe dry-run first; require explicit YES to execute
"""
import os
import json
import time
import cv2
import numpy as np
import pyautogui
from PIL import Image
import imagehash

# optional imports used by wait helpers
try:
    import psutil
except Exception:
    psutil = None

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    import pygetwindow as gw
except Exception:
    gw = None

pyautogui.FAILSAFE = True  # move mouse to corner to abort

WORKFLOWS = "workflows"
ANCHORS_DIR = "anchors"
os.makedirs(ANCHORS_DIR, exist_ok=True)

# -------------------
# Utilities
# -------------------
def compute_phash(path):
    """Compute perceptual hash (phash) for an image file."""
    try:
        h = imagehash.phash(Image.open(path))
        return str(h)
    except Exception:
        return None

def screenshot_to_cv2():
    """Take current screen screenshot and return as OpenCV BGR image."""
    img = pyautogui.screenshot()
    arr = np.array(img)              # RGB
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)  # BGR for OpenCV

def save_anchor(screenshot_path, x, y, w=120, h=60, out_path=None):
    """
    Crop around (x,y) from given screenshot_path and save anchor to out_path.
    Returns anchor_path.
    """
    img = cv2.imread(screenshot_path)
    if img is None:
        raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
    H, W = img.shape[:2]
    x0 = max(0, int(x - w // 2)); y0 = max(0, int(y - h // 2))
    x1 = min(W, x0 + w); y1 = min(H, y0 + h)
    crop = img[y0:y1, x0:x1]
    if out_path is None:
        base = os.path.splitext(os.path.basename(screenshot_path))[0]
        out_path = os.path.join(ANCHORS_DIR, f"{base}_{int(x)}_{int(y)}.png")
    cv2.imwrite(out_path, crop)
    return out_path

def find_anchor_on_screen(template_path, threshold=0.80):
    """
    Try to find the template (anchor) on the current screen using template matching.
    Returns center (x,y) of match if found else None.
    """
    if not os.path.exists(template_path):
        return None
    tpl = cv2.imread(template_path)
    if tpl is None:
        return None
    screen = screenshot_to_cv2()
    try:
        res = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
    except Exception:
        return None
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val >= threshold:
        top_left = max_loc
        th, tw = tpl.shape[:2]
        center = (int(top_left[0] + tw / 2), int(top_left[1] + th / 2))
        return center
    return None

def clean_ocr(text):
    """Simple OCR cleaning - keep useful lines and join."""
    if not text:
        return ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lines = [l for l in lines if len(l) > 2]
    lines = [l for l in lines if not any(k in l.lower() for k in ("©","all","unread","favourites","groups"))]
    return " — ".join(lines[:6])

# -------------------
# Wait-for helpers
# -------------------
def _wait_for_anchor(anchor_path, timeout=8, poll=0.25, threshold=0.80):
    """Wait until anchor template appears on screen or timeout. Returns center or None."""
    if not os.path.exists(anchor_path):
        return None
    start = time.time()
    while time.time() - start < timeout:
        pt = find_anchor_on_screen(anchor_path, threshold=threshold)
        if pt:
            return pt
        time.sleep(poll)
    return None

def _wait_for_anchor_gone(anchor_path, timeout=8, poll=0.25, threshold=0.80):
    """Wait until anchor is NOT found (useful for waiting for close)."""
    if not os.path.exists(anchor_path):
        return True
    start = time.time()
    while time.time() - start < timeout:
        pt = find_anchor_on_screen(anchor_path, threshold=threshold)
        if not pt:
            return True
        time.sleep(poll)
    return False

def _wait_for_ocr_contains(region=None, expected_text=None, timeout=10, poll=0.5):
    """
    region: (left, top, width, height) in screen coords. If None, uses full screen.
    expected_text: substring or list of substrings (any-of)
    Returns OCR text on success or None
    """
    if pytesseract is None:
        return None
    start = time.time()
    while time.time() - start < timeout:
        img = screenshot_to_cv2()
        if region:
            l, t, w, h = region
            l, t, w, h = int(l), int(t), int(w), int(h)
            crop = img[t:t+h, l:l+w]
        else:
            crop = img
        try:
            text = pytesseract.image_to_string(crop).strip()
        except Exception:
            text = ""
        if not text:
            time.sleep(poll); continue
        if isinstance(expected_text, (list, tuple)):
            if any(sub.lower() in text.lower() for sub in expected_text):
                return text
        else:
            if expected_text and expected_text.lower() in text.lower():
                return text
        time.sleep(poll)
    return None

def _wait_for_window_title_contains(substr, timeout=8, poll=0.5):
    """Try to detect a window title containing substr (requires pygetwindow)."""
    if gw is None:
        return None
    start = time.time()
    while time.time() - start < timeout:
        for wtitle in gw.getAllTitles():
            if substr.lower() in (wtitle or "").lower():
                return wtitle
        time.sleep(poll)
    return None

def _wait_for_process_name(name_substr, timeout=8, poll=0.5):
    """Wait for any process with name containing name_substr."""
    if psutil is None:
        return None
    start = time.time()
    while time.time() - start < timeout:
        for p in psutil.process_iter(['name']):
            try:
                nm = p.info.get('name') or ""
                if name_substr.lower() in nm.lower():
                    return True
            except Exception:
                continue
        time.sleep(poll)
    return False

# -------------------
# Workflow loading / dry-run
# -------------------
def load_workflow(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def dry_run(workflow):
    print("Dry run: sequence of actions to perform:")
    for s in workflow.get("steps", []):
        sid = s.get("step_id")
        action = s.get("action")
        details = s.get("details", {})
        ocr = s.get("ocr_text", "") or ""
        post = s.get("post_condition", {})
        print(f" - {sid}: {action} {details} (ocr: {ocr[:80]!r}) post={post}")

# -------------------
# Low-level actions
# -------------------
def _click_at_point(x, y, speed=1.0, clicks=1, interval=0.1):
    """Move and click. clicks=1 for single click, >1 for multi-clicks."""
    pyautogui.moveTo(x, y, duration=max(0.05, 0.15 * speed))
    if clicks == 1:
        pyautogui.click()
    else:
        pyautogui.click(clicks=clicks, interval=interval)

def _type_text(text, speed=1.0):
    pyautogui.typewrite(str(text), interval=0.01 * speed)

def _press_key(key):
    try:
        pyautogui.press(key)
    except Exception:
        pyautogui.typewrite(str(key))

# -------------------
# Replay logic with post-conditions & retries
# -------------------
def _resolve_click_point(step, anchor_threshold=0.80):
    """Return (x,y) or None using anchor, rel_coords, or absolute coords."""
    details = step.get("details", {}) or {}

    # 1) anchor-based
    anchor = step.get("anchor") or {}
    anchor_file = anchor.get("file") if isinstance(anchor, dict) else None
    if anchor_file and os.path.exists(anchor_file):
        found = find_anchor_on_screen(anchor_file, threshold=anchor_threshold)
        if found:
            return found

    # 2) relative coords
    rel = step.get("rel_coords")
    if rel and isinstance(rel, (list, tuple)) and len(rel) >= 2:
        screen_w, screen_h = pyautogui.size()
        return (int(rel[0] * screen_w), int(rel[1] * screen_h))

    # 3) absolute coords in details
    x = details.get("x") or details.get("abs_x") or details.get("abs_coords_x")
    y = details.get("y") or details.get("abs_y") or details.get("abs_coords_y")
    if x is not None and y is not None:
        try:
            return (int(x), int(y))
        except Exception:
            return None

    return None

def replay(workflow, speed=1.0, anchor_threshold=0.80, default_retry=1):
    """
    Execute the workflow.
    Each step may include an optional 'post_condition' dict, for example:
      {"type":"anchor_appears","file":"anchors/x.png","timeout":6}
      {"type":"anchor_gone","file":"anchors/x.png","timeout":6}
      {"type":"ocr_contains","region":[l,t,w,h],"text":"Search results","timeout":10}
      {"type":"window_title","text":"YouTube","timeout":8}
      {"type":"process","name":"chrome","timeout":6}
    post_condition may also include: "retries": N and "fallback_sleep": seconds
    """
    print("Starting replay in 5 seconds. Move mouse to top-left corner to abort.")
    time.sleep(5)

    steps = workflow.get("steps", [])
    for s in steps:
        sid = s.get("step_id")
        act = s.get("action")
        details = s.get("details", {}) or {}
        post = s.get("post_condition") or {}
        retries = int(post.get("retries", default_retry))
        performed = False

        for attempt in range(1, retries + 1):
            if attempt > 1:
                print(f"[Automator] RETRY {attempt}/{retries} for step {sid}")

            # determine target
            click_point = _resolve_click_point(s, anchor_threshold=anchor_threshold)

            # perform action
            try:
                if act in ("mouse_click", "click"):
                    if click_point:
                        # allow step to request multi-clicks via details e.g., {"clicks":1}
                        clicks = int(details.get("clicks", 1))
                        interval = float(details.get("click_interval", 0.08))
                        _click_at_point(click_point[0], click_point[1], speed=speed, clicks=clicks, interval=interval)
                        print(f"[Automator] CLICK {sid} -> {click_point} (clicks={clicks})")
                    else:
                        print(f"[Automator] No click target for {sid}; skipping action")
                elif act in ("key_down", "type", "type_text"):
                    k = details.get("key") or details.get("text") or s.get("text")
                    if k is not None:
                        _type_text(k, speed=speed)
                        print(f"[Automator] TYPE {sid} -> {k!r}")
                    else:
                        print(f"[Automator] No text/key for {sid}; skipping")
                elif act in ("press", "key_press"):
                    k = details.get("key")
                    if k:
                        _press_key(k)
                        print(f"[Automator] PRESS {sid} -> {k}")
                    else:
                        print(f"[Automator] No key specified for {sid}; skipping")
                else:
                    print(f"[Automator] Unsupported action '{act}' in {sid}")
            except Exception as e:
                print(f"[Automator] Error performing action for {sid}: {e}")

            # wait for post-condition if provided
            ok = True
            if post:
                ptype = post.get("type")
                timeout = float(post.get("timeout", 8))
                poll = float(post.get("poll", 0.25))
                if ptype == "anchor_appears" and post.get("file"):
                    ok_point = _wait_for_anchor(post["file"], timeout=timeout, poll=poll, threshold=anchor_threshold)
                    ok = bool(ok_point)
                elif ptype == "anchor_gone" and post.get("file"):
                    ok = _wait_for_anchor_gone(post["file"], timeout=timeout, poll=poll, threshold=anchor_threshold)
                elif ptype == "ocr_contains" and post.get("text"):
                    region = post.get("region")
                    res = _wait_for_ocr_contains(region=region, expected_text=post["text"], timeout=timeout, poll=poll)
                    ok = bool(res)
                elif ptype == "window_title" and post.get("text"):
                    res = _wait_for_window_title_contains(post["text"], timeout=timeout, poll=poll)
                    ok = bool(res)
                elif ptype == "process" and post.get("name"):
                    res = _wait_for_process_name(post["name"], timeout=timeout, poll=poll)
                    ok = bool(res)
                else:
                    # unknown or unsupported post-condition -> fallback sleep
                    fb = float(post.get("fallback_sleep", 0.25))
                    time.sleep(fb)
                    ok = True

                if ok:
                    print(f"[Automator] Post-condition satisfied for {sid}: {post}")
                    performed = True
                    break  # success -> proceed to next step
                else:
                    print(f"[Automator] Post-condition NOT satisfied for {sid}: {post} (attempt {attempt})")
                    # if configured, wait fallback before retrying
                    fallback = float(post.get("retry_wait", 0.5))
                    time.sleep(fallback)
                    continue  # retry

            else:
                # no post-condition -> small pause to let UI react
                time.sleep(0.25 * speed)
                performed = True
                break

        # if after retries still not ok, log and continue (or you can decide to abort here)
        if not performed:
            print(f"[Automator] WARNING: step {sid} failed post-conditions after {retries} attempts. Continuing.")

# -------------------
# CLI
# -------------------
if __name__ == "__main__":
    flows = sorted([f for f in os.listdir(WORKFLOWS) if f.endswith(".json")])
    if not flows:
        print("No workflows found. Run analyzer.py first.")
        exit(1)
    print("Workflows:")
    for i, f in enumerate(flows):
        print(i, f)
    try:
        idx = int(input("Choose workflow index to run: "))
    except Exception:
        print("Invalid input.")
        exit(1)
    wf = load_workflow(os.path.join(WORKFLOWS, flows[idx]))
    dry_run(wf)
    ok = input("Type YES to run this workflow (will send real input): ")
    if ok.strip().upper() == "YES":
        replay(wf)
    else:
        print("Aborted.")
