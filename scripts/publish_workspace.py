import os
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from observstory.workspace import publish
publish(pathlib.Path.cwd(), os.environ.get("OBSERVSTORY_SHA") or "HEAD", os.environ.get("OBSERVSTORY_OUTPUT", "observstory"))
