"""Graphics Lab: interactive demos for NCSD302 Units 3 and 4.

Run:
    python3 main.py                  (macOS / Linux)
    py main.py                       (Windows)

Save one frame as an image instead of opening the interactive window:
    python3 main.py --preview shot.png --demo 4 --mode 2
"""

import argparse

from core.app import App
from demos.transforms_2d import Transforms2DDemo
from demos.transforms_3d import Transforms3DDemo
from demos.viewing_projection import ViewingProjectionDemo
from demos.clipping_demo import ClippingDemo
from demos.illumination_shading import IlluminationShadingDemo
from demos.zbuffer_demo import ZBufferDemo
from demos.scan_conversion import ScanConversionDemo
from demos.colour_models import ColourModelsDemo
from demos.display_pipeline import DisplayPipelineDemo
from demos.pipeline_walkthrough import PipelineWalkthroughDemo


def build_app():
    """Create the window and register every demo, in sidebar order (keys 1-9, then 0)."""
    app = App("Graphics Lab - NCSD302")
    app.register(Transforms2DDemo())          # 1  Lecture 3.1
    app.register(Transforms3DDemo())          # 2  Lecture 3.1
    app.register(ViewingProjectionDemo())     # 3  Lecture 3.2
    app.register(ClippingDemo())              # 4  Lecture 3.3
    app.register(IlluminationShadingDemo())   # 5  Lecture 3.4
    app.register(ZBufferDemo())               # 6  Lecture 3.4
    app.register(ScanConversionDemo())        # 7  Lecture 3.5
    app.register(ColourModelsDemo())          # 8  Lecture 4.1
    app.register(DisplayPipelineDemo())       # 9  Lecture 4.1
    app.register(PipelineWalkthroughDemo())   # 0  the whole pipeline (end of Unit 3)
    return app


def parse_arguments():
    parser = argparse.ArgumentParser(description="Graphics Lab demos")
    parser.add_argument("--preview", metavar="PATH", help="save one frame to PATH and exit")
    parser.add_argument("--demo", type=int, default=1, help="demo number to open (default 1)")
    parser.add_argument("--mode", type=int, default=1, help="mode number within the demo (default 1)")
    return parser.parse_args()


def main():
    args = parse_arguments()
    app = build_app()
    app.select_demo(args.demo - 1)
    app.demo.set_mode(args.mode - 1)

    if args.preview:
        app.save_preview(args.preview)
    else:
        app.run()


if __name__ == "__main__":
    main()
