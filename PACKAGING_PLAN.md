# Packaging & Distribution Plan

## Current Status

✅ **Complete**:
- PyInstaller spec file (`speckit-editor.spec`)
- Documentation (developer-guide.md packaging section)
- Build instructions for all platforms

⚠️ **Known Issues**:
- Python 3.14.2 + PyInstaller 6.x + keyring → `ValueError: invalid version in keyring metadata`
- **Workaround**: Use Python 3.11 or 3.12 for packaging

---

## Task T183: Test Packaged Executables

### Prerequisites

1. **Downgrade to Python 3.12** (temporary for packaging):
   ```powershell
   # Install Python 3.12 if not available
   # Update PATH to use 3.12 first
   python --version  # Should show 3.12.x
   ```

2. **Install PyInstaller**:
   ```powershell
   pip install pyinstaller==6.11.1
   ```

3. **Verify Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

### Build Process

#### Windows (.exe)

```powershell
# Clean previous builds
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# Build executable
python -m PyInstaller speckit-editor.spec

# Output: dist/Speckit Editor.exe (~150MB uncompressed)
```

**Test Checklist** (Windows):
- [ ] Application launches without errors
- [ ] Main window displays correctly
- [ ] Can create new project
- [ ] Can create/edit/save documents
- [ ] Git panel initializes
- [ ] MCP panel loads
- [ ] Settings dialog opens
- [ ] Search functionality works
- [ ] Application closes cleanly

#### macOS (.app)

```bash
# Clean previous builds
rm -rf build dist

# Build application bundle
python -m PyInstaller speckit-editor.spec

# Output: dist/Speckit Editor.app (~150MB)

# Optional: Create DMG
hdiutil create -volname "Speckit Editor" -srcfolder "dist/Speckit Editor.app" -ov -format UDZO dist/speckit-editor.dmg
```

**Test Checklist** (macOS):
- [ ] App launches from Applications folder
- [ ] macOS Gatekeeper allows execution (or requires manual override)
- [ ] Window rendering correct for Retina displays
- [ ] Keyboard shortcuts work (Cmd instead of Ctrl)
- [ ] File dialogs use native macOS picker
- [ ] Git commands work with system git
- [ ] Settings persist across launches

#### Linux (AppImage recommended)

```bash
# Build standalone executable first
python -m PyInstaller speckit-editor.spec

# Package as AppImage (requires appimagetool)
# 1. Create AppDir structure
mkdir -p Speckit-Editor.AppDir/usr/{bin,share/applications,share/icons}

# 2. Copy executable
cp -r dist/Speckit-Editor/* Speckit-Editor.AppDir/usr/bin/

# 3. Create desktop entry
cat > Speckit-Editor.AppDir/usr/share/applications/speckit-editor.desktop <<EOF
[Desktop Entry]
Name=Speckit Editor
Exec=Speckit-Editor
Icon=speckit-editor
Type=Application
Categories=Development;TextEditor;
EOF

# 4. Add icon (if available)
# cp icon.png Speckit-Editor.AppDir/usr/share/icons/speckit-editor.png

# 5. Create AppRun
cat > Speckit-Editor.AppDir/AppRun <<EOF
#!/bin/bash
SELF=\$(readlink -f "\$0")
HERE=\${SELF%/*}
exec "\$HERE/usr/bin/Speckit-Editor" "\$@"
EOF
chmod +x Speckit-Editor.AppDir/AppRun

# 6. Build AppImage
appimagetool Speckit-Editor.AppDir Speckit-Editor-x86_64.AppImage
```

**Test Checklist** (Linux):
- [ ] AppImage executes on Ubuntu 22.04+
- [ ] AppImage executes on Fedora 38+
- [ ] AppImage executes on Arch Linux
- [ ] Desktop integration works
- [ ] Git operations use system git
- [ ] File permissions handled correctly

---

## Task T184: Optimize Bundle Size

### Current Size Estimates
- **Windows**: ~150MB (uncompressed), ~50MB (UPX compressed)
- **macOS**: ~150MB (.app bundle)
- **Linux**: ~150MB (AppImage)

### Optimization Strategies

#### 1. UPX Compression (Recommended)

**Install UPX**:
- Windows: Download from https://upx.github.io/
- macOS: `brew install upx`
- Linux: `sudo apt install upx-ucl`

**Configure PyInstaller** (add to spec file):
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Speckit Editor',
    upx=True,              # Enable UPX compression
    upx_exclude=[],        # Exclude problematic files if needed
    runtime_tmpdir=None,
    console=False,
    ...
)
```

**Expected Reduction**: 50-70% size reduction

#### 2. Exclude Unnecessary Modules

**Update spec file** to exclude unused dependencies:
```python
excludes = [
    'matplotlib',  # If not using charts
    'scipy',       # If not using scientific computing
    'pandas',      # If not using data analysis
    'notebook',    # If not bundling Jupyter
    'IPython',     # If not using IPython
    'tkinter',     # Using PySide6, not Tkinter
]

a = Analysis(
    ...
    excludes=excludes,
)
```

**Expected Reduction**: ~20-30MB

#### 3. Strip Debug Symbols

**Linux only**:
```bash
strip dist/Speckit-Editor/Speckit-Editor
```

**Expected Reduction**: ~10-15MB

#### 4. Optimize Python Bytecode

**Add to spec**:
```python
a = Analysis(
    ...
    optimize=2,  # Maximum optimization
)
```

#### 5. Remove Unnecessary Data Files

**Review and exclude**:
```python
datas = [
    ('src', 'src'),  # Include source
    ('docs', 'docs'),  # Exclude docs for production?
    # Exclude test files
]
```

### Target Sizes After Optimization
- **Windows**: ~40-50MB
- **macOS**: ~50-60MB (harder to compress .app bundles)
- **Linux**: ~40-50MB

---

## Task T185: Code Signing

### Windows Code Signing

**Requirements**:
- Code signing certificate (.pfx file)
- `signtool.exe` (Windows SDK)

**Process**:
```powershell
# Sign executable
signtool sign /f certificate.pfx /p PASSWORD /t http://timestamp.digicert.com /fd SHA256 "dist/Speckit Editor.exe"

# Verify signature
signtool verify /pa "dist/Speckit Editor.exe"
```

**Cost**: ~$200-500/year for certificate

### macOS Code Signing & Notarization

**Requirements**:
- Apple Developer account ($99/year)
- Developer ID certificate

**Process**:
```bash
# 1. Sign application
codesign --force --deep --sign "Developer ID Application: Your Name" "dist/Speckit Editor.app"

# 2. Create ZIP for notarization
ditto -c -k --keepParent "dist/Speckit Editor.app" speckit-editor.zip

# 3. Submit for notarization
xcrun notarytool submit speckit-editor.zip --apple-id YOUR_APPLE_ID --password APP_SPECIFIC_PASSWORD --team-id TEAM_ID --wait

# 4. Staple notarization ticket
xcrun stapler staple "dist/Speckit Editor.app"

# 5. Verify
codesign --verify --deep --strict "dist/Speckit Editor.app"
spctl -a -vvv -t install "dist/Speckit Editor.app"
```

**Cost**: $99/year (Apple Developer)

### Linux (Optional)

**GPG Signing** (free):
```bash
# Create detached signature
gpg --detach-sign --armor Speckit-Editor-x86_64.AppImage

# Creates Speckit-Editor-x86_64.AppImage.asc
```

**Verification**:
```bash
gpg --verify Speckit-Editor-x86_64.AppImage.asc Speckit-Editor-x86_64.AppImage
```

---

## Distribution Checklist

### Pre-Release
- [ ] All tests passing (182/225 = 81%)
- [ ] Documentation complete
- [ ] README.md updated
- [ ] LICENSE file included
- [ ] CONTRIBUTING.md included

### Build Artifacts
- [ ] Windows: `Speckit-Editor-v1.0.0-win64.exe` (signed)
- [ ] macOS: `Speckit-Editor-v1.0.0-macos.dmg` (signed & notarized)
- [ ] Linux: `Speckit-Editor-v1.0.0-x86_64.AppImage` (signed)

### Release Process
1. Tag version: `git tag v1.0.0`
2. Push tag: `git push origin v1.0.0`
3. Create GitHub Release
4. Upload build artifacts
5. Update release notes
6. Announce release

---

## Workarounds for Python 3.14 Issue

### Option 1: Use Python 3.12 (Recommended)

```powershell
# Install Python 3.12 via pyenv or direct download
# Build with 3.12, run with any version
```

### Option 2: Wait for PyInstaller 7.0

- Track: https://github.com/pyinstaller/pyinstaller/issues/8717
- ETA: Unknown (keyring/distutils compatibility)

### Option 3: Patch keyring (Advanced)

```powershell
# Remove keyring from bundled dependencies
pip uninstall keyring
# Rebuild without keyring support
```

---

## Next Steps

1. **T183**: Build and test on all platforms (use Python 3.12)
2. **T184**: Apply UPX compression, exclude unused modules
3. **T185**: Obtain certificates, sign executables

**Time Estimate**:
- T183: 2-3 hours (building + testing)
- T184: 30-60 minutes (optimization)
- T185: 2-4 hours (certificate setup + signing)

**Total**: ~5-8 hours for complete packaging pipeline

---

## Success Criteria

✅ **T183 Complete** when:
- Executable runs on Windows 10/11
- .app runs on macOS 12+ (Monterey)
- AppImage runs on Ubuntu 22.04+

✅ **T184 Complete** when:
- Bundle size < 60MB on all platforms
- Startup time < 3s (SC-007)

✅ **T185 Complete** when:
- Windows executable signed with valid certificate
- macOS .app notarized by Apple
- Linux AppImage has GPG signature

---

**Status**: Ready to execute - waiting for Python 3.12 environment or PyInstaller 7.0 release
