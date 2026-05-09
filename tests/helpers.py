import io
import zipfile


def make_zip(name: str, marker: str = "x") -> io.BytesIO:
    buf = io.BytesIO()
    toml = (
        "[package]\n"
        f'name = "{name}"\n'
        'type = "mod"\n'
        'author = "pytest"\n'
        'license = "MIT"\n'
    )
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("package.toml", toml)
        z.writestr("contents.txt", f"marker={marker}\n")
    buf.seek(0)
    return buf
