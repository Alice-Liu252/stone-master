"""Vision feature extraction for the Stone Master AR scan pipeline.

Phase 0 prototype standing in for the "端側/雲端視覺辨識服務" described in
docs/TECHNICAL_ARCHITECTURE.md section 3. It derives a deterministic feature
vector + perceptual hash from plain color/texture/shape statistics rather
than a trained model. That's enough to prove the pipeline shape (same rock
-> same fingerprint, different rocks -> different fingerprint) but it is
NOT a real geology classifier — rock_type/mineral classification still
needs a model trained on a labeled photo dataset before this can tell a
sedimentary rock from an igneous one for real.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image

THUMBNAIL_SIZE = (128, 128)
COLOR_BINS_PER_CHANNEL = 4  # 4x4x4 = 64-bin joint color histogram
GRADIENT_HIST_BINS = 8
DHASH_SIZE = (9, 8)  # -> 64-bit hash


@dataclass(frozen=True)
class Features:
    embedding: np.ndarray  # L2-normalized float32 vector, fixed length
    phash: int  # 64-bit perceptual hash, used for fast pre-filtering
    mean_color: tuple  # (r, g, b) 0-255, for debug/display
    fill_ratio: float  # foreground / bounding-box area, 0-1
    aspect_ratio: float  # bounding-box width / height
    roughness: float  # mean gradient magnitude, 0-1, raw (pre L2-normalize)

    def embedding_list(self) -> list:
        return self.embedding.tolist()


def _load_rgb(image: Union[str, Path, Image.Image]) -> Image.Image:
    img = image if isinstance(image, Image.Image) else Image.open(image)
    return img.convert("RGB")


def _color_histogram(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """64-bin joint RGB histogram over the foreground (rock) pixels only,
    normalized to sum to 1. Restricting to `mask` matters: the background
    usually covers more of the frame than the rock (docs/GDD.md 4.2's
    guided capture still leaves a visible mat/surface around it), so an
    unmasked histogram mostly fingerprints the scanning surface instead of
    the rock — two different rocks scanned on the same table would then
    look like the same fingerprint."""
    bins = COLOR_BINS_PER_CHANNEL
    pixels = rgb[mask] if mask.any() else rgb.reshape(-1, 3)
    idx = (pixels.astype(np.int32) * bins // 256).clip(0, bins - 1)
    flat_idx = idx[:, 0] * bins * bins + idx[:, 1] * bins + idx[:, 2]
    hist = np.bincount(flat_idx, minlength=bins**3).astype(np.float64)
    total = hist.sum()
    return hist / total if total else hist


def _texture_stats(gray: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Gradient-magnitude mean/std + coarse histogram over the foreground
    pixels, as a roughness proxy for the real crystal facets / grain /
    porosity a trained model would read directly from the image. Gradients
    are computed on the full image first (so edge pixels still have real
    neighbors) and only then restricted to `mask`, for the same reason as
    _color_histogram: an unmasked stat mostly measures the background."""
    gray_f = gray.astype(np.float64)
    gx = np.diff(gray_f, axis=1, prepend=gray_f[:, :1])
    gy = np.diff(gray_f, axis=0, prepend=gray_f[:1, :])
    mag = np.sqrt(gx**2 + gy**2)
    mag_fg = mag[mask] if mask.any() else mag.ravel()
    mean, std = float(mag_fg.mean()), float(mag_fg.std())
    hist, _ = np.histogram(mag_fg, bins=GRADIENT_HIST_BINS, range=(0, 255))
    hist = hist.astype(np.float64)
    total = hist.sum()
    hist = hist / total if total else hist
    return np.concatenate([[mean / 255.0, std / 255.0], hist])


def _otsu_threshold(gray: np.ndarray) -> int:
    """Classic Otsu binarization threshold, implemented from scratch to
    avoid pulling in scikit-image/opencv for one function."""
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))
    hist = hist.astype(np.float64)
    total = hist.sum()
    if total == 0:
        return 128
    sum_all = float(np.dot(np.arange(256), hist))
    sum_b = weight_b = 0.0
    best_thresh, best_var = 0, -1.0
    for t in range(256):
        weight_b += hist[t]
        if weight_b == 0:
            continue
        weight_f = total - weight_b
        if weight_f == 0:
            break
        sum_b += t * hist[t]
        mean_b = sum_b / weight_b
        mean_f = (sum_all - sum_b) / weight_f
        between_var = weight_b * weight_f * (mean_b - mean_f) ** 2
        if between_var > best_var:
            best_var, best_thresh = between_var, t
    return best_thresh


def _foreground_mask(gray: np.ndarray) -> np.ndarray:
    """Foreground/background split assuming the rock is scanned against a
    roughly uniform background, per the guided AR capture flow in
    docs/GDD.md section 4.2. Placeholder heuristic, not a segmentation
    model — will misfire on cluttered backgrounds."""
    thresh = _otsu_threshold(gray)
    mask = gray < thresh
    if mask.sum() > mask.size / 2:
        mask = ~mask  # foreground = minority class
    return mask


def _shape_stats(mask: np.ndarray) -> tuple:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return 1.0, 1.0
    box_w = max(int(xs.max() - xs.min() + 1), 1)
    box_h = max(int(ys.max() - ys.min() + 1), 1)
    fill_ratio = len(xs) / (box_w * box_h)
    aspect_ratio = box_w / box_h
    return float(fill_ratio), float(aspect_ratio)


def _dhash(gray_img: Image.Image) -> int:
    small = gray_img.resize(DHASH_SIZE, Image.Resampling.LANCZOS)
    pixels = np.asarray(small, dtype=np.int32)
    bits = (pixels[:, 1:] > pixels[:, :-1]).ravel()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def extract_features(image: Union[str, Path, Image.Image]) -> Features:
    """Deterministic feature extraction: the same input image always
    produces the same output. Real photos of the same rock taken moments
    apart will differ slightly (lighting, angle, hand shake), which is why
    matching uses a similarity threshold rather than exact equality — see
    fingerprint_store.match_or_create()."""
    rgb_img = _load_rgb(image).resize(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    gray_img = rgb_img.convert("L")

    rgb = np.asarray(rgb_img)
    gray = np.asarray(gray_img)
    mask = _foreground_mask(gray)

    color_hist = _color_histogram(rgb, mask)
    texture = _texture_stats(gray, mask)
    roughness = float(texture[0])  # mean gradient magnitude, before normalize
    fill_ratio, aspect_ratio = _shape_stats(mask)

    embedding = np.concatenate(
        [color_hist, texture, [fill_ratio, aspect_ratio]]
    ).astype(np.float32)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    mean_color = tuple(int(c) for c in rgb.reshape(-1, 3).mean(axis=0))
    phash = _dhash(gray_img)

    return Features(
        embedding=embedding,
        phash=phash,
        mean_color=mean_color,
        fill_ratio=fill_ratio,
        aspect_ratio=aspect_ratio,
        roughness=roughness,
    )


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
