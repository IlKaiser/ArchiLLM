import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any

def _safe_join(root: Path, rel: str) -> Path:
    p = (root / rel).resolve()
    root = root.resolve()
    if not str(p).startswith(str(root)):
        raise ValueError(f"Unsafe path traversal detected: {rel}")
    return p

def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def apply_project_update_from_json(plan_str: str, project_root: Path) -> Dict[str, Any]:
    """
    Parse and apply a JSON update plan to project_root.
    Returns a summary dict with applied actions and any errors.
    """
    summary = {"applied": [], "errors": []}

    try:
        plan = json.loads(plan_str)
    except Exception as e:
        raise ValueError(f"Invalid JSON plan: {e}")

    if not isinstance(plan, dict) or "actions" not in plan or not isinstance(plan["actions"], list):
        raise ValueError("Plan must be an object with an 'actions' array")

    for i, action in enumerate(plan["actions"]):
        try:
            op = action.get("op")
            if op not in {"mkdir", "write", "append", "move", "delete"}:
                raise ValueError(f"Unsupported op: {op}")

            if op == "mkdir":
                rel = action["path"]
                dst = _safe_join(project_root, rel)
                dst.mkdir(parents=True, exist_ok=True)
                summary["applied"].append({"index": i, "op": op, "path": rel})

            elif op in {"write", "append"}:
                rel = action["path"]
                encoding = action.get("encoding", "utf-8")
                if_exists = action.get("if_exists", "overwrite")
                content = action.get("content", "")

                dst = _safe_join(project_root, rel)
                _ensure_parent(dst)

                if dst.exists():
                    if op == "write":
                        if if_exists == "skip":
                            summary["applied"].append({"index": i, "op": op, "path": rel, "skipped": True})
                            continue
                        elif if_exists == "error":
                            raise FileExistsError(f"File exists: {rel}")
                        # overwrite or append handled below
                    # for append op, we always append

                # decode or use as text
                if encoding == "base64":
                    data = base64.b64decode(content.encode("utf-8"))
                    mode = "ab" if op == "append" else "wb"
                    with open(dst, mode) as f:
                        f.write(data)
                elif encoding == "utf-8":
                    mode = "a" if (op == "append" or (op == "write" and if_exists == "append")) else "w"
                    with open(dst, mode, encoding="utf-8") as f:
                        f.write(content)
                else:
                    raise ValueError(f"Unsupported encoding: {encoding}")

                summary["applied"].append({"index": i, "op": op, "path": rel})

            elif op == "move":
                rel_from = action["from"]
                rel_to   = action["to"]
                if_exists = action.get("if_exists", "overwrite")

                src = _safe_join(project_root, rel_from)
                dst = _safe_join(project_root, rel_to)
                _ensure_parent(dst)

                if not src.exists():
                    raise FileNotFoundError(f"Source not found: {rel_from}")

                if dst.exists():
                    if if_exists == "skip":
                        summary["applied"].append({"index": i, "op": op, "from": rel_from, "to": rel_to, "skipped": True})
                        continue
                    elif if_exists == "error":
                        raise FileExistsError(f"Target exists: {rel_to}")
                    elif if_exists == "overwrite":
                        if dst.is_dir():
                            shutil.rmtree(dst)
                        else:
                            dst.unlink()

                shutil.move(str(src), str(dst))
                summary["applied"].append({"index": i, "op": op, "from": rel_from, "to": rel_to})

            elif op == "delete":
                rel = action["path"]
                recursive = bool(action.get("recursive", False))
                target = _safe_join(project_root, rel)

                if not target.exists():
                    summary["applied"].append({"index": i, "op": op, "path": rel, "missing": True})
                    continue

                if target.is_dir():
                    if recursive:
                        shutil.rmtree(target)
                    else:
                        # delete only if empty
                        try:
                            target.rmdir()
                        except OSError:
                            raise OSError(f"Directory not empty: {rel}")
                else:
                    target.unlink()

                summary["applied"].append({"index": i, "op": op, "path": rel})

        except Exception as e:
            summary["errors"].append({"index": i, "action": action, "error": str(e)})

    return summary
