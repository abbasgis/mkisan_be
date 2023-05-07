import os
from io import BytesIO
import numpy as np
from PIL import Image
from rio_tiler.io import COGReader
from rio_tiler.colormap import cmap

from api.logger.utils import DataLogger
from api.utils import CommonUtils
from map_viewer.raster_utils.rio_raster import RioRaster
# from da_utils.raster.s3 import S3Utils
from mkisan_be.settings import MEDIA_ROOT
from rio_cogeo import cog_profiles, cog_translate


class COGRaster:
    cog: COGReader
    file_path: str

    # def __init__(self, uuid: str, is_s3: bool = True):
    #     pass

    @classmethod
    def open_from_local(cls, file_path: str):
        cog_raster = cls()
        cog_raster.cog = COGReader(file_path)
        cog_raster.file_path = file_path
        return cog_raster

    # @classmethod
    # def open_from_s3(cls, file_name: str):
    #     cog_raster = cls()
    #     s3_uri = S3Utils.get_cog_uri(f"{file_name}.tif")
    #     cog_raster.cog = S3Utils().get_cog_rio_dataset(s3_uri)
    #     cog_raster.file_path = s3_uri
    #     return cog_raster

    def get_file_path(self):
        return self.file_path

    def get_rio_raster(self):
        return RioRaster(self.cog.dataset)

    @classmethod
    def create_cog(cls, src_rio_raster: RioRaster, des_path: str,
                   profile: str = "deflate",
                   profile_options: dict = {},
                   **options):
        CommonUtils.make_dirs(des_path)
        with src_rio_raster.get_dataset() as src:
            """Convert image to COG."""
            # Format creation option (see gdalwarp `-co` option)
            # profile = 'DEFLATE'  # ycbcr
            output_profile = cog_profiles.get(profile)
            output_profile.update(dict(BIGTIFF="IF_SAFER"))
            output_profile.update(profile_options)

            # Dataset Open option (see gdalwarp `-oo` option)
            config = dict(
                GDAL_NUM_THREADS="ALL_CPUS",
                GDAL_TIFF_INTERNAL_MASK=True,
                GDAL_TIFF_OVR_BLOCKSIZE="128",
            )

            cog_translate(
                src,
                des_path,
                output_profile,
                overview_level=3,
                config=config,
                in_memory=False,
                quiet=True,
                **options,
            )
            print("cog created")
            return cls.open_from_local(des_path)

    @staticmethod
    def create_color_map(style):
        # min_val = style['min']
        # max_val = style['max']
        palette = style['palette']
        custom_color = {}
        for i in range(len(palette)):
            h = f"{palette[i]}FF".lstrip('#')
            custom_color[i] = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
        # print("custom color", custom_color)
        cp = cmap.register({"cc": custom_color})
        return cp.get("cc")

    @staticmethod
    def create_custom_color_map(style):
        min_val = style['min']
        max_val = style['max']
        interval = (max_val - min_val) / 3
        # Define the custom colormap
        # custom_cmap = {
        #     min_val: (0, 128, 0, 255),  # green
        #     int(min_val + (interval * 1)): (0, 128, 0, 255),  # green
        #     int(min_val + (interval * 1) + 1): (255, 255, 0, 255),  # yellow
        #     int(min_val + (interval * 2)): (255, 255, 0, 255),  # yellow
        #     int(min_val + (interval * 2) + 1): (255, 0, 0, 255),  # red
        #     max_val: (255, 0, 0, 255)  # red
        # }
        custom_cmap = [
            ((0, 12), (0, 0, 0, 0)),
            ((int(min_val + (interval * 1)), int(min_val + (interval * 2))), (255, 255, 255, 255)),
            ((int(min_val + (interval * 2)), int(min_val + (interval * 3))), (255, 0, 0, 255)),
            ((int(min_val + (interval * 3)), max_val), (255, 255, 0, 255)),
        ]
        # Define the minimum and maximum pixel values to map to colors
        vmin_vmax = (min_val, max_val)
        # Get the colormap dictionary
        # graduated_colormap = cmap(custom_cmap)
        cp = cmap.register({"graduated_colormap": custom_cmap})
        return cp.get("graduated_colormap")

    def read_tile_as_png(self, x: int, y: int, z: int, color_map: dict, tile_size=256):
        try:
            tile = self.cog.tile(x, y, z, tilesize=tile_size)
            # tile.rescale(
            #     in_range=((0, 25),),
            #     out_range=((0, 255),)
            # )
            return BytesIO(tile.render(True, colormap=color_map, img_format='PNG'))
        except Exception as e:
            # DataLogger.log_error_message(e)
            # return self.create_empty_image(tile_size, tile_size)
            pass

    @staticmethod
    def create_alpha_band(size_x, size_y):
        return np.zeros([size_x, size_y], dtype=np.uint8)

    def create_empty_image(self, size_x, size_y):
        blank_image = np.zeros([size_x, size_y, 4], dtype=np.uint8)
        # np_array.fill(255)  # or img[:] = 255
        # blank_image[:, :, 3] = 0
        return self.create_image(blank_image)

    @staticmethod
    def create_image(np_array, format="PNG", f_name=None, is_data_file=False):
        img = Image.fromarray(np_array)
        if f_name and is_data_file:
            fp = os.path.join(MEDIA_ROOT, f_name)
            CommonUtils.make_dirs(fp)
            # img.save(fp, format)

        buffer = BytesIO()
        img.save(buffer, format=format)  # Enregistre l'image dans le buffer
        # return "data:image/PNG;base64," + base64.b64encode(buffer.getvalue()).decode()
        return buffer  # .getvalue()

    def get_pixel_value_at_long_lat(self, long: float, lat: float):
        try:
            pt = self.cog.point(long, lat)
            obj = {}
            for ii, b in enumerate(pt.band_names):
                obj[b] = str(pt.data[ii])
            print("RGB-Nir values:")
            print([(b, pt.data[ii]) for ii, b in enumerate(pt.band_names)])
            # print("NDVI values:")
            # ndvi = pt.apply_expression("(b4-b1)/(b4+b1)")
            # print([(b, ndvi.data[ii]) for ii, b in enumerate(ndvi.band_names)])
            # return pt
            return obj
        except Exception as e:
            # DataLogger.log_error_message(e)
            pass

    def get_raster_value_from_geojson(self, geojson):
        try:
            feature = geojson['features'][0]
            img = self.cog.feature(feature, dst_crs=self.cog.crs, max_size=1024)
            obj = img.statistics()
            return obj
        except Exception as e:
            # DataLogger.log_error_message(e)
            pass
