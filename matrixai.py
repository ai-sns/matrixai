import platform
import sys

def detect_platform():
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "mac"
    else:
        return "unsupported"

def main():
    detected = detect_platform()

    if detected == "windows":
        import windows as platform_app
    elif detected == "mac":
        import mac as platform_app
    else:
        print(f"[ERROR] Unsupported platform: {platform.system()}")
        sys.exit(1)

    platform_app.main()

if __name__ == "__main__":
    main()
