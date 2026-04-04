import traceback
import sys

try:
    from app.main import app

    print("Success")
except Exception as e:
    with open("error.txt", "w") as f:
        traceback.print_exc(file=f)
