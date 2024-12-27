"""Recognize image file formats based on their first few bytes."""

from os import PathLike

from contextlib import ExitStack
from collections.abc import Callable

from typing import Any, BinaryIO, Protocol, overload

__all__ = ["what"]


class ReadableBinary(Protocol):
    def tell(self) -> int: ...
    def read(self, size: int, /) -> bytes: ...
    def seek(self, offset: int, /) -> Any: ...


type FLike = PathLike[str] | str | ReadableBinary


tests: list[Callable[[bytes, BinaryIO | None], str | None]] = []


def _append[T: Callable[[bytes, BinaryIO | None], str | None]](f: T) -> T:
    tests.append(f)
    return f


@overload
def what(file: FLike) -> str | None: ...


@overload
def what(file: Any, h: bytes) -> str | None: ...


def what(file: FLike, h: bytes | None = None) -> str | None:
    """Return the type of image contained in a file or byte stream."""
    f = None
    with ExitStack() as stack:
        if h is None:
            if isinstance(file, (str, PathLike)):
                f = stack.enter_context(open(file, "rb"))
                h = f.read(32)
            else:
                location = file.tell()
                h = file.read(32)
                file.seek(location)
        return next(filter(None, (tf(h, f) for tf in tests)), None)
    return None


@_append
def test_jpeg(h: bytes, f: BinaryIO | None) -> str | None:
    """Test for JPEG data with JFIF or Exif markers; and raw JPEG."""
    if h[6:10] in (b"JFIF", b"Exif"):
        return "jpeg"
    elif h[:4] == b"\xff\xd8\xff\xdb":
        return "jpeg"


@_append
def test_png(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a PNG."""
    if h.startswith(b"\211PNG\r\n\032\n"):
        return "png"


@_append
def test_gif(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a GIF ('87 or '89 variants)."""
    if h[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"


@_append
def test_tiff(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a TIFF (can be in Motorola or Intel byte order)."""
    if h[:2] in (b"MM", b"II"):
        return "tiff"


@_append
def test_rgb(h: bytes, f: BinaryIO | None) -> str | None:
    """test for the SGI image library."""
    if h.startswith(b"\001\332"):
        return "rgb"


@_append
def test_pbm(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a PBM (portable bitmap)."""
    if len(h) >= 3 and h[0] == ord(b"P") and h[1] in b"14" and h[2] in b" \t\n\r":
        return "pbm"


@_append
def test_pgm(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a PGM (portable graymap)."""
    if len(h) >= 3 and h[0] == ord(b"P") and h[1] in b"25" and h[2] in b" \t\n\r":
        return "pgm"


@_append
def test_ppm(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a PPM (portable pixmap)."""
    if len(h) >= 3 and h[0] == ord(b"P") and h[1] in b"36" and h[2] in b" \t\n\r":
        return "ppm"


@_append
def test_rast(h: bytes, f: BinaryIO | None) -> str | None:
    """test for the Sun raster file."""
    if h.startswith(b"\x59\xa6\x6a\x95"):
        return "rast"


@_append
def test_xbm(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a X bitmap (X10 or X11)."""
    if h.startswith(b"#define "):
        return "xbm"


@_append
def test_bmp(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a BMP file."""
    if h.startswith(b"BM"):
        return "bmp"


@_append
def test_webp(h: bytes, f: BinaryIO | None) -> str | None:
    """Verify if the image is a WebP."""
    if h.startswith(b"RIFF") and h[8:12] == b"WEBP":
        return "webp"


@_append
def test_exr(h: bytes, f: BinaryIO | None) -> str | None:
    """verify is the image ia a OpenEXR fileOpenEXR."""
    if h.startswith(b"\x76\x2f\x31\x01"):
        return "exr"
