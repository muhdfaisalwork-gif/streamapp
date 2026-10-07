from upload_releases_retry import main
import sys, upload_releases_retry
upload_releases_retry.JOBS = [
    ("StreamApp-Setup-x64.exe",
     __import__("pathlib").Path(r"G:\streaming app\packaging\windows\app\dist-inst-1685496051\ShadowStream-Setup-x64.exe"),
     "application/vnd.microsoft.portable-executable"),
]
sys.exit(upload_releases_retry.main())
