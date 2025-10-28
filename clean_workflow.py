"""
Clean workflow files produced by analyzer.py into minimal, LLM-friendly form.

Usage:
    python clean_workflow.py workflows/workflow_<session>.json
Output:
    clean_workflows/cleaned_<session>.json
"""

import os
import json
import re
from datetime import datetime

RAW_DIR = "clean_workflows"
CLEAN_DIR = os.path.join(RAW_DIR)
os.makedirs(CLEAN_DIR, exist_ok=True)


def simplify_text(text: str, max_len: int = 60) -> str:
    """
    Strip noisy OCR text and keep meaningful words.
    """
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    # Remove common UI artifacts but keep useful context
    text = re.sub(r"(File|Edit|View|Help|Terminal|Selection)(?=\s|$)", "", text)
    text = text.strip()
    
    # Truncate if too long
    if len(text) > max_len:
        text = text[:max_len] + "..."
    
    return text


def format_modifiers(modifiers):
    """Format modifier keys in a readable way."""
    if not modifiers:
        return ""
    return "+".join([m.capitalize() for m in modifiers]) + "+"


def clean_step(step, step_num):
    """
    Convert a noisy analyzer step into a human-readable action description.
    Returns dict with action details for LLM consumption.
    """
    action = step.get("action", "")
    details = step.get("details", {})
    key = details.get("key", "")
    modifiers = details.get("modifiers", [])
    ocr = simplify_text(step.get("ocr_text", ""))
    transcripts = step.get("transcripts", [])
    
    # Build readable action description
    action_desc = ""
    action_type = ""
    target = ""
    
    if action == "mouse_click":
        action_type = "click"
        button = details.get("button", "Button.left").replace("Button.", "")
        x, y = details.get("x", 0), details.get("y", 0)
        
        if ocr:
            action_desc = f"Clicked ({button}) near: '{ocr}'"
            target = ocr
        else:
            action_desc = f"Clicked ({button}) at position ({x}, {y})"
            target = f"({x}, {y})"
            
    elif action == "key_down":
        action_type = "keyboard"
        
        # Handle keyboard shortcuts
        if modifiers:
            mod_str = format_modifiers(modifiers)
            # Clean up key representation
            if isinstance(key, str):
                if key.startswith("Key."):
                    key_clean = key.replace("Key.", "").capitalize()
                elif len(key) == 1:
                    key_clean = key.upper()
                else:
                    key_clean = key
            else:
                key_clean = str(key)
            
            action_desc = f"Pressed shortcut: {mod_str}{key_clean}"
            target = f"{mod_str}{key_clean}"
            
        else:
            # Regular key press
            if "enter" in key.lower():
                action_desc = "Pressed Enter"
                target = "Enter"
            elif "tab" in key.lower():
                action_desc = "Pressed Tab"
                target = "Tab"
            elif "delete" in key.lower():
                action_desc = "Pressed Delete"
                target = "Delete"
            elif "backspace" in key.lower():
                action_desc = "Pressed Backspace"
                target = "Backspace"
            elif "esc" in key.lower():
                action_desc = "Pressed Escape"
                target = "Escape"
            elif len(key) == 1 and key.isalpha():
                action_desc = f"Typed: '{key}'"
                target = key
            elif len(key) == 1:
                action_desc = f"Typed: '{key}'"
                target = key
            else:
                key_clean = key.replace("Key.", "").capitalize() if key.startswith("Key.") else key
                action_desc = f"Pressed: {key_clean}"
                target = key_clean
                
        # Add context from OCR if available
        if ocr and "Pressed shortcut" in action_desc:
            action_desc += f" (Context: {ocr})"
            
    elif action == "type_text":
        action_type = "typing"
        text = details.get("text", "") or step.get("text", "")
        if text:
            action_desc = f"Typed text: '{text}'"
            target = text
        else:
            action_desc = "Typed some text"
            target = ""
            
    elif action == "mouse_scroll":
        action_type = "scroll"
        dx, dy = details.get("dx", 0), details.get("dy", 0)
        direction = "up" if dy > 0 else "down" if dy < 0 else "horizontally"
        action_desc = f"Scrolled {direction}"
        target = direction
        
    else:
        action_type = action
        action_desc = f"Performed: {action}"
        target = ""
    
    result = {
        "step": step_num,
        "action_type": action_type,
        "description": action_desc,
        "target": target
    }
    
    # Add transcripts if available
    if transcripts:
        result["transcripts"] = transcripts
    
    return result


def generate_natural_summary(steps):
    """
    Generate a natural language summary of the workflow.
    """
    if not steps:
        return "No actions performed."
    
    actions = []
    for s in steps:
        desc = s.get("description", "")
        if desc:
            actions.append(desc.replace("Pressed shortcut:", "→").replace("Typed:", "typed"))
    
    # Group consecutive typing
    summary_parts = []
    i = 0
    while i < len(actions):
        if "typed" in actions[i].lower():
            # Collect consecutive typing
            typed = []
            while i < len(actions) and "typed" in actions[i].lower():
                typed.append(actions[i])
                i += 1
            if len(typed) > 3:
                summary_parts.append(f"Typed multiple characters")
            else:
                summary_parts.extend(typed)
        else:
            summary_parts.append(actions[i])
            i += 1
    
    return " → ".join(summary_parts[:15])  # Limit to first 15 actions


def clean_workflow(infile):
    """
    Read raw workflow_<session>.json and output cleaned_<session>.json
    with LLM-friendly format.
    """
    with open(infile, "r", encoding="utf-8") as f:
        raw = json.load(f)

    session_id = raw.get("session", "unknown")
    generated_at = raw.get("generated_at", "")
    summary = raw.get("summary", "")
    steps = raw.get("steps", [])
    
    # Clean each step
    clean_steps = []
    step_num = 1
    for s in steps:
        if isinstance(s, dict):
            # Skip mouse release events and redundant moves
            action = s.get("action", "")
            details = s.get("details", {})
            
            # Skip mouse release events
            if action == "mouse_click" and not details.get("pressed", True):
                continue
            
            # Skip mouse move events (too noisy)
            if action == "mouse_move":
                continue
                
            cleaned = clean_step(s, step_num)
            clean_steps.append(cleaned)
            step_num += 1

    # Remove consecutive duplicate actions
    deduped = []
    for i, s in enumerate(clean_steps):
        if i == 0 or s["description"] != clean_steps[i-1]["description"]:
            deduped.append(s)

    # Generate natural language summary
    natural_summary = generate_natural_summary(deduped)
    
    # Create LLM-friendly output
    cleaned = {
        "metadata": {
            "session_id": session_id,
            "recorded_at": generated_at,
            "total_steps": len(deduped),
            "original_summary": summary
        },
        "workflow_summary": natural_summary,
        "actions": deduped,
        "llm_prompt_template": (
            "This workflow shows a user performing the following actions:\n"
            f"{natural_summary}\n\n"
            "Detailed steps:\n" + 
            "\n".join([f"{i+1}. {s['description']}" for i, s in enumerate(deduped)])
        )
    }

    # Save cleaned workflow
    session_name = session_id if session_id != "unknown" else os.path.basename(infile).replace(".json", "")
    outpath = os.path.join(CLEAN_DIR, f"cleaned_{session_name}.json")
    
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    # Also save a plain text version for easy LLM ingestion
    txt_outpath = outpath.replace(".json", ".txt")
    with open(txt_outpath, "w", encoding="utf-8") as f:
        f.write(f"SESSION: {session_id}\n")
        f.write(f"RECORDED: {generated_at}\n")
        f.write(f"TOTAL ACTIONS: {len(deduped)}\n")
        f.write(f"\nWORKFLOW SUMMARY:\n{natural_summary}\n")
        f.write(f"\n{'='*60}\n")
        f.write(f"DETAILED ACTIONS:\n")
        f.write(f"{'='*60}\n\n")
        
        for i, step in enumerate(deduped, 1):
            f.write(f"Step {i}: {step['description']}\n")
            if "transcripts" in step and step["transcripts"]:
                f.write(f"  Transcripts: {', '.join(step['transcripts'])}\n")
            f.write("\n")

    print(f"✓ Cleaned JSON workflow: {outpath}")
    print(f"✓ Plain text version: {txt_outpath}")
    print(f"\n📋 Summary: {natural_summary}")
    print(f"📊 Total actions: {len(deduped)}")
    
    return cleaned


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python clean_workflow.py workflows/workflow_<session>.json")
        sys.exit(1)

    infile = sys.argv[1]
    if not os.path.exists(infile):
        print(f"❌ File not found: {infile}")
        sys.exit(1)

    clean_workflow(infile)