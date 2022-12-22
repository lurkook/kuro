from PIL import Image, ImageCms
from glob import glob
import struct
import os
import io
import argparse
import sys

parser = argparse.ArgumentParser(description="UbiArt Wii texture encoder")

parser.add_argument("-i", "--input", help="Input image(s)", required=True)
parser.add_argument("-o", "--output", help="Output directory")
parser.add_argument("-w", "--wimgt-executable-path",
                    default="wimgt.exe", help="Path to Wiimms Image Tool")
parser.add_argument("-m", "--masked", action="store_true",
                    help="Texture should be masked?")
parser.add_argument("-e", "--extension-name", default="tga",
                    help="Name of extension what should be used for output file names (example. tga/png)")
parser.add_argument("-W", "--white-alpha", action="store_true",
                    help="Alpha texture should be re-masked to have white background? (This can be useful when texture gets artifacts)")


# PIL saves PNGs with sRGB profile what makes Wiimm Image Tool crash
# I used code from https://github.com/python-pillow/Pillow/issues/6467
# to create this function
def safe_save(img, output_path):
    # Creating the clean sRGB image
    srgb_profile = ImageCms.createProfile("sRGB")

    if img.info.get("icc_profile", None):
        # Getting current image profile
        profile = img.info["icc_profile"]

        # Converting input image from original profile to clean sRGB profile
        img = ImageCms.profileToProfile(
            img, io.BytesIO(profile), srgb_profile)

    # Save .PNG image with clean sRGB profile
    img.save(output_path, icc_profile=ImageCms.ImageCmsProfile(
        srgb_profile).tobytes(), format="png")


# Function for building Alpha Map Container for masked textures
def build_apmc(writer_io, img, args):
    # Write header stuff
    writer_io.write(b"APMC")  # AlPha Map Container
    writer_io.write(
        b"\0\0\0\x20\0\xFF\0\0\0\0\xFF\0\0\0\0\xFF\xFF\0\0\0\0\0\x10\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0")

    # Creating the alpha & mask source textures
    alpha_texture = img.convert("RGB").convert("RGBA")

    mask_texture = img.tobytes("raw", "A")
    mask_texture = Image.frombytes("L", img.size, mask_texture)
    mask_texture = mask_texture.convert("RGBA")

    # Creating the empty white image
    source_size = (img.size[0], img.size[1] * 2)
    source_texture = Image.new("RGB", source_size, (255, 255, 255))

    if args.white_alpha:
        # Creating the mask for alpha texture in source texture
        # This is needed because some textures can have problems with black background
        mask_for_alpha_texture = mask_texture.convert("L")
        mask_for_alpha_texture = mask_for_alpha_texture.point(
            lambda p: 255 if p > 1 else 0)
        mask_for_alpha_texture = mask_for_alpha_texture.convert("1")

        # Putting it together
        source_texture.paste(alpha_texture, (0, 0), mask_for_alpha_texture)
        source_texture.paste(mask_texture, (0, img.size[1]))
    else:
        # Putting it together
        source_texture.paste(alpha_texture, (0, 0))
        source_texture.paste(mask_texture, (0, img.size[1]))

    # Saving the input texture
    safe_save(source_texture, "temp/input_source.png")
    source_texture = "temp/input_source.png"

    # Convert source texture to TEX format with CMPR encoding
    destination_texture = "temp/destination_texture.tpl"
    os.system(f"{args.wimgt_executable_path} COPY \"{source_texture}\" --transform tpl.cmpr --overwrite --strip --dest \"{destination_texture}\"")

    # Opening the destination texture
    with open(destination_texture, "rb") as f:
        assert f.read(4) == b"\0\x20\xaf\x30"

        # Getting the texture data size and read it
        f.seek(0x40, os.SEEK_SET)
        tex_data = f.read()

        # Write the texture data to our passed writeable IO
        writer_io.write(tex_data)

    # Remove source texture & destination texture
    # from temporary directory
    # os.remove(source_texture)
    # os.remove(destination_texture)


# Function for building 1 Texture for not-masked textures
def build_1txd(writer_io, img, args):
    # Convert the image data to the RGB and save it to temporary directory
    source_texture = img.convert("RGB")
    safe_save(source_texture, "temp/source_texture.png")

    source_texture = "temp/source_texture.png"

    # Write the header stuff
    writer_io.write(b"1TXD")  # 1 TeXture (D???)
    writer_io.write(
        b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x10\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0")

    # Convert source texture to TEX format with CMPR encoding
    destination_texture = "temp/destination_texture.tpl"
    os.system(f"{args.wimgt_executable_path} ENCODE \"{source_texture}\" --transform tpl.cmpr --overwrite --strip --dest \"{destination_texture}\"")

    # Opening the destination texture
    with open(destination_texture, "rb") as f:
        assert f.read(4) == b"\0\x20\xaf\x30"

        # Getting the texture data size and read it
        f.seek(0x40, os.SEEK_SET)
        tex_data = f.read()

        # Write the texture data to our passed writeable IO
        writer_io.write(tex_data)

    # Remove source texture & destination texture
    # from temporary directory
    os.remove(source_texture)
    os.remove(destination_texture)


# Convert function
def convert(input_file, output_file, args, masked):
    # Open the image using PIL library
    img = Image.open(input_file)
    w, h = img.size

    # Checks the image size
    if w % 2 != 0 or h % 2 != 0:
        raise Exception(
            "Bad image input. Width and height should be width and height with a power of 2")

    # Writing the UbiArt texture container header
    header_buf = io.BytesIO()

    #                                                    placeholder value
    header_buf.write(b"\0\0\0\x09\x54\x45\x58\0\0\0\0\x2C\x00\x00\x80\x80")

    header_buf.write(struct.pack(">HH", w, h))
    header_buf.write(
        b"\x00\x01\x18\0\0\0\x80\x80\0\0\0\0\0\x10\0\0\0\0\0\0\0\0\xCC\xCC")

    # Writing the contained texture header
    contained_buf = io.BytesIO()
    contained_buf.write(b"\x20\x53\x44\x44\0\0\0\x7C\0\x08\x10\x07")
    contained_buf.write(struct.pack(">II", w, h))
    contained_buf.write(
        b"\0\0\x80\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x54\x54\x56\x4E\0\x02\0\x07\0\0\0\x20\0\0\0\x04")

    # If we need masked, then we will do APMC
    # If not, then 1TXD
    if masked:
        build_apmc(contained_buf, img, args)
    else:
        build_1txd(contained_buf, img, args)

    # Writing the contained data size to UbiArt header
    header_buf.seek(0xc, os.SEEK_SET)
    header_buf.write(struct.pack(">I", contained_buf.tell()))

    # Writing the data to the output file
    with open(output_file, "wb") as f:
        f.write(header_buf.getvalue() + contained_buf.getvalue())


# Main function
def main():
    # Parse the command line arguments
    args = parser.parse_args()

    # If temporary directory is not exists
    # create the new ones
    if not os.path.exists("temp"):
        os.mkdir("temp")

    # Getting the information from command line arguments
    input_files = glob(args.input)
    masked = args.masked

    if args.extension_name not in ['tga', 'png']:
        print(f"Unknown extension: {args.extension_name}")
        os.exit(-1)

    # Converting the files
    for input_file in input_files:
        # Getting the output path
        output_file = os.path.splitext(
            input_file)[0] + f".{args.extension_name}.ckd"

        if args.output:
            output_file = os.path.join(
                args.output, os.path.basename(output_file))

        print(f"{input_file} --> {output_file}")

        try:
            convert(input_file, output_file, args, masked)
        except Exception as e:
            print(f"Exception occurred while converting {input_file}:")
            print(e)

            continue

    # If temporary directory is empty, we will remove it
    if len(os.listdir("temp")) == 0:
        os.rmdir("temp")


# If current name of script is __main__,
# program execute main function
if __name__ == "__main__":
    main()
