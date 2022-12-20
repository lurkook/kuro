from PIL import Image, ImageCms
import struct
import os
import io
import argparse
import sys

parser = argparse.ArgumentParser(description="UbiArt Wii texture encoder")

parser.add_argument("-i", "--input", help="Input image", required=True)
parser.add_argument("-o", "--output", help="Output texture")
parser.add_argument("-w", "--wimgt-executable-path",
                    default="wimgt.exe", help="Path to Wiimms Image Tool")
parser.add_argument("-m", "--masked", action="store_true",
                    help="Texture should be masked?")


# PIL saves PNGs with sRGB profile what makes Wiimm Image Tool crash
# I used code from https://github.com/python-pillow/Pillow/issues/6467
# to create this function
def safe_save(img, output_path):
    # Getting current image profile and creating the clean sRGB profile
    profile = img.info["icc_profile"]
    srgb_profile = ImageCms.createProfile("sRGB")

    # Converting input image from original profile to clean sRGB profile
    safe_img = ImageCms.profileToProfile(
        img, io.BytesIO(profile), srgb_profile)

    # Save .PNG image with clean sRGB profile
    safe_img.save(output_path, icc_profile=ImageCms.ImageCmsProfile(
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

    safe_save(alpha_texture, "temp/alpha_source.png")
    safe_save(alpha_texture, "temp/mask_source.png")

    for source_texture in ["temp/alpha_source.png", "temp/mask_source.png"]:
        # Convert source texture to TEX format with CMPR encoding
        destination_texture = source_texture.split(".")[0] + ".tex"
        os.system(f"{args.wimgt_executable_path} ENCODE \"{source_texture}\" --transform tex.cmpr --overwrite --strip  --dest \"temp/{destination_texture}\"")

        # Opening the destination texture
        with open(destination_texture, "rb") as f:
            assert f.read(4) == b"TEX0"

            # Getting the texture data size and read it
            f.seek(0x14, os.SEEK_SET)
            tex_size = struct.unpack(">I", f.read(4))[0]

            f.seek(0x40, os.SEEK_SET)
            tex_data = f.read(tex_size)

            # Write the texture data to our passed writeable IO
            writer_io.write(tex_data)

        # Remove source texture & destination texture
        # from temporary directory
        os.remove(source_texture)
        os.remove(destination_texture)


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
    os.system(f"{args.wimgt_executable_path} ENCODE \"temp/source_texture.png\" --transform tex.cmpr --overwrite --strip --dest \"temp/destination_texture.tex\"")
    destination_texture = "temp/destination_texture.tex"

    # Opening the destination texture
    with open(destination_texture, "rb") as f:
        assert f.read(4) == b"TEX0"

        # Getting the texture data size and read it
        f.seek(0x14, os.SEEK_SET)
        tex_size = struct.unpack(">I", f.read(4))[0]

        f.seek(0x40, os.SEEK_SET)
        tex_data = f.read(tex_size)

        # Write the texture data to our passed writeable IO
        writer_io.write(tex_data)

    # Remove source texture & destination texture
    # from temporary directory
    os.remove(source_texture)
    os.remove(destination_texture)


def main():
    # Parse the command line arguments
    args = parser.parse_args()

    # If temporary directory is not exists
    # create the new ones
    if not os.path.exists("temp"):
        os.mkdir("temp")

    # Getting the information from command line arguments
    input_file = args.input
    masked = args.masked
    output_file = args.output if args.output else os.path.splitext(args.input)[
        0] + ".tga.ckd"

    # Open the image using PIL library
    img = Image.open(input_file)
    w, h = img.size

    # Checks the image size
    if w % 2 != 0 or h % 2 != 0:
        print(
            "Bad image input. Width and height should be width and height with a power of 2")
        sys.exit(-1)

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

    # If temporary directory is empty, we will remove it
    if len(os.listdir("temp")) == 0:
        os.rmdir("temp")


if __name__ == "__main__":
    main()
