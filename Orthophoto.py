import os
import numpy as np
import cv2
import time
from module.ExifData import *
from module.EoData import readEO, geographic2plane, Rot3D
from module.Boundary import boundary
from module.BackprojectionResample import projectedCoord, backProjection, resample, createGeoTiff


if __name__ == '__main__':
    ground_height = 65  # unit: m
    sensor_width = 6.3  # unit: mm

    ground_height = 9.55  # unit: m
    ground_height = 2.44  # unit: m
    sensor_width = 11.0435  # unit: mm
    epsg = 3415
    epsg = 5186
    # epsg = 4490

    root_path = "./TestData"
    root_path = "./img"
    # root_path = "./Data"

    for root, dirs, files in os.walk(root_path): #get path
        for file in files:
            image_start_time = time.time()
            start_time = time.time()

            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.JPG' or extension == '.jpg':
                print('Read the image - ' + file)
                image = cv2.imread(file_path, -1) #get image and alpha channel

                # 1. Extract EXIF data from a image
                focal_length, orientation = getExif(file_path)  # unit: m, _
                print("focal_length:",focal_length)

                # 2. Restore the image based on orientation information
                restored_image = restoreOrientation(image, orientation)

                # 3. Convert pixel values into temperature

                image_rows = restored_image.shape[0]
                image_cols = restored_image.shape[1]

                pixel_size = sensor_width / image_cols  # unit: mm/px
                pixel_size = pixel_size / 1000  # unit: m/px

                end_time = time.time()
                print("--- %s seconds ---" % (time.time() - start_time))

                read_time = end_time - start_time

                ###################
                ###################
                ###################
                print('Read EOP - ' + filename + ".txt")
                print('Latitude | Longitude | Height | Omega | Phi | Kappa')
                file_path = root + '/' + filename + '.txt'
                eo = readEO(file_path)
                # convert to the correct area( can continue)
                eo = geographic2plane(eo, epsg)
                print("eo:",eo)

                # rot matrix
                R = Rot3D(eo)

                # 4. Extract a projected boundary of the image
                bbox = boundary(restored_image, eo, R, ground_height, pixel_size, focal_length)
                print("bbox:",bbox)
                # break
                print("--- %s seconds ---" % (time.time() - start_time))

                # 5. Compute GSD & Boundary size
                # GSD
                gsd = (pixel_size * (eo[2] - ground_height)) / focal_length  # unit: m/px
                print("gsd:",gsd)
                # break
                # Boundary size
                boundary_cols = int((bbox[1, 0] - bbox[0, 0]) / gsd)
                boundary_rows = int((bbox[3, 0] - bbox[2, 0]) / gsd)

                print(boundary_cols," ",boundary_rows)
                if boundary_rows > 10000 or boundary_cols > 10000:
                    continue
                # break

                # 6. Compute coordinates of the projected boundary
                print('projectedCoord')
                start_time = time.time()
                proj_coords = projectedCoord(bbox, boundary_rows, boundary_cols, gsd, eo, ground_height)
                print("--- %s seconds ---" % (time.time() - start_time))

                # Image size
                image_size = np.reshape(restored_image.shape[0:2], (2, 1))

                # 6. Back-projection into camera coordinate system
                print('backProjection')
                start_time = time.time()
                backProj_coords = backProjection(proj_coords, R, focal_length, pixel_size, image_size)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 7. Resample the pixels
                print('resample')
                start_time = time.time()
                b, g, r, a = resample(backProj_coords, boundary_rows, boundary_cols, image)
                print("--- %s seconds ---" % (time.time() - start_time))

                # 8. Create GeoTiff
                print('Save the image in GeoTiff')
                start_time = time.time()
                dst = './geotiff/' + filename
                createGeoTiff(b, g, r, a, bbox, gsd, boundary_rows, boundary_cols, dst,epsg)
                # break
                print("--- %s seconds ---" % (time.time() - start_time))

                print('*** Processing time per each image')
                print("--- %s seconds ---" % (time.time() - image_start_time + read_time))
            else:
                continue

