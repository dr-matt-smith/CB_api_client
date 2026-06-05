import io
import zipfile


def make_zip(name: str, marker: str = "x", with_public: bool = False) -> io.BytesIO:
    buf = io.BytesIO()
    # v7 ignores `type`; only name + author are read from the manifest.
    toml = (
        "[package]\n"
        f'name = "{name}"\n'
        'author = "pytest"\n'
        'license = "MIT"\n'
    )
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("package.toml", toml)
        z.writestr("contents.txt", f"marker={marker}\n")
        if with_public:
            # A public/ folder makes the version web-publishable via /api/publish.
            z.writestr("public/index.html", f"<h1>{name}</h1>\n")
    buf.seek(0)
    return buf
