"""
Story image generation boundary.

The story pipeline always creates stable image paths and prompts. Actual image
file generation is intentionally provider-based so the backend can run before
the final image model is chosen.
"""

import os
import random
import time
from io import BytesIO
from typing import Optional

import requests

from shared.settings import (
    COMFYUI_BASE_URL,
    COMFYUI_CFG,
    COMFYUI_CHECKPOINT,
    COMFYUI_HEIGHT,
    COMFYUI_TABLET_HEIGHT,
    COMFYUI_TABLET_DENOISE,
    COMFYUI_TABLET_MODE,
    COMFYUI_TABLET_WIDTH,
    COMFYUI_OUTPAINT_FEATHERING,
    COMFYUI_SAMPLER,
    COMFYUI_SCHEDULER,
    COMFYUI_STEPS,
    COMFYUI_WIDTH,
    GENERATE_TABLET_IMAGES,
    IMAGE_OUTPUT_DIR,
    IMAGE_PROVIDER,
    IMAGE_REFERENCE,
    IMAGE_STYLE_GUIDE,
    TABLET_IMAGE_SUFFIX,
)
from shared.models import StoryPage


def build_image_path(
    book_id: str,
    episode: int,
    page_number: int,
    output_dir: Optional[str] = None,
) -> str:
    directory = output_dir or IMAGE_OUTPUT_DIR
    return str(os.path.join(directory, f"{book_id}_ep{episode}_p{page_number}.png"))


def build_tablet_image_path(image_path: str) -> str:
    stem, ext = os.path.splitext(image_path)
    return f"{stem}{TABLET_IMAGE_SUFFIX}{ext or '.png'}"


def attach_planned_image_paths(
    pages: list[StoryPage],
    *,
    book_id: str,
    episode: int,
    output_dir: Optional[str] = None,
) -> list[str]:
    paths = []
    for page in pages:
        page.image_path = build_image_path(book_id, episode, page.page_number, output_dir)
        paths.append(page.image_path)
    return paths


def generate_story_images(
    pages: list[StoryPage],
    *,
    book_id: str,
    episode: int,
    output_dir: Optional[str] = None,
) -> list[str]:
    """
    Generate one image per story page.

    IMAGE_PROVIDER=none keeps the paths/prompts only. This is useful while the
    final image backend is undecided. Once a provider is chosen, implement it
    here without touching the rest of the lesson pipeline.
    """
    paths = attach_planned_image_paths(
        pages, book_id=book_id, episode=episode, output_dir=output_dir
    )

    if IMAGE_PROVIDER == "none":
        return paths

    if IMAGE_PROVIDER == "comfyui":
        ensure_image_output_dir(output_dir)
        for page in pages:
            _generate_page_with_comfyui(page)
        return paths

    raise ValueError(f"Unsupported IMAGE_PROVIDER: {IMAGE_PROVIDER}")


def build_final_image_prompt(page: StoryPage, *, layout: str = "mobile") -> str:
    reference_note = (
        f"Use this reference image for style consistency: {IMAGE_REFERENCE}"
        if IMAGE_REFERENCE
        else "Use the shared style guide exactly for consistency."
    )
    if layout == "tablet":
        composition = (
            "iPad landscape 4:3 composition, fill the full wide canvas, keep every "
            "important character and action inside the central safe area, no side bars"
        )
        output = "One iPad landscape 4:3 story illustration."
    else:
        composition = (
            "portrait mobile composition, keep the important character and action "
            "inside the central safe area"
        )
        output = "One portrait mobile story illustration."

    return f"""{page.image_prompt}

{IMAGE_STYLE_GUIDE}

Consistency requirement:
- The full lesson must look like one illustrated book by the same artist.
- Keep the protagonist identical across all pages.
- Same line weight, color palette, lighting, shading, and responsive framing.
- Use {composition}.
- {reference_note}

Output:
- {output}
- No UI chrome, buttons, captions, watermarks, or text inside the image."""


def ensure_image_output_dir(output_dir: Optional[str] = None) -> None:
    os.makedirs(output_dir or IMAGE_OUTPUT_DIR, exist_ok=True)


def _generate_page_with_comfyui(page: StoryPage) -> None:
    if not page.image_path:
        raise ValueError("StoryPage.image_path must be set before image generation.")

    prompt = build_final_image_prompt(page, layout="mobile")
    workflow = _build_sdxl_workflow(
        prompt,
        width=COMFYUI_WIDTH,
        height=COMFYUI_HEIGHT,
        filename_prefix="lion_story_mobile",
    )
    prompt_id = _queue_comfyui_prompt(workflow)
    output = _wait_for_comfyui_image(prompt_id)
    image_bytes = _download_comfyui_image(output)

    with open(page.image_path, "wb") as f:
        f.write(image_bytes)

    if GENERATE_TABLET_IMAGES:
        tablet_path = build_tablet_image_path(page.image_path)
        if COMFYUI_TABLET_MODE == "outpaint":
            _outpaint_tablet_image_with_comfyui(page, tablet_path)
        elif COMFYUI_TABLET_MODE == "generate":
            _generate_tablet_image_with_comfyui(page, tablet_path)
        else:
            raise ValueError(f"Unsupported COMFYUI_TABLET_MODE: {COMFYUI_TABLET_MODE}")


def _generate_tablet_image_with_comfyui(page: StoryPage, tablet_path: str) -> None:
    tablet_prompt = build_final_image_prompt(page, layout="tablet")
    _generate_image_from_prompt(tablet_prompt, tablet_path, filename_prefix="lion_story_tablet")


def generate_tablet_image_from_prompt(image_prompt: str, output_path: str) -> str:
    prompt = build_tablet_prompt_from_image_prompt(image_prompt)
    _generate_image_from_prompt(prompt, output_path, filename_prefix="lion_story_tablet")
    return output_path


def _generate_image_from_prompt(prompt: str, output_path: str, *, filename_prefix: str) -> None:
    tablet_workflow = _build_sdxl_workflow(
        prompt,
        width=COMFYUI_TABLET_WIDTH,
        height=COMFYUI_TABLET_HEIGHT,
        filename_prefix=filename_prefix,
    )
    tablet_prompt_id = _queue_comfyui_prompt(tablet_workflow)
    tablet_output = _wait_for_comfyui_image(tablet_prompt_id)
    tablet_image_bytes = _download_comfyui_image(tablet_output)
    _write_image_bytes(output_path, tablet_image_bytes)


def build_tablet_prompt_from_image_prompt(image_prompt: str) -> str:
    return f"""{image_prompt}

{IMAGE_STYLE_GUIDE}

Output:
- One iPad landscape 4:3 children's storybook illustration.
- Fill the full wide canvas naturally.
- Keep all important characters and story action inside the central safe area.
- Use the same cute character design, warm lighting, clean line weight, and cheerful palette.
- No UI chrome, buttons, captions, watermarks, or text inside the image."""


def _outpaint_tablet_image_with_comfyui(page: StoryPage, tablet_path: str) -> None:
    if not page.image_path:
        raise ValueError("StoryPage.image_path must be set before tablet outpainting.")

    prepared = _prepare_tablet_outpaint_source(page.image_path)
    uploaded_name = _upload_comfyui_image(prepared["image_bytes"], prepared["filename"])
    prompt = build_outpaint_image_prompt(page)
    workflow = _build_sdxl_outpaint_workflow(
        prompt,
        uploaded_image=uploaded_name,
        left=prepared["left"],
        right=prepared["right"],
        top=prepared["top"],
        bottom=prepared["bottom"],
        filename_prefix="lion_story_tablet_outpaint",
    )
    prompt_id = _queue_comfyui_prompt(workflow)
    output = _wait_for_comfyui_image(prompt_id)
    image_bytes = _download_comfyui_image(output)

    with open(tablet_path, "wb") as f:
        f.write(image_bytes)


def outpaint_existing_image_for_tablet(
    image_path: str,
    *,
    output_path: str | None = None,
    prompt: str | None = None,
) -> str:
    tablet_path = output_path or build_tablet_image_path(image_path)
    prepared = _prepare_tablet_outpaint_source(image_path)
    uploaded_name = _upload_comfyui_image(prepared["image_bytes"], prepared["filename"])
    workflow = _build_sdxl_outpaint_workflow(
        prompt or build_generic_outpaint_prompt(),
        uploaded_image=uploaded_name,
        left=prepared["left"],
        right=prepared["right"],
        top=prepared["top"],
        bottom=prepared["bottom"],
        filename_prefix="lion_story_tablet_outpaint",
    )
    prompt_id = _queue_comfyui_prompt(workflow)
    output = _wait_for_comfyui_image(prompt_id)
    image_bytes = _download_comfyui_image(output)
    _write_image_bytes(tablet_path, image_bytes)
    return tablet_path


def build_outpaint_image_prompt(page: StoryPage) -> str:
    return f"""{page.image_prompt}

{IMAGE_STYLE_GUIDE}

Outpaint requirement:
- Preserve the existing center image exactly: same characters, same action, same facial expressions, same lighting.
- Extend only the missing left and right background into a natural iPad landscape 4:3 scene.
- Continue the forest, sky, room, ground, colors, line weight, and shading from the original image.
- Do not redraw or duplicate the central characters.
- No UI chrome, buttons, captions, watermarks, or text inside the image."""


def build_generic_outpaint_prompt() -> str:
    return f"""Existing children's storybook illustration.

{IMAGE_STYLE_GUIDE}

Outpaint requirement:
- Preserve the existing center image exactly: same characters, same action, same facial expressions, same lighting.
- Extend only the missing left and right background into a natural iPad landscape 4:3 scene.
- Continue the original background, colors, line weight, and shading.
- Do not redraw, move, crop, or duplicate the central characters.
- No UI chrome, buttons, captions, watermarks, or text inside the image."""


def _write_image_bytes(path: str, image_bytes: bytes) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    ext = os.path.splitext(path)[1].lower()
    if ext in {".webp", ".jpg", ".jpeg"}:
        image_module = _image_module()
        with image_module.open(BytesIO(image_bytes)) as image:
            image = image.convert("RGB")
            if ext == ".webp":
                image.save(path, format="WEBP", quality=95, method=6)
            else:
                image.save(path, format="JPEG", quality=95)
        return

    with open(path, "wb") as f:
        f.write(image_bytes)


def _prepare_tablet_outpaint_source(image_path: str) -> dict[str, object]:
    image_module = _image_module()
    with image_module.open(image_path) as image:
        source = image.convert("RGB")
        source_width, source_height = source.size

        scale = min(COMFYUI_TABLET_WIDTH / source_width, COMFYUI_TABLET_HEIGHT / source_height)
        resized_width = max(1, round(source_width * scale))
        resized_height = max(1, round(source_height * scale))
        resized = source.resize((resized_width, resized_height), image_module.Resampling.LANCZOS)

        buffer = BytesIO()
        resized.save(buffer, format="PNG")

    left = max(0, (COMFYUI_TABLET_WIDTH - resized_width) // 2)
    right = max(0, COMFYUI_TABLET_WIDTH - resized_width - left)
    top = max(0, (COMFYUI_TABLET_HEIGHT - resized_height) // 2)
    bottom = max(0, COMFYUI_TABLET_HEIGHT - resized_height - top)
    filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_tablet_source.png"

    return {
        "image_bytes": buffer.getvalue(),
        "filename": filename,
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
    }


def _image_module():
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Pillow is required for tablet outpainting. Run `pip install -r requirements.txt` inside the project venv."
        ) from exc
    return Image


def _queue_comfyui_prompt(workflow: dict) -> str:
    resp = requests.post(
        f"{COMFYUI_BASE_URL.rstrip('/')}/prompt",
        json={"prompt": workflow},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(
            "ComfyUI rejected the workflow. "
            f"status={resp.status_code} body={resp.text[:4000]}"
        )
    return resp.json()["prompt_id"]


def _upload_comfyui_image(image_bytes: bytes, filename: str) -> str:
    resp = requests.post(
        f"{COMFYUI_BASE_URL.rstrip('/')}/upload/image",
        files={"image": (filename, image_bytes, "image/png")},
        data={"overwrite": "true"},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("name") or filename


def _wait_for_comfyui_image(prompt_id: str, timeout_seconds: int = 300) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        resp = requests.get(
            f"{COMFYUI_BASE_URL.rstrip('/')}/history/{prompt_id}",
            timeout=30,
        )
        resp.raise_for_status()
        history = resp.json()
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            for node_output in outputs.values():
                images = node_output.get("images", [])
                if images:
                    return images[0]
        time.sleep(1)

    raise TimeoutError(f"ComfyUI image generation timed out: {prompt_id}")


def _download_comfyui_image(image_info: dict) -> bytes:
    resp = requests.get(
        f"{COMFYUI_BASE_URL.rstrip('/')}/view",
        params={
            "filename": image_info["filename"],
            "subfolder": image_info.get("subfolder", ""),
            "type": image_info.get("type", "output"),
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def _build_sdxl_workflow(
    prompt: str,
    *,
    width: int,
    height: int,
    filename_prefix: str,
) -> dict:
    negative_prompt = (
        "photorealistic, realistic, 3d render, watercolor, sketch, messy lines, "
        "different character design, inconsistent style, text, caption, watermark, "
        "logo, UI, button, blurry, low quality, extra limbs, scary, violent"
    )
    seed = random.randint(1, 2**31 - 1)
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": COMFYUI_CHECKPOINT},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative_prompt, "clip": ["1", 1]},
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": COMFYUI_STEPS,
                "cfg": COMFYUI_CFG,
                "sampler_name": COMFYUI_SAMPLER,
                "scheduler": COMFYUI_SCHEDULER,
                "denoise": 1,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": filename_prefix, "images": ["6", 0]},
        },
    }


def _build_sdxl_outpaint_workflow(
    prompt: str,
    *,
    uploaded_image: str,
    left: int,
    right: int,
    top: int,
    bottom: int,
    filename_prefix: str,
) -> dict:
    negative_prompt = (
        "photorealistic, realistic, 3d render, watercolor, sketch, messy lines, "
        "different character design, duplicated characters, changed face, changed pose, "
        "text, caption, watermark, logo, UI, button, blurry, low quality, extra limbs, "
        "scary, violent"
    )
    seed = random.randint(1, 2**31 - 1)
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": COMFYUI_CHECKPOINT},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": uploaded_image},
        },
        "3": {
            "class_type": "ImagePadForOutpaint",
            "inputs": {
                "image": ["2", 0],
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
                "feathering": COMFYUI_OUTPAINT_FEATHERING,
            },
        },
        "4": {
            "class_type": "VAEEncodeForInpaint",
            "inputs": {
                "pixels": ["3", 0],
                "vae": ["1", 2],
                "mask": ["3", 1],
                "grow_mask_by": 8,
            },
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative_prompt, "clip": ["1", 1]},
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": COMFYUI_STEPS,
                "cfg": COMFYUI_CFG,
                "sampler_name": COMFYUI_SAMPLER,
                "scheduler": COMFYUI_SCHEDULER,
                "denoise": COMFYUI_TABLET_DENOISE,
                "model": ["1", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["4", 0],
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["7", 0], "vae": ["1", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": filename_prefix, "images": ["8", 0]},
        },
    }
