"""System operations skills implementation."""

import os
import shutil
import psutil
from pathlib import Path
from typing import Optional


SKILL_DEFINITION = {
    "name": "system_ops",
    "description": "System operations toolkit",
    "category": "system",
    "parameters": {}
}


def file_read(path: str, encoding: str = "utf-8") -> dict:
    """Read file contents."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}
        if not file_path.is_file():
            return {"success": False, "error": f"Not a file: {path}"}

        content = file_path.read_text(encoding=encoding)
        return {
            "success": True,
            "content": content,
            "size": file_path.stat().st_size,
            "path": str(file_path.absolute()),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def file_write(path: str, content: str, encoding: str = "utf-8", mode: str = "overwrite") -> dict:
    """Write content to file."""
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if mode == "append":
            with open(file_path, "a", encoding=encoding) as f:
                f.write(content)
        else:
            file_path.write_text(content, encoding=encoding)

        return {
            "success": True,
            "path": str(file_path.absolute()),
            "size": len(content),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def file_list(path: str, pattern: str = "*", recursive: bool = False) -> dict:
    """List files in directory."""
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return {"success": False, "error": f"Directory not found: {path}"}
        if not dir_path.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}

        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        file_list = []
        for f in files:
            stat = f.stat()
            file_list.append({
                "name": f.name,
                "path": str(f.absolute()),
                "type": "directory" if f.is_dir() else "file",
                "size": stat.st_size if f.is_file() else None,
                "modified": stat.st_mtime,
            })

        return {
            "success": True,
            "files": file_list,
            "count": len(file_list),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def file_delete(path: str) -> dict:
    """Delete a file."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            shutil.rmtree(file_path)

        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def file_copy(source: str, destination: str) -> dict:
    """Copy a file."""
    try:
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            return {"success": False, "error": f"Source not found: {source}"}

        dst_path.parent.mkdir(parents=True, exist_ok=True)

        if src_path.is_file():
            shutil.copy2(src_path, dst_path)
        elif src_path.is_dir():
            shutil.copytree(src_path, dst_path)

        return {
            "success": True,
            "source": str(src_path.absolute()),
            "destination": str(dst_path.absolute()),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def process_list(name_filter: Optional[str] = None) -> dict:
    """List running processes."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if name_filter and name_filter.lower() not in pinfo['name'].lower():
                    continue
                processes.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "username": pinfo['username'],
                    "cpu": pinfo['cpu_percent'],
                    "memory": pinfo['memory_percent'],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return {
            "success": True,
            "processes": processes,
            "count": len(processes),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def process_kill(pid: int, force: bool = False) -> dict:
    """Kill a process by PID."""
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()

        if force:
            proc.kill()
        else:
            proc.terminate()

        return {
            "success": True,
            "pid": pid,
            "name": proc_name,
        }
    except psutil.NoSuchProcess:
        return {"success": False, "error": f"Process not found: {pid}"}
    except psutil.AccessDenied:
        return {"success": False, "error": f"Access denied: {pid}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def system_info() -> dict:
    """Get system information."""
    try:
        import platform

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "success": True,
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def disk_usage(path: str = "/") -> dict:
    """Get disk usage information."""
    try:
        usage = psutil.disk_usage(path)

        return {
            "success": True,
            "path": path,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Export functions
execute = system_info  # Default executor
