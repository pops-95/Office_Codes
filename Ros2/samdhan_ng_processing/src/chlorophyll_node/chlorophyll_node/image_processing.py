#!/usr/bin/env python3

import cv2
import numpy as np
import math
import datetime
from shutil import copyfile
from numpy import uint8
import warnings
from pathlib import Path

thresHLow, thresSLow, thresILow = 0.0, 0.0, 0.0   #from file
thresHHigh, thresSHigh, thresIHigh = 0.0, 0.0, 0.0   #from file
row, col = 0, 0
top_border, left_border, bottom_border, right_border = 0, 0, 0, 0   #from file
thresh_dist = 1000.0
min_Object_area_cut,max_Object_area_cut = 0,0
min_Object_area_cut_tillering,max_Object_area_cut_tillering = 0,0 #from file
lowTillering_thresLow, lowTillering_thresHigh,mediumTillering_thresLow, mediumTillering_thresHigh,highTillering_thresLow, highTillering_thresHigh = 0,0,0,0,0,0 #from file
dumpSave = 1
 
def read_params(parentPath):
        try:        
                cdir = parentPath
                global thresHLow, thresSLow, thresILow
                f = open(cdir + "/param_threshold1.bin", "r")
                if f.mode == 'r':
                        data = f.readlines()  # read the text file
                i = 0
                for line in data:
                    if i == 0:
                        thresHLow, thresSLow, thresILow = np.array(
                            line.replace('\n', '').split('\t'), dtype=np.float32)
                    i = i + 1
                f.close()

                global thresHHigh, thresSHigh, thresIHigh
                f = open(cdir + "/param_threshold2.bin", "r")
                if f.mode == 'r':
                        data = f.readlines()  # read the text file
                i = 0
                for line in data:
                    if i == 0:
                        thresHHigh, thresSHigh, thresIHigh = np.array(
                            line.replace('\n', '').split('\t'), dtype=np.float32)
                    i = i + 1
                f.close()
                
                global thresh_dist
                f = open(cdir + "/param_thresdist.bin", "r")
                if f.mode == 'r':
                        data = f.readlines()  # read the text file
                i = 0
                for line in data:
                    if i == 0:
                        thresh_dist = np.array(
                            line.replace('\n', '').split('\t'), dtype=np.float32)
                    i = i + 1
                f.close()
                
                linecount=0
                f = open(cdir + "/pallete.txt", "r")
                if f.mode == 'r':
                        data = f.readlines()  # read the text file
                for line in data:
                        linecount = linecount + 1
                f.close() 

                global color_pallete_avg_R,color_pallete_avg_G,color_pallete_avg_B
                color_pallete_avg_R=np.empty(linecount,dtype=float)
                color_pallete_avg_G=np.empty(linecount,dtype=float)
                color_pallete_avg_B=np.empty(linecount,dtype=float)

                f = open(cdir + "/pallete.txt", "r")
                if f.mode == 'r':
                        data = f.readlines()  # read the text file
                i = 0
                for line in data:
                        color_pallete_avg_R[i], color_pallete_avg_G[i], color_pallete_avg_B[i] = np.array(
                                line.replace('\n', '').split('\t'), dtype=float)
                        i = i + 1
                f.close()

                global min_Object_area_cut,max_Object_area_cut
                f = open(cdir + "/param_areacutoff.bin", "r")
                if f.mode == 'r':
                        data = f.readlines()  # read the text file
                i = 0
                for line in data:
                    if i == 0:
                        min_Object_area_cut,max_Object_area_cut = np.array(
                            line.replace('\n', '').split('\t'), dtype=np.float32)
                    i = i + 1
                f.close()
                
                global min_Object_area_cut_tillering,max_Object_area_cut_tillering
                f = open(cdir + "/param_areacutoff_tillering.bin", "r")
                if f.mode == 'r':
                        data = f.readlines()  # read the text file
                i = 0
                for line in data:
                    if i == 0:
                        min_Object_area_cut_tillering,max_Object_area_cut_tillering = np.array(
                            line.replace('\n', '').split('\t'), dtype=np.float32)
                    i = i + 1
                f.close()

                global lowTillering_thresLow, lowTillering_thresHigh,mediumTillering_thresLow, mediumTillering_thresHigh,highTillering_thresLow, highTillering_thresHigh
                f = open(cdir + "/param_tillering.bin", "r")
                if f.mode == 'r':
                        data = f.readlines()  # read the text file
                i = 0
                for line in data:
                    if i == 0:
                      lowTillering_thresLow,lowTillering_thresHigh,mediumTillering_thresLow,mediumTillering_thresHigh, highTillering_thresLow, highTillering_thresHigh = np.array(line.replace('\n', '').split('\t'), dtype=np.float32)
                      i = i + 1
                f.close()

                 
                return True
        except Exception as e:
                print (e)
                return False
def objectCount(output):
    if(output==0):
            return output
    global min_Object_area_cut,max_Object_area_cut
    obj_count = 0
    sizes = output[2][0:, 4]
    for i in range(1, output[0]):
        #print(sizes[i])
        if sizes[i] >= min_Object_area_cut and sizes[i] <= max_Object_area_cut:
            obj_count = obj_count + 1

    return obj_count

def estimateTillering(output):
    if(output==0):
            return output
    global min_Object_area_cut_tillering,max_Object_area_cut_tillering
    obj_count = 0
    area_temp = 0
    sizes = output[2][0:, 4]
    for i in range(1, output[0]):
        #print(sizes[i])
        if sizes[i] >= min_Object_area_cut_tillering and sizes[i] <= max_Object_area_cut_tillering:
            obj_count = obj_count + 1
            area_temp = area_temp + sizes[i]

        
    if(obj_count > 0):
        if area_temp/obj_count >= lowTillering_thresLow and area_temp/obj_count <= lowTillering_thresHigh:
                return "Low Tillering"
        elif area_temp/obj_count >= mediumTillering_thresLow and area_temp/obj_count <= mediumTillering_thresHigh:
                return "Medium Tillering"
        elif area_temp/obj_count >= highTillering_thresLow and area_temp/obj_count <= highTillering_thresHigh:
                return "High Tillering"
        else:
                return "NA"
    else:
        return "NA"           
        


def analysis(path, node, config_path, output_path=None):
        global thresH, thresS, thresI
        global color_pallete_avg_R,color_pallete_avg_G,color_pallete_avg_B
        global thresh_dist

        config_path = Path(config_path)
        output_path = Path(output_path) if output_path else config_path
        output_path.mkdir(parents=True, exist_ok=True)
        dump_path = output_path / "dump"
        if dumpSave == 1:
                dump_path.mkdir(parents=True, exist_ok=True)

        img = cv2.imread(path)
        if img is None:
               return "Image Read Error Occurred"
        
        if(not read_params(str(config_path))):
               #print("File not Found");
               return "File Read Error Occurred"
        
        output_image = output_path / "output.jpg"
        cv2.imwrite(str(output_image),img)
        if dumpSave==1:
                timestr=dump_path / ("img_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
                copyfile(str(output_image), str(timestr)+".jpg")

        imgWidth=320
        imgHeight=240
        img = cv2.resize(img, (imgWidth, imgHeight))
                        
        if node=="ChlorophyllNode":
                str1=""
                img =  ImageEnhance_Enhance(img, 0, 0, 0, 0)
                img =  ImageOps_Segment(img,thresHLow, thresSLow, thresILow,thresHHigh, thresSHigh, thresIHigh)
                avg_R,avg_G,avg_B =  ImageMath_Eval_Mean(img)
                with open(output_path / "chloro.txt", 'w') as f:
                        f.write(str(avg_R)+"\t"+str(avg_G)+"\t"+str(avg_B))
                        f.close()
                linecount = len(color_pallete_avg_R)
                min_distance=999999
                matched_index=-1
                for i in range(0,linecount):
                        a = (avg_R,avg_G,avg_B)
                        b = (color_pallete_avg_R[i], color_pallete_avg_G[i], color_pallete_avg_B[i])
                        dist = math.sqrt(((avg_R-color_pallete_avg_R[i])*(avg_R-color_pallete_avg_R[i]))\
                                         +((avg_G-color_pallete_avg_G[i])*(avg_G-color_pallete_avg_G[i]))\
                                         +((avg_B-color_pallete_avg_B[i])*(avg_B-color_pallete_avg_B[i])))
                        if dist < min_distance:
                            min_distance = dist
                            matched_index = i+1 
                if min_distance < thresh_dist:
                        str1 = str1 + "Index "+str(matched_index)
                else:
                        str1="No Match"                
                return str1
        
        if node=="SeedlingNode":
                img =  ImageEnhance_Enhance(img, 0, 0, 0, 0)
                img =  ImageOps_Segment(img,thresHLow, thresSLow, thresILow,thresHHigh, thresSHigh, thresIHigh)
                output =  ImageMorph_MorphOp(img,str(output_path))
                obj_count = objectCount(output)
                return obj_count
        
        if node=="TilleringNode":
                img =  ImageEnhance_Enhance(img, 0, 0, 0, 0)
                img =  ImageOps_Segment(img,thresHLow, thresSLow, thresILow,thresHHigh, thresSHigh, thresIHigh)  
                output =  ImageMorph_MorphOp(img,str(output_path))
                result = estimateTillering(output)
                return result
        


def ImageOps_SegmentRGB(img, thresR, thresG, thresB, threshInv="", check=0):
    try:
        arrRGB = np.array(img)
        #arrRGB = np.array(np.asarray(cv2.cvtColor(img, cv2.COLOR_BGR2HSV)))

        thresholdRGB = [thresR, thresG, thresB]

        if threshInv=="THRESH_INV":
            if check==4444:
                cv2.imwrite("thres_prev_inv.jpg",arrRGB)
            valid_RGB_range = np.logical_and(thresR <= arrRGB[:, :, 0], thresG <= arrRGB[:, :, 1], thresB <= arrRGB[:, :, 2])
            arrRGB[valid_RGB_range] = 0
            if check==4444:
                cv2.imwrite("thres_after_inv.jpg",arrRGB)
        else:
            if check==4444:
                cv2.imwrite("thres_prev.jpg",arrRGB)
            valid_RGB_range = np.logical_and(thresR <= arrRGB[:, :, 0], thresG <= arrRGB[:, :, 1], thresB <= arrRGB[:, :, 2])
            arrRGB[valid_RGB_range] = 0
            if check==4444:
                cv2.imwrite("thres_after.jpg",arrRGB)
        return arrRGB
    except:
        #print("ERROR: Could not find a version that satisfies the requirement\nERROR: No matching distribution found")
        return 0

def ImageOps_Segment1(img, thresR, thresG, thresB, threshInv="", check=0):
    try:
        arrRGB = np.array(img)
        if threshInv=="THRESH_INV":
            if check==4444:
                cv2.imwrite("thres_prev_inv.jpg",arrRGB)
        else:
            if check==4444:
                cv2.imwrite("thres_prev.jpg",arrRGB)
        arrRGB = np.array(np.asarray(cv2.cvtColor(img, cv2.COLOR_BGR2HSV)))

        thresholdRGB = [thresR, thresG, thresB]

        if threshInv=="THRESH_INV":
            valid_RGB_range = np.logical_and(arrRGB[:, :, 0] >= thresR, arrRGB[:, :, 1] >= thresG, arrRGB[:, :, 2] >= thresB)
            arrRGB[np.logical_not(valid_RGB_range)] = 0
            arrRGB = np.array(np.asarray(cv2.cvtColor(arrRGB, cv2.COLOR_HSV2BGR)))
            if check==4444:
                cv2.imwrite("thres_after_inv.jpg",arrRGB)
        else:
            valid_RGB_range = np.logical_and(arrRGB[:, :, 0] <= thresR, arrRGB[:, :, 1] <= thresG, arrRGB[:, :, 2] <= thresB)
            arrRGB[np.logical_not(valid_RGB_range)] = 0
            arrRGB = np.array(np.asarray(cv2.cvtColor(arrRGB, cv2.COLOR_HSV2BGR)))

            if check==4444:
                cv2.imwrite("thres_after.jpg",arrRGB)
            
        return arrRGB
    except:
        #print("ERROR: Could not find a version that satisfies the requirement\nERROR: No matching distribution found")
        return 0
    
def ImageOps_Segment(img, thresR, thresG, thresB,thresR1, thresG1, thresB1, check=0):
    try:
        arrRGB_org = np.array(img)
        if check==4444:
            cv2.imwrite("thres_prev.jpg",arrRGB_org)
        arrRGB = np.array(np.asarray(cv2.cvtColor(img, cv2.COLOR_BGR2LAB)))
        S_range = np.logical_and(arrRGB[:, :, 1]>=thresG, arrRGB[:, :, 1] <= thresG1)
        arrRGB_org[(S_range)] = 0
        if check==4444:
         cv2.imwrite("thres_after_1.jpg",arrRGB_org)
        
        I_range = np.logical_and(arrRGB[:, :, 0]>=thresR, arrRGB[:, :, 0] <= thresR1)
        arrRGB_org[(I_range)] = 0

        if check==4444:
         cv2.imwrite("thres_after_2.jpg",arrRGB_org)
        #print("T111111111111")
	#print("T222222222222")	
        return arrRGB_org
    except Exception  as e:
        print(e)
        print("ERROR: Could not find a version that satisfies the requirement\nERROR: No matching distribution found")
        return 0

def impro_connectedComponents(img):
    try:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = img.astype('uint8')
        _, img = cv2.threshold(img,0,255,cv2.THRESH_BINARY|cv2.THRESH_OTSU)
        # You need to choose 4 or 8 for connectivity type
        connectivity = 4  
        # Perform the operation
        output = cv2.connectedComponentsWithStats(img, connectivity, cv2.CV_32S)
        
        # Get the results
        
        # The first cell is the number of labels
        no_of_objects = output[0]
        
        # The second cell is the label matrix
        # Labels is a matrix the size of the input image where each element has a value equal to its label
        labels = output[1]
        object_stats = output[2]
            
        #only to show the result of connected component

        '''
        label_hue = np.uint8(179 * labels / np.max(labels))
        blank_ch = 255 * np.ones_like(label_hue)
        labeled_img = cv2.merge([label_hue, blank_ch, blank_ch])
        labeled_img = cv2.cvtColor(labeled_img, cv2.COLOR_HSV2BGR)
        labeled_img[label_hue == 0] = 0
        '''
             
        return labels,output
    except:
        #print("ERROR: Could not find a version that satisfies the requirement\nERROR: No matching distribution found")
        return 0,0

def ImageMath_Eval_Mean(fwbgr):   
    try:
        avg_R=0.0
        avg_G=0.0
        avg_B=0.0
        '''
        pixcount=0
        row, col, _ = fwbgr.shape
        for m in range(0,row-1):
            for n in range(0,col-1): 
                if (int(fwbgr[m][n][2])+int(fwbgr[m][n][1])+int(fwbgr[m][n][0]))/3 > 0:
                    avg_R += fwbgr[m][n][2]
                    avg_G += fwbgr[m][n][1]
                    avg_B += fwbgr[m][n][0]
                    pixcount = pixcount+1
        if pixcount > 0:
            avg_R = avg_R/pixcount
            avg_G = avg_G/pixcount
            avg_B = avg_B/pixcount
        print(avg_R,avg_G,avg_B)
        cv2.imwrite('aa.jpg',fwbgr)
        '''
        #print(111111)
        fwbgr = np.array(np.asarray(fwbgr),dtype=float)
        fwbgr[(fwbgr[:, :, 0]+fwbgr[:, :, 1]+fwbgr[:, :, 2])==0] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            avg_color_per_row = np.nanmean(fwbgr, axis=0)
            avg_color = np.nanmean(avg_color_per_row, axis=0)
            #print(3333333)
            avg_R =  avg_color[2] if not np.isnan(avg_color[2]) else 0
            avg_G =  avg_color[1] if not np.isnan(avg_color[1]) else 0
            avg_B =  avg_color[0] if not np.isnan(avg_color[0]) else 0

        #print(2222222)
        #print(avg_R,avg_G,avg_B)
        '''
        if(not init_Func()):
            avg_R =  0
            avg_G =  0
            avg_B =  0
        '''
        #print(333333)
        #print(avg_R,avg_G,avg_B)
        return (avg_R,avg_G,avg_B)
    except Exception as e:
        #print(e) 
        #print("ERROR: Could not find a version that satisfies the requirement\nERROR: No matching distribution found")
        return 0,0,0

def impro_objectCount(img,output,min_Object_area_cut,max_Object_area_cut):
    try:
        obj_count = 0
        sizes = output[2][0:, 4]

        for i in range(1, output[0]):
            if sizes[i] >= min_Object_area_cut and sizes[i] <= max_Object_area_cut:
                obj_count = obj_count + 1;
            
        return obj_count
    except:
        #print("ERROR: Could not find a version that satisfies the requirement\nERROR: No matching distribution found")
        return 0

def ImageEnhance_Enhance(img,top_border,bottom_border,left_border,right_border):
    try:
        #imgWidth=320
        #imgHeight=240
        #img = cv2.resize(img, (imgWidth, imgHeight))
        row, col, _ = img.shape
        fwbgr = img[top_border:row - bottom_border, left_border:col - right_border]

        return fwbgr
    except:
        #print("ERROR: Could not find a version that satisfies the requirement\nERROR: No matching distribution found")
        return 0

def ImageMorph_MorphOp(img,parentPath):
    try:
            
        cdir = parentPath
        label,output = impro_connectedComponents(img)
             
        #obj_count = impro_objectCount(img,output,min_Object_area_cut,max_Object_area_cut)
       
        return output
    except:
        #print("ERROR: Could not find a version that satisfies the requirement\nERROR: No matching distribution found")
        return 0
