#!/bin/bash

VERSION=$1
IDENTIFIER="com.guty345.oclp.t2fix"
INSTALL_LOCATION="/Library/Application Support/Dortania"
RESOURCES_DIR="ci_tooling/resources"
DIST_DIR="dist"

echo "Starting Build for Version: $VERSION"

# 1. Prepare Staging Areas
rm -rf payload_installer payload_uninstaller tmp_scripts build_meta
mkdir -p "payload_installer$INSTALL_LOCATION"
mkdir -p "payload_uninstaller/tmp"
mkdir -p tmp_scripts/installer tmp_scripts/uninstaller build_meta
mkdir -p "$RESOURCES_DIR"

# 2. Prepare Scripts
if [ -f "ci_tooling/postinstall.sh" ]; then
    cp "ci_tooling/postinstall.sh" "tmp_scripts/installer/postinstall"
    chmod +x "tmp_scripts/installer/postinstall"
fi
if [ -f "ci_tooling/preinstall.sh" ]; then
    cp "ci_tooling/preinstall.sh" "tmp_scripts/uninstaller/preinstall"
    chmod +x "tmp_scripts/uninstaller/preinstall"
fi

# 3. Extract Icon from App (If exists)
if [ -d "$DIST_DIR/OpenCore-Patcher.app" ]; then
    cp -R "$DIST_DIR/OpenCore-Patcher.app" "payload_installer$INSTALL_LOCATION/"
    cp "payload_installer$INSTALL_LOCATION/OpenCore-Patcher.app/Contents/Resources/AppIcon.icns" "$RESOURCES_DIR/icon.icns" 2>/dev/null || true
fi

# 4. Build Component Package (The core files)
pkgbuild --root payload_installer \
         --identifier "$IDENTIFIER" \
         --version "$VERSION" \
         --install-location "/" \
         --scripts tmp_scripts/installer \
         "build_meta/core.pkg"

# 5. Generate distribution.xml and Build Final Product (With UI)
# เราจะใช้ sed เพื่อฉีดเวอร์ชันเข้าไปใน XML
cat <<EOF > build_meta/distribution.xml
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>OpenCore Legacy Patcher T2</title>
    <welcome file="welcome.txt"/>
    <options customize="never" require-scripts="false"/>
    <choices-outline>
        <line choice="default"/>
    </choices-outline>
    <choice id="default" title="OpenCore Legacy Patcher T2">
        <pkg-ref id="core"/>
    </choice>
    <pkg-ref id="core" version="$VERSION" onConclusion="none">core.pkg</pkg-ref>
</installer-gui-script>
EOF

productbuild --distribution build_meta/distribution.xml \
             --resources "$RESOURCES_DIR" \
             --package-path build_meta \
             "$DIST_DIR/OpenCore-Patcher-T2-Installer-v$VERSION.pkg"

# 6. Build Uninstaller Component (Standalone)
pkgbuild --root payload_uninstaller \
         --identifier "$IDENTIFIER.uninstall" \
         --version "$VERSION" \
         --install-location "/tmp" \
         --scripts tmp_scripts/uninstaller \
         "$DIST_DIR/OpenCore-Patcher-T2-Uninstaller-v$VERSION.pkg"

rm -rf tmp_scripts build_meta
echo "Build Finished!"