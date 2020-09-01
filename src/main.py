import math
import sys
import shutil
from pathlib import Path

import click
from psd_tools import PSDImage
from PIL import Image

@click.command()
@click.option('--in', prompt='Input path', help='The path to directory containing psd files')
@click.option('--out', prompt='Output path', help='The path to place output')
def main(**kwargs: str) -> None:
	input_dir = Path(kwargs["in"])
	output_dir = Path(kwargs["out"])

	print(f"Generating art assets: {str(input_dir)} -> {str(output_dir)}")
	if not input_dir.exists():
		print("ERROR: No such directory:", input_dir)
		sys.exit(1)

	if output_dir.exists():
		shutil.rmtree(output_dir)
	output_dir.mkdir()

	files_processed = 0

	for obj in input_dir.glob("**/*"):
		if obj.is_dir():
			output_dir.joinpath("/".join(obj.parts[1:])).mkdir()
		elif str(obj).endswith(".psd"):
			process_psd(obj, output_dir)
			files_processed += 1

	if files_processed == 0:
		print("ERROR: No psd files found under: ", input_dir)

	print(f"Processed {files_processed} files")


def process_psd(file_path: Path, out_path: Path) -> None:
	png_path = out_path.joinpath("/".join(file_path.parts[1:])).with_suffix(".png")
	psd = PSDImage.open(file_path)

	len_psd = len(psd)
	if len_psd > 1:
		width = nearest_square(len_psd)
		height = width
		if len_psd <= width * (width - 1):
			height = width - 1

		new_image = Image.new('RGBA', (width * psd.width, height * psd.height))
		for i, layer in enumerate(psd):
			row = 0
			column = 0
			if i != 0:
				column, row = divmod(i, width)
			box = (
				row * psd.width,
				column * psd.height,
				(row + 1) * psd.width,
				(column + 1) * psd.height,
			)
			new_image.paste(layer.composite(), box=box)
		new_image.save(png_path)
	else:
		png = standardize_alpha(psd)
		png.save(png_path)

def standardize_alpha(psd_image: PSDImage) -> Image:
	image = psd_image.composite()
	width, height = image.size
	for x in range(width):
		for y in range(height):
			r, g, b, a = image.getpixel((x,y))
			if a == 0:
				image.putpixel((x,y), (0, 0, 0, 0))

	return image

def nearest_square(number: int) -> int:
	sqrt = math.sqrt(number)
	return math.ceil(sqrt)

if __name__ == '__main__':
	main() # pylint: disable=no-value-for-parameter
