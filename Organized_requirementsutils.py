from pathlib import Path

def safe_clean_directory(
    dir_path: Path, 
    pattern: str = "*",
    confirm: bool = True,
    dry_run: bool = False
) -> bool:
    """
    Safely removes files with multiple safety checks and flexible options.
    
    Args:
        dir_path: Directory to clean
        pattern: File pattern to match (default "*")
        confirm: Whether to prompt for confirmation (default True)
        dry_run: Just show what would be done without deleting (default False)
    
    Returns:
        bool: True if files were deleted (or would be in dry-run), False if cancelled
    """
    # Validate directory exists
    if not dir_path.exists():
        print(f"⚠️ Directory does not exist: {dir_path}")
        return False
    if not dir_path.is_dir():
        print(f"⚠️ Path is not a directory: {dir_path}")
        return False

    # Get matching files
    files = sorted(dir_path.glob(pattern))
    if not files:
        print(f"ℹ️ No files matching '{pattern}' in {dir_path}")
        return True
    
    # Show preview
    print(f"Found {len(files)} files in {dir_path}:")
    for i, f in enumerate(files[:3], 1):
        print(f"{i}. {f.name} ({f.stat().st_size/1024:.1f} KB)")
    if len(files) > 3:
        print(f"...and {len(files)-3} more")
    
    # Skip confirmation if disabled
    if not confirm:
        if dry_run:
            print(f"Would delete {len(files)} files (dry-run)")
            return True
        return _perform_deletion(files)
    
    # Interactive mode
    while True:
        response = input(
            f"Delete these {len(files)} files? "
            "(y)es/(n)o/(dry-run)/(p)review all: "
        ).lower()
        
        if response in ('y', 'yes'):
            if dry_run:
                print(f"Would delete {len(files)} files (dry-run)")
                return True
            return _perform_deletion(files)
        elif response in ('n', 'no'):
            print("Operation cancelled")
            return False
        elif response in ('d', 'dry-run'):
            print(f"Would delete {len(files)} files (dry-run)")
            return True
        elif response in ('p', 'preview'):
            for i, f in enumerate(files, 1):
                print(f"{i}. {f.name} ({f.stat().st_size/1024:.1f} KB)")
        else:
            print("Invalid input. Please choose y/n/d/p")

def _perform_deletion(files: list[Path]) -> bool:
    """Helper function to actually delete files with error handling"""
    success_count = 0
    for f in files:
        try:
            f.unlink()
            success_count += 1
        except Exception as e:
            print(f"⚠️ Failed to delete {f.name}: {str(e)}")
    
    print(f"Deleted {success_count}/{len(files)} files")
    return success_count == len(files)