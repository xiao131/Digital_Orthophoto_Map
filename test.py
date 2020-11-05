import os
import time
from PIL import Image
import RPY_OPK

def GPSWeek2UTC(gpsweek,gpsseconds,leapseconds):
    import datetime
    datetimeformat = "%Y-%m-%d %H:%M:%S"
    epoch = datetime.datetime.strptime("1980-01-06 00:00:00",datetimeformat)
    # print(epoch)
    elapsed = datetime.timedelta(days=(gpsweek*7),seconds=(gpsseconds+leapseconds))

    formate_time = datetime.datetime.strftime(epoch + elapsed,datetimeformat)
    # print(formate_time)
    formate_time = time.strptime(formate_time,datetimeformat)
    formate_time = time.mktime(formate_time)
    return int(formate_time) + 28800

def getExif(path):
    src_image = Image.open(path)
    info = src_image._getexif()

    # Focal Length (jiao ju)
    focalLength = info[37386]
    print(info)
    # print(focalLength)
    # focal_length = focalLength[0] / focalLength[1] # unit: mm
    focal_length = focalLength
    focal_length = focal_length * pow(10, -3) # unit: m

    # Orientation
    try:
        orientation = info[274]
    except:
        orientation = 0

    return focal_length, orientation,info[36867]

def GetAtt(log_path,att_path):
    ###########
    f = open(log_path, "r")
    att_file = open(att_path, "a+")
    for t in f.readlines():
        if t.startswith("GPS,"):
            att_file.write(t)
            # c = 1
        elif t.startswith("ATT,"):
            att_file.write(t)
            # att = t.split(",")
            # print(att)
            # roll = float(att[3])
            # pitch = float(att[5])
            # yaw = float(att[7])
            # print(RPY_OPK.hrp2opk(roll,pitch,yaw))
            # break
    f.close()
    att_file.close()

def GetImg2Att(root_path,att_path,leapseconds = 27):
    for root, dirs, files in os.walk(root_path):  # get path
        for file in files:
            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.JPG' or extension == '.jpg':
                print('Read the image - ' + file)
                img_time = int(os.path.getmtime(file_path)) - 28800

                att_all = open(att_path, "r")
                rpy = None
                while True:
                    # for att in att_all.readlines():
                    att = att_all.readline()
                    if att.startswith("GPS,"):
                        gps = att.split(",")
                        if img_time == GPSWeek2UTC(int(gps[4]), float(gps[3]) / 1000, leapseconds):
                            # print(img_time)
                            # print(GPSWeek2UTC(int(gps[4]), float(gps[3])/1000, leapseconds))
                            if rpy == None:
                                rpy = att_all.readline()
                            if rpy.startswith("ATT,"):
                                rpy = rpy.split(",")
                                # omega, phi, kappa = RPY_OPK.hrp2opk(float(rpy[3]), float(rpy[5]), float(rpy[7]))
                                omega, phi, kappa = RPY_OPK.hrp2opk(0, 0, float(rpy[7]))
                                att_result = file + "\t" + gps[8] + "\t" + gps[7] + "\t" + gps[9] + "\t" \
                                             + str(omega) + "\t" + str(phi) + "\t" + str(kappa)

                                f = open(root + "/" + filename + ".txt", "w+")
                                f.write(att_result)
                                f.close()
                                print(att_result)
                                # print(att)
                                # print(att_all.readline())
                                break
                    rpy = att
                att_all.close()

if __name__ == '__main__':
    log_path = "./img/00000057.log"
    att_path = "./img/att.txt"
    GetAtt(log_path, att_path)

    # print(GPSWeek2UTC(2129, 528049, 27))

    root_path = "./img"
    leapseconds = 27


    for root, dirs, files in os.walk(root_path):  # get path
        for file in files:
            filename = os.path.splitext(file)[0]
            extension = os.path.splitext(file)[1]
            file_path = root + '/' + file

            if extension == '.JPG' or extension == '.jpg':
                # print(filename)
                temp_time = filename.split("-")
                # print(temp_time)
                img_time = "2020-11-04 "+str(temp_time[0])+":"+str(temp_time[1])+":"+str(temp_time[2])
                img_time = int(time.mktime(time.strptime(img_time,"%Y-%m-%d %H:%M:%S")))
                print(img_time)
                # exit(0)
                print('Read the image - ' + file)
                # img_time = int(os.path.getmtime(file_path)) - 28800

                att_all = open(att_path, "r")
                rpy = None
                while True:
                    # for att in att_all.readlines():
                    att = att_all.readline()
                    if att.startswith("GPS,"):
                        gps = att.split(",")
                        if img_time == GPSWeek2UTC(int(gps[4]), float(gps[3]) / 1000, leapseconds):
                            # print(img_time)
                            # print(GPSWeek2UTC(int(gps[4]), float(gps[3])/1000, leapseconds))
                            if rpy == None:
                                rpy = att_all.readline()
                            if rpy.startswith("ATT,"):
                                rpy = rpy.split(",")
                                # omega, phi, kappa = RPY_OPK.hrp2opk(float(rpy[3]), float(rpy[5]), float(rpy[7]))
                                omega, phi, kappa = RPY_OPK.hrp2opk(0, 0, float(rpy[7]))
                                att_result = file + "\t" + gps[8] + "\t" + gps[7] + "\t" + gps[9] + "\t" \
                                             + str(omega) + "\t" + str(phi) + "\t" + str(kappa)

                                f = open(root + "/" + filename + ".txt", "w+")
                                f.write(att_result)
                                f.close()
                                print(att_result)
                                # print(att)
                                # print(att_all.readline())
                                break
                    rpy = att
                att_all.close()

    exit(0)
    ###Get ATT data
    log_path = "./TestData/00000037.log"
    att_path = "./TestData/att.txt"
    GetAtt(log_path,att_path)

    # print(GPSWeek2UTC(2129, 528049, 27))

    root_path = "./TestData"
    GetImg2Att(root_path, att_path, leapseconds=27)
