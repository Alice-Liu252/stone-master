import numpy as np

from make_test_rocks import make_rock_image
from stone_master import vision


def test_extract_features_is_deterministic(tmp_path):
    img_path = tmp_path / "rock.png"
    make_rock_image(seed=1).save(img_path)

    a = vision.extract_features(img_path)
    b = vision.extract_features(img_path)

    assert np.array_equal(a.embedding, b.embedding)
    assert a.phash == b.phash
    assert a.fill_ratio == b.fill_ratio
    assert a.aspect_ratio == b.aspect_ratio


def test_different_rocks_produce_different_fingerprints(tmp_path):
    path_a = tmp_path / "a.png"
    path_b = tmp_path / "b.png"
    make_rock_image(seed=1).save(path_a)
    make_rock_image(seed=2).save(path_b)

    a = vision.extract_features(path_a)
    b = vision.extract_features(path_b)

    assert a.phash != b.phash
    assert vision.cosine_similarity(a.embedding, b.embedding) < 0.99


def test_cosine_similarity_of_identical_vector_is_one():
    v = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    assert abs(vision.cosine_similarity(v, v) - 1.0) < 1e-6


def test_hamming_distance_zero_for_equal_hash():
    assert vision.hamming_distance(0b1010, 0b1010) == 0
    assert vision.hamming_distance(0b1010, 0b0010) == 1
