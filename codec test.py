import ffmpeg
import os
import subprocess
from secrets import secret
input_file = secret.input_file
output_file = secret.output_file
json = secret.json
folder_path = secret.folder_path
error_files = []
h264_files = []
hevc_files = []
other_files = []
h264_file_paths = []
hevc_file_paths = []
other_file_paths = []
total_size_h264 = 0
total_size_hevc = 0
total_size_other = 0


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


def codec_extractor(file_path):
    data = ffmpeg.probe(file_path)
    return data['streams'][0]['codec_name']


# Scan all files
def perform_initial_scan(debug=False):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        file_size = int(os.path.getsize(file_path) / (1024 * 1024))
        # Check if it's a regular file (not a directory)
        if os.path.isfile(file_path):
            try:
                codec = codec_extractor(file_path)
                if codec == "h264":
                    h264_files.append(file_name)
                    h264_file_paths.append(file_path)
                    total_size_h264 = total_size_h264 + file_size
                elif codec == "hevc":
                    hevc_files.append(file_name)
                    hevc_file_paths.append(file_path)
                    total_size_hevc = total_size_hevc + file_size
                else:
                    other_files.append(file_name)
                    other_file_paths.append(file_path)
                    total_size_other = total_size_other + file_size
                if debug:
                    print(f"File: {file_name}, Path: {file_path}, Size: {file_size} MB")
                    print(codec)

            except Exception as e:
                print('something went wrong')
                error_files.append(file_name)
    # Error info at end
    if len(error_files) > 0:
        for file in error_files:
            print(file)
        else:
            print("No error files were found")


def encode_files(file_list: list, outputPath):
    for file_path in file_list:
        print(f"Encoding: {os.path.basename(file_path)}")
        new_file_path = os.path.join(outputPath, os.path.basename(file_path))
        original_file_sizeMB = int(os.path.getsize(file_path) / (1024 * 1024))
        convert_video(file_path, new_file_path, json)
        new_file_sizeMB = int(os.path.getsize(new_file_path) / (1024 * 1024))
        space_saved = original_file_sizeMB - new_file_sizeMB
        print(
            f"Size before encode: {original_file_sizeMB} Size after encode: {new_file_sizeMB} Space saved: {int(space_saved)}")
        if space_saved < 0:
            print(f"new file is larger , deleting the new file {new_file_path}")
            os.remove(new_file_path)

def main():
    print("Scanning files")
    perform_initial_scan()
    print(f"Total Files scanned successfully: {len(h264_files) + len(hevc_files) + len(other_files)}")
    print("hevc:", total_size_hevc)
    print("h264:", total_size_h264)
    print("others:", total_size_other)

    user_encode_choice = input("would you like to encode h264 files?")
    if user_encode_choice.lower() == "yes":
        print("encoding h264 files")
        encode_files(h264_file_paths, r'C:\Users\sixsi\PycharmProjects\encode_details\encoded_videos_test')
    else:
        print("Exiting.")
        exit()


main()
