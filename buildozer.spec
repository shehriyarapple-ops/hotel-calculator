[app]
title = Hotel Calculator
package.name = hotelcalc
package.domain = org.hotelcalc
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 34
android.minapi = 21
android.archs = arm64-v8a
android.archs = arm64-v8a
android.accept_sdk_license = True

p4a.fork = kivy
p4a.branch = release-2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
