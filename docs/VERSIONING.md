# Versioning Strategy

**Project**: Lodestar  
**Last Updated**: 2026-02-09

---

## 📋 Overview

This document defines how we version Project Lodestar using **Semantic Versioning 2.0.0** with clear increment rules tied to feature completion.

---

## 🔢 Semantic Versioning Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

### Components

- **MAJOR**: Breaking changes, incompatible API changes
- **MINOR**: New features, backwards-compatible
- **PATCH**: Bug fixes, backwards-compatible
- **PRERELEASE**: alpha, beta, rc (release candidate)
- **BUILD**: Build metadata (optional)

### Examples
- `1.0.0` - First stable release
- `2.0.0-beta.1` - Second major version, first beta
- `2.1.0` - Minor feature release
- `2.1.1` - Patch/bugfix release
- `2.2.0-alpha.1` - Alpha prerelease

---

## 📊 Current Version Status

### Released
- **v1.0.0** (2026-02-08) - Initial stable release
  - Multi-provider routing
  - FREE tier support
  - Basic CLI

### In Development
- **v2.1.0-alpha.1** (Current `develop` branch)
  - All v2.0-beta.1 features merged
  - Response caching added
  - Branching strategy implemented

---

## 🎯 Version Increment Rules

### When to Increment MAJOR (x.0.0)
**Breaking changes that require user action**

Examples:
- Change CLI command structure
- Remove deprecated features
- Change configuration file format
- Incompatible API changes

**Process**:
1. Announce breaking changes in advance
2. Provide migration guide
3. Update CHANGELOG with BREAKING CHANGE section
4. Increment major version

### When to Increment MINOR (1.x.0)
**New features, backwards-compatible**

Examples:
- Add new CLI command
- Add new module
- Add new configuration option
- Enhance existing feature (non-breaking)

**Process**:
1. Merge feature to `develop`
2. Update CHANGELOG under [Unreleased]
3. When ready to release, increment minor version
4. Move [Unreleased] items to new version section

### When to Increment PATCH (1.0.x)
**Bug fixes, backwards-compatible**

Examples:
- Fix crash or error
- Fix incorrect behavior
- Performance improvement
- Documentation fixes

**Process**:
1. Fix bug in hotfix branch
2. Merge to `main` and `develop`
3. Increment patch version
4. Update CHANGELOG

---

## 🚀 Release Workflow

### Alpha Releases (x.y.0-alpha.N)
**Purpose**: Early testing, unstable, breaking changes possible

**When**: After completing a major feature or set of features

**Process**:
```bash
# 1. Ensure all features merged to develop
git checkout develop
git pull origin develop

# 2. Update version in files
# - pyproject.toml
# - README.md (if shown)
# - CHANGELOG.md

# 3. Commit version bump
git add .
git commit -m "chore: bump version to 2.1.0-alpha.1"

# 4. Tag release
git tag -a v2.1.0-alpha.1 -m "Release v2.1.0-alpha.1"
git push origin develop --tags
```

**Frequency**: As needed, after significant features

### Beta Releases (x.y.0-beta.N)
**Purpose**: Feature-complete, testing for bugs, API stable

**When**: All planned features complete, ready for testing

**Process**:
```bash
# 1. Create release branch
git checkout develop
git checkout -b release/v2.1.0-beta.1

# 2. Update version and docs
# - pyproject.toml
# - README.md
# - CHANGELOG.md (move Unreleased to version section)

# 3. Final testing
pytest modules/tests/ -v

# 4. Commit and tag
git add .
git commit -m "chore: prepare v2.1.0-beta.1 release"
git tag -a v2.1.0-beta.1 -m "Release v2.1.0-beta.1"

# 5. Merge to main
git checkout main
git merge --no-ff release/v2.1.0-beta.1
git push origin main --tags

# 6. Merge back to develop
git checkout develop
git merge --no-ff release/v2.1.0-beta.1
git push origin develop
```

**Frequency**: When feature-complete for a minor version

### Release Candidates (x.y.0-rc.N)
**Purpose**: Final testing before stable, no new features

**When**: After beta testing, no major bugs found

**Process**: Same as beta, but with `-rc.N` suffix

**Frequency**: 1-2 weeks before stable release

### Stable Releases (x.y.0)
**Purpose**: Production-ready, stable, supported

**When**: After RC testing, ready for production

**Process**:
```bash
# 1. Create release branch
git checkout develop
git checkout -b release/v2.1.0

# 2. Final version update
# Remove prerelease suffix
# Update all docs

# 3. Full test suite
pytest modules/tests/ -v
# Manual testing
# Performance testing

# 4. Merge to main
git checkout main
git merge --no-ff release/v2.1.0
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin main --tags

# 5. Merge back to develop
git checkout develop
git merge --no-ff release/v2.1.0
git push origin develop

# 6. Create GitHub release
# - Upload artifacts
# - Write release notes
# - Announce to community
```

**Frequency**: When stable and ready for production

---

## 📅 Version Roadmap

### Current: v2.1.0-alpha.1 (develop branch)
**Status**: In development  
**Features**:
- ✅ Health monitoring
- ✅ Cost dashboard
- ✅ Visual diff AI
- ✅ Self-healing agent
- ✅ Response caching
- 🚧 Model warm-up
- 🚧 Connection pooling
- 🚧 GPU optimization

**Next Release**: v2.1.0-alpha.2 (when warm-up + pooling complete)

### Planned: v2.1.0-beta.1
**Target**: Week of Feb 16  
**Requirements**:
- All performance features complete
- Integration tests passing
- Documentation updated

### Planned: v2.1.0 (stable)
**Target**: Week of Feb 23  
**Requirements**:
- Beta testing complete
- No critical bugs
- Production-ready

### Future: v2.2.0
**Target**: Week of Mar 2  
**Features**:
- GPU monitoring
- Provider dashboard
- Model recommendations

### Future: v3.0.0
**Target**: Q2 2026  
**Features**:
- Web UI (breaking: new deployment model)
- Multi-project support
- Breaking API changes

---

## 🔄 Version Increment Triggers

### Automatic Triggers

| Event | Version Change | Example |
|-------|---------------|---------|
| Merge feature to develop | Update [Unreleased] | No version change yet |
| Complete sprint milestone | Alpha release | 2.1.0-alpha.1 → 2.1.0-alpha.2 |
| All features for minor complete | Beta release | 2.1.0-alpha.N → 2.1.0-beta.1 |
| Beta testing complete | RC release | 2.1.0-beta.N → 2.1.0-rc.1 |
| RC approved | Stable release | 2.1.0-rc.N → 2.1.0 |
| Hotfix merged | Patch release | 2.1.0 → 2.1.1 |

### Manual Triggers

- Breaking changes → Major version (requires approval)
- New feature set → Minor version (when ready)
- Critical bug → Patch version (immediate)

---

## 📝 Version Update Checklist

### Files to Update

When bumping version, update these files:

1. **`pyproject.toml`**
   ```toml
   [project]
   version = "2.1.0-alpha.1"
   ```

2. **`CHANGELOG.md`**
   ```markdown
   ## [2.1.0-alpha.1] - 2026-02-09
   
   ### Added
   - Feature X
   
   ### Changed
   - Improvement Y
   
   ### Fixed
   - Bug Z
   ```

3. **`README.md`** (if version shown)
   ```markdown
   **Current Status:** v2.1.0-alpha.1
   ```

4. **`docs/PROJECT_STATUS_*.md`** (current status doc)
   - Update version references

5. **Git Tag**
   ```bash
   git tag -a v2.1.0-alpha.1 -m "Release v2.1.0-alpha.1"
   ```

### Commit Message Format
```
chore: bump version to 2.1.0-alpha.1

- Update pyproject.toml
- Update CHANGELOG.md
- Update README.md
- Tag release
```

---

## 🎯 Feature → Version Mapping

### v2.1.0 Features

| Feature | Status | Triggers |
|---------|--------|----------|
| Response caching | ✅ Complete | alpha.1 |
| Model warm-up | 🚧 In Progress | alpha.2 |
| Connection pooling | ⏳ Planned | alpha.2 |
| GPU optimization | ⏳ Planned | alpha.3 |
| **All complete** | ⏳ | **beta.1** |

**Rule**: Each completed feature set triggers an alpha release

### v2.2.0 Features

| Feature | Status | Triggers |
|---------|--------|----------|
| GPU monitoring | ⏳ Planned | alpha.1 |
| Provider dashboard | ⏳ Planned | alpha.2 |
| Model recommendations | ⏳ Planned | alpha.3 |
| **All complete** | ⏳ | **beta.1** |

---

## 🔍 Version Checking

### In Code
```python
# pyproject.toml
[project]
version = "2.1.0-alpha.1"

# Access in Python
import importlib.metadata
version = importlib.metadata.version("lodestar")
```

### In CLI
```bash
# Add version command
lodestar --version
# Output: Lodestar v2.1.0-alpha.1

# Or in status
lodestar status
# Shows version in output
```

### In Git
```bash
# List all tags
git tag

# Show current version
git describe --tags

# Show latest release
git tag --sort=-v:refname | head -1
```

---

## 📊 Version History

```
v1.0.0 (2026-02-08) - Initial stable release
├── v2.0.0-alpha.1 (2026-02-09) - Module system
├── v2.0.0-alpha.2 (2026-02-09) - Proxy integration
├── v2.0.0-beta.1 (2026-02-09) - All v2.0 features
└── v2.1.0-alpha.1 (2026-02-09) - Response caching [CURRENT]
    ├── v2.1.0-alpha.2 (planned) - Warm-up + pooling
    ├── v2.1.0-beta.1 (planned) - Feature complete
    └── v2.1.0 (planned) - Stable release
```

---

## 🎓 Best Practices

### DO ✅
- Increment version with each significant change
- Update CHANGELOG for every release
- Tag all releases in git
- Follow semantic versioning strictly
- Communicate breaking changes early

### DON'T ❌
- Skip version numbers
- Reuse version tags
- Make breaking changes in minor/patch
- Release without updating CHANGELOG
- Tag without testing

---

## 📞 Quick Reference

### Current Version
```
v2.1.0-alpha.1 (develop branch)
```

### Next Version
```
v2.1.0-alpha.2 (after warm-up + pooling)
```

### Version Files
- `pyproject.toml` - Source of truth
- `CHANGELOG.md` - Version history
- Git tags - Release markers

### Commands
```bash
# Check version
git describe --tags

# Create release
git tag -a v2.1.0-alpha.2 -m "Release v2.1.0-alpha.2"
git push origin --tags

# List versions
git tag --sort=-v:refname
```

---

**Remember**: Version numbers communicate change. Use them wisely! 🚀
