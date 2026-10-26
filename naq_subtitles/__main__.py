import argparse

from naq_utils.naq_tool import NaqTool
from naq_subtitles.rename_videos_and_subtitles import RenameTool
from naq_subtitles.convert_subtitles import ConvertSubsTool

subtitle_support = True

try:
    from naq_subtitles.generate_subtitles import GenSubsTool
except (OSError, ValueError, ImportError) as e:
    # Subtitle generation is an optional heavyweight feature.  The remaining
    # subtitle commands stay usable when its dependencies are not installed.
    subtitle_support = False


class SubtitlesTool(NaqTool):

    def _populate_parser(self):
        subparsers = self.parser.add_subparsers(dest="subtitle_command", required=True)

        if subtitle_support:
            gen_subs_parser = subparsers.add_parser("generate", help="Generate subtitles for video files using Whisper AI")
            self._gen_subs_tool = GenSubsTool(gen_subs_parser)

        rename_parser = subparsers.add_parser("rename", help="Rename show episodes and corresponding subtitles with standard: <Show Title> - ExxSyy")
        self._rename_tool = RenameTool(rename_parser)

        convert_parser = subparsers.add_parser("convert", help="Convert subtitlesn from one type to another")
        self._convert_tool = ConvertSubsTool(convert_parser)

    def main(self, args: argparse.Namespace):
        if args.subtitle_command == "generate":
            self._gen_subs_tool.main(args)
        elif args.subtitle_command == "rename":
            self._rename_tool.main(args)
        elif args.subtitle_command == "convert":
            self._convert_tool.main(args)


def main():
    parser = argparse.ArgumentParser(prog="naq-subtitles", description="Subtitle tools")
    tool = SubtitlesTool(parser)
    args = parser.parse_args()

    tool.main(args)


if __name__ == "__main__":
    main()
