import argparse
from naq_utils.logging import logger
from naq_utils.extensions import Path
from naq_utils.naq_tool import NaqTool
import webvtt

class ConvertSubsTool(NaqTool):
    def _populate_parser(self):
        self.parser.add_argument("--input_type", choices=['srt'], default='srt', help='Type of the input subtitle files.')
        self.parser.add_argument("--output_type", choices=['vtt'], default='vtt', help='Type of the output subtitle files.')    
        
    def main(self, args: argparse.Namespace):
        for input_file_path in sorted(Path.cwd().rglob(f"*.{args.input_type}")):
            output_file_path = input_file_path.with_suffix(f".{args.output_type}")
            logger.info(f"Converting {input_file_path} to {output_file_path}")
            if args.input_type == 'srt' and args.output_type == 'vtt':
                webvtt.from_srt(str(input_file_path)).save(str(output_file_path))
                input_file_path.unlink()
            else:
                logger.error(f"Conversion from {args.input_type} to {args.output_type} is not supported.")