"""
Project Anantha: Optic Nerve Server
=========================================================
Classifies COCO-detected objects into:
    • Living beings   → humans, animals, birds, etc.
    • Non-living      → vehicles, furniture, electronics, etc.

Target Hardware: ESP32-CAM (GC2145) via Wi-Fi Stream
"""

import argparse
import cv2
import time
from pathlib import Path
from ultralytics import YOLO

# ──────────────────────────────────────────────────────────────────────────────
# COCO class → category mapping
# ──────────────────────────────────────────────────────────────────────────────

LIVING_CLASSES = {
    # People
    "person",
    # Animals — domestic & farm
    "cat", "dog", "horse", "sheep", "cow", "elephant",
    "bear", "zebra", "giraffe",
    # Birds
    "bird",
    # Aquatic / other
    "fish",
}

NON_LIVING_CLASSES = {
    # Vehicles
    "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat",
    # Road objects
    "traffic light", "fire hydrant", "stop sign", "parking meter",
    # Outdoor
    "bench",
    # Sports
    "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket",
    # Kitchen / food (non-living once prepared)
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
    "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
    "hot dog", "pizza", "donut", "cake",
    # Furniture
    "chair", "couch", "potted plant", "bed", "dining table", "toilet",
    # Electronics
    "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    # Appliances
    "microwave", "oven", "toaster", "sink", "refrigerator",
    # Miscellaneous
    "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush", "umbrella", "handbag", "tie", "suitcase", "backpack",
}

# Colours (BGR) - OpenCV uses Blue, Green, Red
COLOR_LIVING     = (0, 220, 0)      # Green (Target)
COLOR_NON_LIVING = (0, 100, 255)    # Orange (Obstacle)
COLOR_UNKNOWN    = (180, 180, 180)  # Grey

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def classify(label: str) -> str:
    """Return 'Living', 'Non-Living', or 'Unknown' for a COCO class label."""
    label_lower = label.lower()
    if label_lower in LIVING_CLASSES:
        return "Living"
    if label_lower in NON_LIVING_CLASSES:
        return "Non-Living"
    return "Unknown"


def get_color(category: str):
    return {
        "Living": COLOR_LIVING,
        "Non-Living": COLOR_NON_LIVING,
    }.get(category, COLOR_UNKNOWN)


def draw_box(frame, box, label: str, conf: float, category: str):
    """Draw a labelled bounding box on the frame."""
    x1, y1, x2, y2 = map(int, box)
    color = get_color(category)

    # Box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    # Label background
    text = f"{label} ({category}) {conf:.2f}"
    (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    cv2.rectangle(frame, (x1, y1 - th - baseline - 4), (x1 + tw + 4, y1), color, -1)

    # Label text
    cv2.putText(
        frame, text,
        (x1 + 2, y1 - baseline - 2),
        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
        (255, 255, 255), 1, cv2.LINE_AA,
    )


def draw_legend(frame):
    """Draw a small legend in the top-right corner."""
    h, w = frame.shape[:2]
    items = [
        ("Living",     COLOR_LIVING),
        ("Non-Living", COLOR_NON_LIVING),
        ("Unknown",    COLOR_UNKNOWN),
    ]
    x_start = w - 160
    y_start = 12
    for i, (label, color) in enumerate(items):
        y = y_start + i * 22
        cv2.rectangle(frame, (x_start, y), (x_start + 16, y + 16), color, -1)
        cv2.putText(
            frame, label, (x_start + 22, y + 13),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA,
        )


def draw_summary(frame, counts: dict):
    """Show per-category counts at the bottom-left."""
    h = frame.shape[0]
    y = h - 10
    summary = " | ".join(f"{k}: {v}" for k, v in counts.items())
    cv2.putText(
        frame, summary,
        (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
        (255, 255, 255), 1, cv2.LINE_AA,
    )


def draw_fps(frame, fps: float):
    cv2.putText(
        frame, f"FPS: {fps:.1f}",
        (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
        (0, 255, 255), 2, cv2.LINE_AA,
    )

# ──────────────────────────────────────────────────────────────────────────────
# Core inference
# ──────────────────────────────────────────────────────────────────────────────

def process_frame(frame, model, conf_thresh: float):
    """Run YOLOv8 on a single frame and annotate it. Returns annotated frame."""
    results = model(frame, conf=conf_thresh, verbose=False)[0]
    counts = {"Living": 0, "Non-Living": 0, "Unknown": 0}

    for box in results.boxes:
        cls_id  = int(box.cls[0])
        label   = model.names[cls_id]
        conf    = float(box.conf[0])
        xyxy    = box.xyxy[0].tolist()
        category = classify(label)

        draw_box(frame, xyxy, label, conf, category)
        counts[category] += 1

    draw_legend(frame)
    draw_summary(frame, counts)
    return frame, counts


def run_inference(source, model_path: str, conf: float, save: bool, show: bool):
    print(f"\n[INFO] Loading AI Brain (Model) : {model_path}")
    model = YOLO(model_path)

    # Determine if source is an image or video/stream
    source_path = str(source)
    is_image = source_path.lower().endswith(
        (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
    )

    # ── Image ──────────────────────────────────────────────────────────────
    if is_image:
        print(f"[INFO] Processing image: {source_path}")
        frame = cv2.imread(source_path)
        if frame is None:
            raise FileNotFoundError(f"Could not read image: {source_path}")

        annotated, counts = process_frame(frame, model, conf)
        print(f"[INFO] Detections → {counts}")

        if show:
            cv2.imshow("Anantha Vision System", annotated)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        if save:
            out_path = Path(source_path).stem + "_annotated.jpg"
            cv2.imwrite(out_path, annotated)
            print(f"[INFO] Saved to: {out_path}")
        return

    # ── Video / Wi-Fi Stream ───────────────────────────────────────────────
    print(f"[INFO] Connecting to Optic Nerve at: {source_path}")
    
    # This automatically handles both webcams ("0") and Wi-Fi streams ("http://...")
    cap_source = int(source_path) if source_path.isdigit() else source_path
    
    # OpenCV Network Stream Buffer Settings (Helps with ESP32-CAM lag)
    cv2.setUseOptimized(True)
    cap = cv2.VideoCapture(cap_source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2) 

    if not cap.isOpened():
        raise RuntimeError(f"\n[ERROR] Cannot connect to camera. Is the ESP32-CAM powered on and connected to the Hotspot?")

    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    print(f"[INFO] Uplink Established! Resolution: {w}x{h} @ ~{fps:.1f} fps")

    writer = None
    if save and not source_path.isdigit():
        out_path = Path("video_output").stem + "_annotated.mp4"
        fourcc   = cv2.VideoWriter_fourcc(*"mp4v")
        writer   = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
        print(f"[INFO] Saving output to: {out_path}")

    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] Frame dropped or connection lost. Attempting to recover...")
                time.sleep(0.5)
                continue # Try to grab the next frame instead of crashing

            annotated, _ = process_frame(frame, model, conf)

            # FPS counter
            curr_time = time.time()
            draw_fps(annotated, 1.0 / max(curr_time - prev_time, 1e-6))
            prev_time = curr_time

            if writer:
                writer.write(annotated)

            if show:
                cv2.imshow("Anantha Vision System", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("\n[INFO] Vision System shut down by user.")
                    break
    finally:
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        print("[INFO] Ground Station Offline.")

# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Project Anantha: Living / Non-Living AI Detector"
    )
    parser.add_argument(
        # WE CHANGED THE DEFAULT SOURCE HERE TO YOUR ESP32-CAM IP ADDRESS!
        "--source", type=str, default="http://url/stream",# Enter the URL generated by ESP32 CAM Module
        help="Input source: Wi-Fi stream, webcam index, or image path",
    )
    parser.add_argument(
        "--model", type=str, default="yolov8n.pt",
        help="YOLOv8 model weights (default: yolov8n.pt)",
    )
    parser.add_argument(
        "--conf", type=float, default=0.35,
        help="Confidence threshold (default: 0.35)",
    )
    parser.add_argument(
        "--save", action="store_true",
        help="Save annotated output (image or video)",
    )
    parser.add_argument(
        "--no-show", action="store_true",
        help="Suppress display window (useful for headless servers)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_inference(
        source    = args.source,
        model_path= args.model,
        conf      = args.conf,
        save      = args.save,
        show      = not args.no_show,
    )
