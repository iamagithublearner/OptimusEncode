import ffmpeg
import subprocess

from pathlib import Path
from typing import List
import time
import humanize
import json
from tqdm import tqdm


class ProjectPaths:
    def __init__(self):
        self.json = Path()
        self.FolderPath = Path()
        self.OutputPath = Path()

    def noConfigFile(self):
        print("Secrets.py was not found.Please provide path for the following files")
        self.json = Path(input("JSON file path for video conversion:"))
        self.FolderPath = Path(input("Absolute path to scan videos in:"))
        self.OutputPath = Path(input("Absolute path for encoded media output:"))

    def usingConfigFile(self, jsonPath: Path):
        print("Config file was found, using it to set JSON path , Scan path")
        with open(jsonPath, 'r') as file:
            secret_data = json.load(file)
        self.json = secret_data["json_path"]
        self.FolderPath = secret_data["folder_path"]
        self.OutputPath = secret_data["output_path"]


h264_files = []
hevc_files = []
other_files = []
h264_file_paths: List[Path] = []
hevc_file_paths: List[Path] = []
other_file_paths: List[Path] = []


def convert_video(Input_file, Output_file, json_file, debug=False):
    # Command to execute HandBrakeCLI
    command = [
        'HandBrakeCLI',
        '--preset-import-file', json_file,
        '-i', Input_file,  # Input file

        'file', 'name',
        '-o', Output_file,  # Output file
    ]
    if debug:
        command.insert(1, '-v')

    # Run the command
    try:
        subprocess.run(command, check=True)
        print("Conversion completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")


# HandBrakeCLI -v --preset-import-file custom.json -i C:\Users\sixsi\Videos\11.webm file name -o outputfile.mp4

def codec_extractor(file_path: Path):
    data = ffmpeg.probe(file_path)
    return data['streams'][0]['codec_name']


def encode_files(file_path_list: List[Path], outputPath):
    for file_path in file_path_list:
        print(f"Encoding: {file_path.name}")
        new_file_path = outputPath / file_path.name
        convert_video(file_path, new_file_path, json)
        original_file_size = humanize.naturalsize(file_path.stat().st_size)
        new_file_size = humanize.naturalsize(new_file_path.stat().st_size)
        space_saved = file_path.stat().st_size - new_file_path.stat().st_size
        print(
            f"Size before encode: {original_file_size} Size after encode: {new_file_size} Space saved: {humanize.naturalsize(space_saved)}")
        if space_saved < 0:
            print(f"new file is larger , deleting the new file {new_file_path}")
            new_file_path.unlink()


class InitialScan:

    def __init__(self):
        self.total_size_h264Files = 0
        self.total_size_hevcFiles = 0
        self.total_size_otherFiles = 0
        self.error_files = []

    def perform_initial_scan(self, folder_path: Path, debug=False):
        if not folder_path.is_dir():
            print("This is not a directory path! \n Exiting.")
            exit()

        for file_path in folder_path.iterdir():
            file_name = file_path.name
            # Converts file size from bytes to Megabytes
            file_size = file_path.stat().st_size

            # Check if it's a regular file (not a directory)
            if file_path.is_file():
                try:
                    codec = codec_extractor(file_path=file_path)
                    if codec == "h264":
                        h264_files.append(file_name)
                        h264_file_paths.append(file_path)
                        self.total_size_h264Files += file_size
                    elif codec == "hevc":
                        hevc_files.append(file_name)
                        hevc_file_paths.append(file_path)
                        self.total_size_hevcFiles += file_size
                    else:
                        other_files.append(file_name)
                        other_file_paths.append(file_path)
                        self.total_size_otherFiles += file_size
                    if debug:
                        print(f"File: {file_name}, Path: {file_path}, Size: {humanize.naturalsize(file_size)}")
                        print(codec)

                except Exception as e:
                    print('something went wrong')
                    print(f"Error caught: {e}")
                    self.error_files.append(file_name)

    def print_error_files(self):
        # Error info at end
        if len(self.error_files) > 0:
            for file in self.error_files:
                print(file)
            else:
                print("No error files were found")


def main():
    PathObject = ProjectPaths()

    # Check if JSON file config file is present or not
    try:
        json_file_path = Path('Config.json')
        PathObject.usingConfigFile(json_file_path)
    except FileNotFoundError:
        PathObject.noConfigFile()

    ScanObject = InitialScan()
    print("Scanning files")
    start_time = time.time()
    ScanObject.perform_initial_scan(folder_path=PathObject.FolderPath)
    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_minutes = elapsed_time // 60
    elapsed_seconds = elapsed_time - elapsed_minutes * 60
    print(f"Scan completed in {elapsed_minutes:.2f} minutes, {elapsed_seconds:.2f} seconds.")

    print(f"Total Files scanned successfully: {len(h264_files) + len(hevc_files) + len(other_files)}")
    print("hevc:", humanize.naturalsize(ScanObject.total_size_hevcFiles))
    print("h264:", humanize.naturalsize(ScanObject.total_size_h264Files))
    print("others:", humanize.naturalsize(ScanObject.total_size_otherFiles))

    user_encode_choice = input("would you like to encode h264 files?")
    if user_encode_choice.lower() == "yes":
        print("encoding h264 files")
        encode_files(h264_file_paths, PathObject.OutputPath)
    else:
        print("Exiting.")
        exit()


main()
