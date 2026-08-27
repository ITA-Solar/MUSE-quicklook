# MUSE PyFiles Quick Reference

## Setup (One-time)

```bash
cd /Users/mawiesma/muse/MUSE-quicklook
./setup_venv.sh
```

## Daily Usage

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run application
python muse_pyfiles.py

# 3. When done
deactivate
```

## Common Commands

| Task | Command |
|------|---------|
| Activate venv | `source venv/bin/activate` |
| Run application | `python muse_pyfiles.py` or `muse-pyfiles` |
| Run tests | `python test_muse_pyfiles.py` |
| Deactivate venv | `deactivate` |
| Reinstall deps | `pip install -r requirements.txt` |
| Update project | `pip install -e .` |

## Project Structure

```
muse_pyfiles.py              ? Main application
muse_recent_timewindows.py   ? Time management
test_muse_pyfiles.py         ? Tests
pyproject.toml               ? Project config
setup_venv.sh                ? Setup script
venv/                        ? Virtual environment
~/.muse_pyfiles/             ? User settings
```

## Configuration Files

- **User settings**: `~/.muse_pyfiles/muse_pyfiles_searches.pkl`
- **Project config**: `pyproject.toml`
- **Dependencies**: `requirements.txt`

## Help

- Full docs: [README_MUSE_PyFiles.md](README_MUSE_PyFiles.md)
- Installation: [INSTALL.md](INSTALL.md)
- Issues: Report to MUSE team
