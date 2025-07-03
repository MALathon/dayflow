---
name: Folder Reorganization Migration
about: Add migration support when changing folder_organization setting
title: 'feat: Add migration support for folder_organization changes'
labels: enhancement, vault
assignees: ''

---

## Description

When users change the `folder_organization` setting in their configuration, existing files are not migrated to the new structure. This leads to duplicate files, broken links, and orphaned notes.

## Current Behavior

- Changing `folder_organization` only affects where new files are written
- The `note_exists()` method only checks the base folder, not subfolders
- No migration or reorganization of existing files occurs
- No warnings are shown to users about potential issues

## Expected Behavior

When `folder_organization` is changed, the system should:

1. Detect existing files in the old structure
2. Offer to migrate them to the new structure (with user confirmation)
3. Update any wiki links that reference the moved files
4. Provide a dry-run option to preview changes
5. Create a backup before migration

## Proposed Solution

### 1. Add Migration Command
```bash
dayflow vault migrate-folders --dry-run
dayflow vault migrate-folders --confirm
```

### 2. Enhanced File Discovery
- Update `note_exists()` to search recursively in all subfolder patterns
- Maintain a mapping of old paths to new paths during migration

### 3. Link Update Logic
- Parse all markdown files for wiki links
- Update links to point to new locations
- Handle both `[[...]]` and `[...]()` link formats

### 4. Safety Features
- Automatic backup before migration
- Rollback option if migration fails
- Detailed logging of all changes

## Example Scenarios

### Scenario 1: Flat to Date-Based
- Before: `/Calendar/2024-01-15 Team Meeting.md`
- After: `/Calendar/2024/01/15/0900 - Team Meeting.md`

### Scenario 2: Date-Based to Flat
- Before: `/Calendar/2024/01/15/0900 - Team Meeting.md`
- After: `/Calendar/2024-01-15 Team Meeting.md`

### Scenario 3: Changing Date Pattern
- Before: `/Calendar/2024/01/15/Meeting.md` (year/month/day)
- After: `/Calendar/2024/W03/Meeting.md` (year/week)

## Technical Considerations

- Handle large vaults efficiently
- Preserve file metadata (creation/modification times)
- Support for custom folder patterns
- Cross-platform path handling

## Alternative Approach

If full migration is too complex, at minimum:
1. Update `note_exists()` to search all possible locations
2. Add warnings when changing `folder_organization`
3. Provide a tool to find and report duplicate files
