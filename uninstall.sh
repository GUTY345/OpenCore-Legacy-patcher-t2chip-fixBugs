#!/bin/bash

# Manual Uninstaller for OpenCore Legacy Patcher T2

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)"
  exit 1
fi

echo "Removing files..."

rm -rf "/Applications/OpenCore-Patcher.app"
rm -rf "/Library/Application Support/Dortania/OpenCore-Patcher.app"

# แจ้งเตือนเรื่อง NVRAM/EFI
echo "--------------------------------------------------------"
echo "Files removed successfully."
echo "Note: EFI partitions and NVRAM variables were not touched."
echo "Please use the Patcher app to revert Root Patches before deleting the app if possible."
echo "--------------------------------------------------------"
exit 0