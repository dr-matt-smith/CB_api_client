import io
import zipfile


def make_zip(name: str, marker: str = "x") -> io.BytesIO:
    buf = io.BytesIO()
    # v8 reads only name + author from the manifest.
    toml = (
        "[package]\n"
        f'name = "{name}"\n'
        'author = "pytest"\n'
        'license = "MIT"\n'
    )
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("package.toml", toml)
        z.writestr("contents.txt", f"marker={marker}\n")
    buf.seek(0)
    return buf


def make_page_zip(path: str, marker: str = "x") -> io.BytesIO:
    """A standalone page bundle for the v8 /api/pages endpoint.

    The ZIP root is the served site: everything except pages.toml is published
    verbatim to /pages/<org>/<path>/. pages.toml carries the [publish].path.
    """
    buf = io.BytesIO()
    toml = (
        "[publish]\n"
        f'path = "{path}"\n'
    )
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pages.toml", toml)
        z.writestr("index.html", f"<h1>{marker}</h1>\n")
    buf.seek(0)
    return buf
