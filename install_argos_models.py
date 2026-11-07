import argostranslate.package

print("📦 Package index update ho raha hai...")
argostranslate.package.update_package_index()

print("🔍 Available packages dhundh rahe hain...")
available = argostranslate.package.get_available_packages()

# English → Hindi
en_hi_pkg = None
for pkg in available:
    if pkg.from_code == "en" and pkg.to_code == "hi":
        en_hi_pkg = pkg
        break

if en_hi_pkg:
    print(f"⬇️  Download: English → Hindi ({en_hi_pkg.package_version})")
    argostranslate.package.install_from_path(en_hi_pkg.download())
    print("✅ English → Hindi installed")
else:
    print("❌ English → Hindi package nahi mila")

# Hindi → English
hi_en_pkg = None
for pkg in available:
    if pkg.from_code == "hi" and pkg.to_code == "en":
        hi_en_pkg = pkg
        break

if hi_en_pkg:
    print(f"⬇️  Download: Hindi → English ({hi_en_pkg.package_version})")
    argostranslate.package.install_from_path(hi_en_pkg.download())
    print("✅ Hindi → English installed")
else:
    print("❌ Hindi → English package nahi mila")

print("\n🎉 Sab ho gaya! Ab test karein...")

# Quick test
from argostranslate import translate
test_text = "Hello, how are you?"
hindi = translate.translate(test_text, "en", "hi")
print(f"\nEnglish: {test_text}")
print(f"Hindi: {hindi}")

back = translate.translate(hindi, "hi", "en")
print(f"Back to English: {back}")