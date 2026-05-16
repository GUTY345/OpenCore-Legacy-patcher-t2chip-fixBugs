#!/bin/bash
VERSION=$1
if [ -z "$VERSION" ]; then
    VERSION="1.0.0"
fi

echo "🚀 Starting PKG Build for version: $VERSION"

# สร้างโฟลเดอร์
mkdir -p dist
cd source || { echo "❌ Cannot find source folder"; exit 1; }

# คัดลอก payload (ปรับตามโครงสร้างจริงของคุณ)
mkdir -p ../payload/OpenCore-Legacy-Patcher-T2.app
# ถ้า source มีโฟลเดอร์ opencore_legacy_patcher หรือ OpenCore-Patcher.app ให้ปรับตรงนี้
if [ -d "opencore_legacy_patcher" ]; then
    cp -R opencore_legacy_patcher/* ../payload/ 2>/dev/null || true
fi

cd ..

# === Build Installer PKG ===
pkgbuild --root payload \
         --identifier com.guty345.oclp.t2fix \
         --version "$VERSION" \
         --install-location "/Applications" \
         --scripts ci_tooling/pkg_assets/scripts \
         --component-plist ci_tooling/pkg_assets/component.plist \
         "dist/OpenCore-Legacy-Patcher-T2-$VERSION.pkg"

# === Build Uninstaller PKG ===
pkgbuild --nopayload \
         --identifier com.guty345.oclp.t2fix.uninstall \
         --version "$VERSION" \
         --scripts ci_tooling/pkg_assets/uninstall_scripts \
         "dist/OpenCore-Legacy-Patcher-T2-Uninstaller-$VERSION.pkg"

echo "✅ Build completed!"
ls -la dist/