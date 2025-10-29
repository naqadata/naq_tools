import argparse

from naq_utils import custom_logging as logging
from naq_utils.naq_tool import NaqTool
from naq_subtitles.generate_subtitles import GenSubsTool
from naq_subtitles.rename_videos_and_subtitles import RenameTool


class SubtitlesTool(NaqTool):

    def _populate_parser(self):
        subparsers = self.parser.add_subparsers(dest="subtitle_command", required=True)
        
        gen_subs_parser = subparsers.add_parser("generate", help="Generate subtitles for video files using Whisper AI")
        self._gen_subs_tool = GenSubsTool(gen_subs_parser)

        rename_parser = subparsers.add_parser("rename_episodes", help="Rename show episodes and corresponding subtitles with standard: <Show Title> - ExxSyy")
        self._rename_parser = RenameTool(rename_parser)
        
    def main(self, args: argparse.Namespace):
        if args.subtitle_command == "generate":
            self._gen_subs_tool.main(args)
        elif args.subtitle_command == "rename_episodes":
            self._rename_parser.main(args)


def main():
    parser = argparse.ArgumentParser(prog="naq-subtitles", description="Subtitle tools")
    tool = SubtitlesTool(parser)
    args = parser.parse_args()

    tool.main(args)


if __name__ == "__main__":    
    main()
