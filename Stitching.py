# -*-coding:utf-8-*-

# import gdal
import glob
from math import ceil
import numpy as np
from osgeo import gdal, osr
from os import remove
import time

def get_extent(fn):
    ds = gdal.Open(fn)
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    # 获取图像角点坐标
    gt = ds.GetGeoTransform()
    minx = gt[0]
    maxy = gt[3]
    maxx = gt[0] + gt[1] * rows
    miny = gt[3] + gt[5] * cols
    return (minx, maxy, maxx, miny,gt[1])

def imagexy2geo(dataset, row, col):
    '''
    根据GDAL的六参数模型将影像图上坐标（行列号）转为投影坐标或地理坐标（根据具体数据的坐标系统转换）
    :param dataset: GDAL地理数据
    :param row: 像素的行号
    :param col: 像素的列号
    :return: 行列号(row, col)对应的投影坐标或地理坐标(x, y)
    '''
    trans = dataset.GetGeoTransform()
    px = trans[0] + col * trans[1] + row * trans[2]
    py = trans[3] + col * trans[4] + row * trans[5]
    return px, py

def geo2imagexy(dataset, x, y):
    '''
    根据GDAL的六 参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
    :param dataset: GDAL地理数据
    :param x: 投影或地理坐标x
    :param y: 投影或地理坐标y
    :return: 影坐标或地理坐标(x, y)对应的影像图上行列号(row, col)
    '''
    trans = dataset.GetGeoTransform()
    a = np.array([[trans[1], trans[2]], [trans[4], trans[5]]])
    b = np.array([x - trans[0], y - trans[3]])
    return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解

if __name__ == '__main__':

    epsg = 5186
    # epsg = 4490
    # epsg = 3415
    tiff_path = './geotiff/*.tif'
    temp_path = 'mosaic_temp.tif'
    dst_path = 'mosaic_1104.tif'

    start_time = time.time()
    # os.chdir('D:\MODIS-data')
    in_files = glob.glob(tiff_path)
    in_files = sorted(in_files)
    print(in_files)
    # print(in_files)
    # exit(0)
    # 通过两两比较大小,将最终符合条件的四个角点坐标保存，
    # 即为拼接图像的四个角点坐标
    minX, maxY, maxX, minY,minGt1 = get_extent(in_files[0])
    for fn in in_files[1:]:
        minx, maxy, maxx, miny,mingt1 = get_extent(fn)
        minX = min(minX, minx)
        maxY = max(maxY, maxy)
        maxX = max(maxX, maxx)
        minY = min(minY, miny)
        minGt1 = min(minGt1,mingt1)
        # print(mingt1)
    # print(maxY,maxy,minY,maxX,minX)
    # 获取输出图像的行列数
    in_ds = gdal.Open(in_files[0])
    gt = in_ds.GetGeoTransform()
    print("gt:",gt)
    # rows = ceil((maxX - minX) / abs(gt[5]))
    # cols = ceil((maxY - minY) / gt[1])
    # print(minGt1)
    # rows = ceil((maxX - minX) / minGt1)
    # cols = ceil((maxY - minY) / minGt1)
    #
    # print(rows)
    # print(cols)

    rows = 0
    cols = 0

    ### get rows and cols

    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(temp_path, 1, 1, 4, gdal.GDT_Byte)
    gt = list(in_ds.GetGeoTransform())
    gt[0], gt[3] = minX, maxY
    out_ds.SetGeoTransform(gt)

    for fn in in_files:
        in_ds_t = gdal.Open(fn)
        trans = gdal.Transformer(in_ds_t, out_ds, [])
        success, xyz = trans.TransformPoint(False, 0, 0)
        x, y, z = map(int, xyz)
        print("xy:",x,y)
        x_size = in_ds_t.RasterXSize
        y_size = in_ds_t.RasterYSize
        if x + x_size > cols:
            cols = x+x_size
        if y + y_size > rows:
            rows = y + y_size
    #delete
    remove(temp_path)
    print(rows,cols)

    # exit(0)

    # 创建输出图像
    ###
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(dst_path, cols, rows, 4, gdal.GDT_Byte)

    out_ds.SetProjection(in_ds.GetProjection())
    # print(in_ds.GetProjection())

    # in_ds = gdal.Open(in_files[0])
    # gt = in_ds.GetGeoTransform()
    # print("gt:", gt)
    gt = list(in_ds.GetGeoTransform())
    print(minX,minY,maxX,maxY)
    gt[0], gt[3] = minX, maxY
    ### ???
    print(gt)
    out_ds.SetGeoTransform(gt)


    # srs = osr.SpatialReference()  # establish encoding
    # srs.ImportFromEPSG(epsg)
    # out_ds.SetProjection(srs.ExportToWkt())

    for fn in in_files:
        in_ds = gdal.Open(fn)
        trans = gdal.Transformer(in_ds, out_ds, [])
        print("trans:",trans)
        success, xyz = trans.TransformPoint(False, 0, 0)
        print("xyz:",xyz)
        x, y, z = map(int, xyz)
        print("xy:",x,y)
        # px,py = imagexy2geo(in_ds, 0, 0)
        # print("px,py:",px," - ",py)
        # tr,tc = geo2imagexy(out_ds, px, py)
        # print("tr,tc:", tr, " - ", tc)
        for k in range(1,5):
            data = in_ds.GetRasterBand(k).ReadAsArray()

            out_band = out_ds.GetRasterBand(k)
            org_band = out_band.ReadAsArray()
            org_band = org_band[y:data.shape[0] + y, x:data.shape[1] + x]

            d_shape = data.shape
            o_shape = org_band.shape
            # print(d_shape)
            if d_shape[0] > o_shape[0]:
                data = data[:o_shape[0],:]
            if d_shape[1] > o_shape[1]:
                data = data[:,:o_shape[1]]

            # print(data.shape)
            data[data < 1] = org_band[data < 1]
            # print(data)
            # print(data.shape)
            out_band.WriteArray(data, x, y)
        # break
        # if i == 1:
        #     continue

        # print(org_band.shape)
        #
        # print(data1.shape)
        # print(data1[data1 > 0].shape)
        # print(data1[data1>0])
        #
        # out_band2.WriteArray(data2, y, x)
        # out_band3.WriteArray(data3, y, x)
        # out_band4.WriteArray(data4, y, x)
        # # if i == 3:
        # #     break
        # print("success:",success)

    out_ds.FlushCache()  # write to disk
    out_ds = None
    del in_ds, out_band,out_ds

    end_time = time.time()
    print("cost time(s):",end_time-start_time)