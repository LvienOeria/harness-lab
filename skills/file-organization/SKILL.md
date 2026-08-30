---
name: file-organization
description: Use when a task asks to organize, move, or rename files in a directory tree.
---

# File organization

- Inspect the full tree first with `find . -type f` before moving anything.
- Create destination directories only if they do not already exist.
- Move files; do not copy them unless the task explicitly says copy.
- Keep file contents byte-for-byte identical unless the task says otherwise.
- Leave no old names behind when the task asks to rename.
- Verify with `find . -type f | sort` that the tree matches the requested structure.
