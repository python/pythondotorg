from pathlib import Path


def get_test_rss_path():
    return str(Path(__file__).parent / "psf_feed_example.xml")
