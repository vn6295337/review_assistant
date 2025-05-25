import argparse
import shutil
import logging
from pathlib import Path
from datetime import datetime
import re
import hashlib
from collections import defaultdict

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Naming and skip patterns
PY_PATTERN = r'^[a-z][a-z0-9_]*\.py$'
SH_PATTERN = r'^[a-z][a-z0-9_]*\.sh$'
DIR_PATTERN = r'^[a-z][a-z0-9_]*$'
BACKUP_PREFIX = 'cleanup_backup_'  # prefix for backup dirs
SKIP_DIR_PATTERNS = ['/.git/', '/venv/', '/env/']

# Unwanted patterns
UNWANTED_FILE_EXTS = {'.log', '.cache', '.tmp', '.temp', '~'}
UNWANTED_DIR_NAMES = {'__pycache__', 'node_modules'}

# Reorganization categories with proper paths
FILE_CATEGORIES = {
    #'core': {'file_chunker.py', 'file_summarizer.py', 'chunk_searcher.py', 'mcp_helper.py'}, files moved to review_assistant/python
    'scripts': {'.sh'},
    'python': {'.py'},
    'docs': {'.md', '.txt'},
}

# Define the expected location of core files
CORE_FILE_PATHS = {
    'file_chunker.py': 'core/file_chunker.py',
    'file_summarizer.py': 'core/file_summarizer.py',
    'chunk_searcher.py': 'core/chunk_searcher.py',
    'mcp_helper.py': 'core/mcp_helper.py',
    'rag_assistant.sh': 'scripts/rag_assistant.sh',
    'rag_helper.sh': 'scripts/rag_helper.sh'
}

# Duplicate detection settings
HASH_CHUNK_SIZE = 4096


def should_skip(p: Path) -> bool:
    """Determine if a path should be skipped during cleanup."""
    # Skip backups, hidden, git, venv
    s = str(p)
    if p.parts and BACKUP_PREFIX in p.parts[0]:
        return True
    if any(part.startswith('.') for part in p.parts):
        return True
    return any(pat in s for pat in SKIP_DIR_PATTERNS)


def is_self(p: Path, script_path: Path) -> bool:
    """Check if the path is the script itself to avoid moving itself during execution."""
    try:
        return p.resolve() == script_path.resolve()
    except (OSError, RuntimeError):
        # Handle potential permission issues or circular symlinks
        return False


def has_standard_name(p: Path, pattern: str) -> bool:
    """Check if a path has a standardized name according to the pattern."""
    return bool(re.match(pattern, p.name))


def suggest_standard_name(p: Path) -> str:
    """Generate a standardized name for a file or directory."""
    cleaned = re.sub(r'[\s\-]+', '_', p.stem.lower())
    cleaned = re.sub(r'[^a-z0-9_]', '', cleaned)
    # Ensure the name starts with a letter
    if cleaned and not cleaned[0].isalpha():
        cleaned = 'x_' + cleaned
    # Handle empty names
    if not cleaned:
        cleaned = 'unnamed'
    return f"{cleaned}{p.suffix if p.is_file() else ''}"


def backup_path_for(p: Path, root: Path, backup_base: Path) -> Path:
    """Generate a backup path preserving the relative structure."""
    target = backup_base / p.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def categorize_and_move(p: Path, root: Path, dry_run: bool, script_path: Path) -> bool:
    """Categorize and move a file to its appropriate directory."""
    # Skip if it's the script itself
    if is_self(p, script_path):
        logger.info(f"Skipping self: {p}")
        return False
        
    for folder, types in FILE_CATEGORIES.items():
        if p.name in types or p.suffix in types:
            dest = root / folder
            dest.mkdir(exist_ok=True)
            target = dest / p.name
            
            # Handle filename collisions
            if target.exists() and p != target:
                # Only move if the file is different
                if calculate_file_hash(p) != calculate_file_hash(target):
                    counter = 1
                    while target.exists():
                        new_name = f"{p.stem}_{counter}{p.suffix}"
                        target = dest / new_name
                        counter += 1
            
            if target != p:  # Only move if paths are different
                if not dry_run:
                    # Ensure parent directory exists
                    target.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        p.rename(target)
                        logger.info(f"Moved {p} -> {target}")
                    except OSError as e:
                        logger.error(f"Failed to move {p}: {e}")
                else:
                    logger.info(f"Would move {p} -> {target}")
                return True
    return False


def write_tree_structure(root: Path, tree_file: Path):
    """Write a tree structure of the directory to a file."""
    with tree_file.open('w') as f:
        f.write(f"Tree structure for {root} at {datetime.now()}\n")
        f.write("="*50 + "\n\n")
        for p in sorted(root.rglob('*')):
            if should_skip(p):
                continue
            rel = p.relative_to(root)
            indent = '    ' * (len(rel.parts) - 1)
            f.write(f"{indent}{p.name}{' (dir)' if p.is_dir() else ''}\n")


def calculate_file_hash(p: Path) -> str:
    """Calculate a hash for a file to identify duplicates."""
    if not p.is_file():
        return ""
    
    try:
        hasher = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError) as e:
        logger.error(f"Cannot hash {p}: {e}")
        return f"ERROR_{str(e)}"


def find_duplicate_groups(root: Path) -> dict:
    """Find groups of duplicate files based on content hash."""
    groups = defaultdict(list)
    for p in root.rglob('*'):
        if p.is_file() and not should_skip(p):
            try:
                h = calculate_file_hash(p)
                if h:  # Only add if we got a valid hash
                    groups[h].append(p)
            except Exception as e:
                logger.error(f"Error processing {p}: {e}")
    return {h: fs for h, fs in groups.items() if len(fs) > 1 and h}


def handle_duplicates(root: Path, backup_base: Path, dry_run: bool, backup: bool, script_path: Path):
    """Handle duplicate files by either backing up or deleting them."""
    for h, files in find_duplicate_groups(root).items():
        # Sort by modification time (newest first)
        try:
            files_sorted = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
        except OSError:
            logger.error(f"Cannot stat some files in group {h[:8]}, using alphabetical order")
            files_sorted = sorted(files, key=lambda x: str(x))
        
        # Keep the first (newest) file
        for dup in files_sorted[1:]:
            # Skip if it's the script itself
            if is_self(dup, script_path):
                logger.info(f"Skipping duplicate that is self: {dup}")
                continue
                
            if backup:
                target = backup_path_for(dup, root, backup_base)
                if not dry_run:
                    try:
                        shutil.move(str(dup), str(target))
                        logger.info(f"Backed up duplicate: {dup} -> {target}")
                    except (OSError, shutil.Error) as e:
                        logger.error(f"Failed to backup {dup}: {e}")
                else:
                    logger.info(f"Would backup duplicate: {dup} -> {target}")
            else:
                if not dry_run:
                    try:
                        dup.unlink()
                        logger.info(f"Deleted duplicate: {dup}")
                    except OSError as e:
                        logger.error(f"Failed to delete {dup}: {e}")
                else:
                    logger.info(f"Would delete duplicate: {dup}")


def find_empty_directories(root: Path) -> list:
    """Find empty directories that can be removed."""
    try:
        dirs = [d for d in root.rglob('*') 
                if d.is_dir() 
                and not any(d.iterdir()) 
                and not should_skip(d)]
        return sorted(dirs, key=lambda d: len(d.parts), reverse=True)
    except (PermissionError, OSError) as e:
        logger.error(f"Error finding empty directories: {e}")
        return []


def check_core_files(root: Path) -> list:
    """Check if core files exist in their expected locations."""
    missing = []
    for filename, path in CORE_FILE_PATHS.items():
        full_path = root / path
        if not full_path.exists():
            # Check if it exists elsewhere
            alternatives = list(root.rglob(filename))
            if alternatives:
                logger.info(f"Core file {filename} found at {alternatives[0]} instead of {full_path}")
            else:
                missing.append(filename)
    return missing


def main(root: Path, backup_dir: Path, dry_run: bool, analyze: bool, dup_backup: bool):
    """Main function coordinating the cleanup process."""
    # Get absolute path of this script to avoid moving it during execution
    script_path = Path(__file__).resolve()
    logger.info(f"Script running from: {script_path}")
    
    logger.info(f"Starting cleanup for {root}")
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_base = backup_dir / f"{BACKUP_PREFIX}{ts}"
    if not dry_run:
        backup_base.mkdir(parents=True, exist_ok=True)

    # Collect information
    try:
        empty_dirs = find_empty_directories(root)
        nonstd_files = [f for f in root.rglob('*') if f.is_file() and f.suffix in {'.py', '.sh'}
                        and not should_skip(f)
                        and not has_standard_name(f, PY_PATTERN if f.suffix=='.py' else SH_PATTERN)
                        and not is_self(f, script_path)]
        nonstd_dirs = [d for d in root.rglob('*') if d.is_dir()
                       and not should_skip(d)
                       and not has_standard_name(d, DIR_PATTERN)]
        unwanted_files = [f for f in root.rglob('*') if f.is_file() and f.suffix in UNWANTED_FILE_EXTS
                          and not should_skip(f)
                          and not is_self(f, script_path)]
        unwanted_dirs = [d for d in root.rglob('*') if d.is_dir() and d.name in UNWANTED_DIR_NAMES
                         and not should_skip(d)]
    except Exception as e:
        logger.error(f"Error collecting files and directories: {e}")
        return

    # Check core files
    missing_core = check_core_files(root)

    if analyze:
        logger.info(f"Empty dirs: {len(empty_dirs)}")
        for d in empty_dirs[:5]:
            logger.info(f"  - {d}")
        if len(empty_dirs) > 5:
            logger.info(f"  - ... and {len(empty_dirs) - 5} more")
            
        logger.info(f"Non-standard filenames: {len(nonstd_files)}")
        for f in nonstd_files[:5]:
            logger.info(f"  - {f} -> {suggest_standard_name(f)}")
        if len(nonstd_files) > 5:
            logger.info(f"  - ... and {len(nonstd_files) - 5} more")
            
        logger.info(f"Non-standard directory names: {len(nonstd_dirs)}")
        logger.info(f"Unwanted files: {len(unwanted_files)}")
        logger.info(f"Unwanted dirs: {len(unwanted_dirs)}")
        
        dup_groups = find_duplicate_groups(root)
        logger.info(f"Duplicate groups: {len(dup_groups)}")
        for h, files in list(dup_groups.items())[:3]:
            logger.info(f"  - Group {h[:8]}: {', '.join(str(f.name) for f in files)}")
        if len(dup_groups) > 3:
            logger.info(f"  - ... and {len(dup_groups) - 3} more groups")
            
        logger.info(f"Missing core files: {missing_core}")
        return

    # 1. Backup unwanted files and dirs
    for f in unwanted_files:
        if is_self(f, script_path):
            logger.info(f"Skipping self in unwanted files: {f}")
            continue
            
        tgt = backup_path_for(f, root, backup_base)
        if not dry_run:
            try:
                shutil.move(str(f), str(tgt))
                logger.info(f"Backed up unwanted file: {f} -> {tgt}")
            except (OSError, shutil.Error) as e:
                logger.error(f"Failed to backup {f}: {e}")
        else:
            logger.info(f"Would backup unwanted file: {f} -> {tgt}")
            
    for d in unwanted_dirs:
        tgt = backup_path_for(d, root, backup_base)
        if not dry_run:
            try:
                shutil.move(str(d), str(tgt))
                logger.info(f"Backed up unwanted dir: {d} -> {tgt}")
            except (OSError, shutil.Error) as e:
                logger.error(f"Failed to backup {d}: {e}")
        else:
            logger.info(f"Would backup unwanted dir: {d} -> {tgt}")

    # 2. Remove empty directories
    for d in empty_dirs:
        if not dry_run:
            try:
                d.rmdir()
                logger.info(f"Removed empty dir: {d}")
            except OSError as e:
                logger.error(f"Failed to remove {d}: {e}")
        else:
            logger.info(f"Would remove empty dir: {d}")

    # 3. Rename non-standard files and directories
    for f in nonstd_files:
        if is_self(f, script_path):
            logger.info(f"Skipping self in non-standard files: {f}")
            continue
            
        new_name = suggest_standard_name(f)
        new_path = f.with_name(new_name)
        
        # Handle name collisions
        counter = 1
        while new_path.exists() and new_path != f:
            new_name = f"{new_path.stem}_{counter}{new_path.suffix}"
            new_path = f.with_name(new_name)
            counter += 1
            
        if not dry_run:
            try:
                f.rename(new_path)
                logger.info(f"Renamed file {f} -> {new_name}")
            except OSError as e:
                logger.error(f"Failed to rename {f}: {e}")
        else:
            logger.info(f"Would rename file {f} -> {new_name}")
            
    # Rename directories from bottom up to avoid parent renaming issues
    for d in sorted(nonstd_dirs, key=lambda x: len(str(x).split('/')), reverse=True):
        new_name = suggest_standard_name(d)
        new_path = d.parent / new_name
        
        # Handle name collisions
        counter = 1
        while new_path.exists() and new_path != d:
            new_name = f"{new_name}_{counter}"
            new_path = d.parent / new_name
            counter += 1
            
        if not dry_run:
            try:
                d.rename(new_path)
                logger.info(f"Renamed dir {d} -> {new_name}")
            except OSError as e:
                logger.error(f"Failed to rename {d}: {e}")
        else:
            logger.info(f"Would rename dir {d} -> {new_name}")

    # 4. Create category directories
    for folder in FILE_CATEGORIES.keys():
        (root / folder).mkdir(exist_ok=True)
        
    # 5. Reorganize files (but skip the script itself)
    try:
        # First, process files in root
        for p in root.iterdir():
            if p.is_file() and not is_self(p, script_path):
                categorize_and_move(p, root, dry_run, script_path)
        
        # Then process files in subdirectories, but be more selective
        # Don't move files that are already in their correct category folder
        for folder, types in FILE_CATEGORIES.items():
            folder_path = root / folder
            for p in root.rglob('*'):
                if (p.is_file() and 
                    not is_self(p, script_path) and
                    p.parent != folder_path and  # Not already in correct category
                    (p.name in types or p.suffix in types)):
                    categorize_and_move(p, root, dry_run, script_path)
    except Exception as e:
        logger.error(f"Error during file reorganization: {e}")

    # 6. Handle duplicates
    try:
        handle_duplicates(root, backup_base, dry_run, dup_backup, script_path)
    except Exception as e:
        logger.error(f"Error handling duplicates: {e}")

    # 7. Write tree structure
    tree_file = root / f"tree_structure_{ts}.txt"
    if not dry_run:
        try:
            write_tree_structure(root, tree_file)
            logger.info(f"Tree structure written to {tree_file}")
        except Exception as e:
            logger.error(f"Failed to write tree structure: {e}")
    else:
        logger.info(f"Would write tree structure to {tree_file}")

    # Check core files again after reorganization
    post_missing_core = check_core_files(root)
    
    # Summary
    logger.info("="*50)
    logger.info("Cleanup Summary:")
    logger.info(f"Backup folder: {backup_base}")
    logger.info(f"Empty directories removed: {len(empty_dirs)}")
    logger.info(f"Non-standard files renamed: {len(nonstd_files)}")
    logger.info(f"Non-standard directories renamed: {len(nonstd_dirs)}")
    logger.info(f"Unwanted files handled: {len(unwanted_files)}")
    logger.info(f"Unwanted directories handled: {len(unwanted_dirs)}")
    logger.info(f"Missing core files (before): {missing_core}")
    logger.info(f"Missing core files (after): {post_missing_core}")
    logger.info(f"Operation mode: {'Dry run (no changes made)' if dry_run else 'Live run'}")
    logger.info("="*50)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Unified cleanup script for RAG assistant codebase')
    parser.add_argument('root', type=Path, help='Root directory to clean')
    parser.add_argument('--backup-dir', type=Path, default=Path.cwd() / 'backups', help='Backup directory')
    parser.add_argument('--dry-run', action='store_true', help='Preview actions without making changes')
    parser.add_argument('--analyze', action='store_true', help='Analyze only, no changes')
    parser.add_argument('--dup-backup', action='store_true', help='Backup duplicates instead of deleting them')
    args = parser.parse_args()
    
    # Validate paths
    if not args.root.exists():
        logger.error(f"Root directory {args.root} does not exist")
        exit(1)
        
    try:
        main(args.root, args.backup_dir, args.dry_run, args.analyze, args.dup_backup)
        logger.info("Cleanup completed successfully")
    except KeyboardInterrupt:
        logger.error('Aborted by user')
        exit(1)
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        exit(1)
