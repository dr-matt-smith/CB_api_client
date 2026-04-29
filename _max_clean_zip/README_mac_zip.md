
to ZIP on mac without the "__MACOSX" folder and contents

    zip -r son-of-fungus.zip son-of-fungus -x ".*" "*/.*"

BUT this still creates a "son-of-fungus" folder inside "son-of-fungus.zip".

To zip the *contents* of the folder (no wrapping folder inside the archive), cd into it and zip `.`:

    (cd son-of-fungus && zip -r ../son-of-fungus.zip . -x ".*" "*/.*")

- The parentheses run it in a subshell so your working directory doesn't change.
- `.` means "everything in the current dir" — entries are stored as `file.txt`, `sub/file.txt`, with no `son-of-fungus/` prefix.
- `../son-of-fungus.zip` writes the archive one level up, outside the folder being zipped.
- `-x ".*" "*/.*"` skips dotfiles like `.DS_Store`, keeping `__MACOSX` out.