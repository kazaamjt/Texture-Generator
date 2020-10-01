import math
import sys
import shutil
from pathlib import Path
from typing import List

import click
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer

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

	base_layer = None
	layers: List[PixelLayer] = []
	for i, layer in enumerate(psd):
		if layer.visible:
			if base_layer is None:
				base_layer = layer.composite()
			elif "[md]" in layer.name:
				base_layer.paste(layer.composite(), box=None)
			else:
				layers.append(base_layer)
				base_layer = layer.composite()
	layers.append(base_layer)

	len_layers = len(layers)
	if len_layers == 1:
		png = layers[0]
	elif len_layers > 1:
		width = nearest_square(len_layers)
		height = width
		if len_layers <= width * (width - 1):
			height = width - 1

		png = Image.new('RGBA', (width * layers[0].width, height * layers[0].height))
		row = 0
		column = 0
		for i, layer in enumerate(layers):
			if i != 0:
				column, row = divmod(i, width)
			box = (
				row * psd.width,
				column * psd.height,
			)
			png.paste(layer.composite(), box=box)

	png = standardize_alpha(psd)
	png.save(png_path)

def standardize_alpha(psd_image: PSDImage) -> Image:
	image = psd_image.composite()
	width, height = image.size
	for x in range(width):
		for y in range(height):
			_, _, _, a = image.getpixel((x,y))
			if a == 0:
				image.putpixel((x,y), (0, 0, 0, 0))

	return image

def nearest_square(number: int) -> int:
	sqrt = math.sqrt(number)
	return math.ceil(sqrt)

if __name__ == '__main__':
	main() # pylint: disable=no-value-for-parameter
