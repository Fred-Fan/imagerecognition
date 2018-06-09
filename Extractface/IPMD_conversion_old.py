# import the necessary packages
from imutils import face_utils
import numpy as np
#import argparse
import imutils
import dlib
import cv2
import multiprocessing
from multiprocessing import Pool
import glob
import os
import pandas as pd
import re
import pickle

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")


def firstmodify(left, right, up, bottom, margin_perc):
    """
    This function is to make a square images based on the facemark + margin.

    Args:
        left(int): the left border of the image.
        right(int): the right border of the image.
        up(int): the bottom border of the image.
        bottom(int): the upper border of the image.
        margin_perc(int): the percentage, change it to control the margin width

    Returns:
        int: the new border of the image.

    """
    if (right-left)>=(bottom-up):
        margin = int((right-left)*margin_perc/100)
        diff = (right-left)-(bottom-up)
        if diff%2 == 0:
            left = int(left-margin)
            right = int(right+margin)
            up = int(up-margin-diff)
            bottom = int(bottom+margin)

        else:
            left = int(left-margin)
            right = int(right+margin)
            up = int(up-margin-diff)
            bottom = int(bottom+margin)
    else:
        margin = int((bottom-up)*margin_perc/100)
        diff = (bottom-up)-(right-left)
        if diff%2 == 0:
            left = int(left-margin-diff/2)
            right = int(right+margin+diff/2)
            up = int(up-margin)
            bottom = int(bottom+margin)
        else:
            left = int(left-margin-(diff/2+0.5))
            right = int(right+margin+(diff/2-0.5))
            up = int(up-margin)
            bottom = int(bottom+margin)

    return left, right, up, bottom


def ifoverborder(left, right, up, bottom, width, height):
    """
    This function is to modify the image to match the originial border if it in firstmodify exceeds the originial border.

    Args:
        left(int): the left border of the image.
        right(int): the right border of the image.
        up(int): the bottom border of the image.
        bottom(int): the upper border of the image.
        width(int): the right border of the original image.
        height(int): the upper border of the original image.

    Returns:
        int: the new border of the image.

    """
    if left < 0:
        right = right + (0-left)
        left = 0
        if right > width:
            right = width
    if right > width:
        left = left - (right-width)
        right = width
        if left < 0:
            left = 0
    if up < 0:
        bottom = bottom + (0-up)
        up = 0
        if bottom > height:
            bottom = height
    if bottom > height:
        up = up - (bottom - height)
        bottom = height
        if up < 0:
            up = 0
    #print(left, right, up, bottom, width, height)
    return left, right, up, bottom

def finalmodify(left, right, up, bottom):
    """
    This function is to resize the image to square if it is modified according to the original border.

    Args:
        left(int): the left border of the image.
        right(int): the right border of the image.
        up(int): the bottom border of the image.
        bottom(int): the upper border of the image.

    Returns:
        int: the new border of the image.

    """
    if right - left > bottom - up:
        diff = (right-left)-(bottom-up)
        if diff%2 == 0:
            left = int(left+diff/2)
            right = int(right-diff/2)
        else:
            left = int(left+(diff/2+0.5))
            right = int(right-(diff/2+0.5))
        # if diff%2 == 0:
            # up = int(up+diff/2)
            # bottom = int(bottom-diff/2)
        #else:
            #up = int(up+(diff/2-0.5))
            #bottom = int(bottom-(diff/2-0.5))
    else:
        diff = (bottom-up)-(right-left)
        #if diff%2 == 0:
            #left = int(left+diff/2)
            #right = int(right-diff/2)
        #else:
            #left = int(left+(diff/2+0.5))
            #right = int(right-(diff/2+0.5))
        if diff%2 == 0:
            up = int(up+diff/2)
            bottom = int(bottom-diff/2)
        else:
            up = int(up+(diff/2-0.5))
            bottom = int(bottom-(diff/2-0.5))
    return left, right, up, bottom


def conversion(f, return_rectangle = False):
    """
    This function is to extract the front face.

    Args:
        f(str): path name of the image.

    Returns:
        numpy.ndarray: the extracted front face.
        Also write this image to the outfile.

    """
    head, tail = os.path.split(f)

    # load the input image, resize it, and convert it to grayscale
    image = cv2.imread(f)
    height, width = image.shape[:2]
    # keep cropping the image to detect faces.
    for new_width in range(width, 100, -5):
        image = imutils.resize(image, width=new_width)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # detect faces in the grayscale image
        rects = detector(gray, 1)
        # loop over the face detections
        for (i, rect) in enumerate(rects):
            # determine the facial landmarks for the face region, then
            # convert the landmark (x, y)-coordinates to a NumPy array
            try:
                print(rect[0])
                continue
            except TypeError:
                #print(new_width)
                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
                left_list = []
                right_list = []
                up_list = []
                bottom_list = []
                #for (i, rect) in enumerate(rects):
                    # determine the facial landmarks for the face region, then
                    # convert the landmark (x, y)-coordinates to a NumPy array
                #shape = predictor(gray, rect)
                #shape = face_utils.shape_to_np(shape)
                # loop over the facial landmarks
                for (name, (i, j)) in face_utils.FACIAL_LANDMARKS_IDXS.items():
                    (x, y, w, h) = cv2.boundingRect(np.array([shape[i:j]]))
                    left_list.append(x)
                    right_list.append(x+w)
                    up_list.append(y)
                    bottom_list.append(y+h)
                left = min(left_list)
                right = max(right_list)
                up = min(up_list)
                bottom = max(bottom_list)
                left, right, up, bottom = firstmodify(left, right, up, bottom, 30) # 30 is the percentage, change it to control the margin width
                left, right, up, bottom = ifoverborder(left, right, up, bottom, width, height)
                left, right, up, bottom = finalmodify(left, right, up, bottom)
                roi = image[up:bottom, left:right]
                #roi = image[y:y + h, x:x + w]
                roi = cv2.resize(roi, (200,200), interpolation = cv2.INTER_AREA)
                output = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                #outfile = 'output/'+tail
                #cv2.imwrite(outfile,output)
                # change (96,96) to (1, 96*96)
                output = output.flatten()

                if not return_rectangle:
                    return output
                return output, [left, right, up, bottom, new_width]

def main():
    """
    This function is to extract the front face of the given images and write the result into 'pixel.pd' and 'error.txt'.

    """
    # set mulit-process number, equal to the number of cores
    # process_number = 1
    filepath = input("Filepath: ")
    start_number = int(input("start_id:"))
    error_file = ''
    os.mkdir('output')
    #pool = Pool(processes=process_number)
    output_array = []
    for f in glob.glob(filepath + '/**/*.*', recursive=True):
    #for f in glob.glob(filepath + '/*.*'):
        #print(f)
        print(str(start_number))
        head, tail = os.path.split(f)
        if re.search(r'^\d+ \w+.\w+$', tail) is not None:
        # for standard
            photo_id = re.findall(r'\d+', tail)[0]
        else:
        # for non standard
            photo_id = str(start_number)
        start_number += 1
        try:
            emotion = re.findall(r' ([A-Za-z]+)\.', tail)[0]
        except IndexError:
            emotion = 'Need to check'
        #result = pool.apply_async(conversion, (f,))
        #result.get()
        try:
            temp_output = conversion(f)
            output_array.append([photo_id, temp_output, emotion.strip().title(), tail])
            # if cannot convert, temp_output == None
            if temp_output is None:
                error_file += f + ': fail to find the front face\n'
        except:
            error_file += f + ': fail to find the front face\n'
            print('error')
    #pool.close()
    output_pd = pd.DataFrame(output_array, columns =['id', 'pixels', 'emotion', 'original_file'])

    with open('pixel.pd', 'wb') as fout:
        pickle.dump(output_pd, fout)
    with open('error.txt', 'w') as fout:
        fout.write(error_file)


if __name__ == "__main__":
    multiprocessing.freeze_support()  # must run for windows
    main()
