# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 20:09:46 2020

@author: kornilov
"""
import glob
from matplotlib.image import imread
from matplotlib.image import imsave
import numpy

cards=glob.glob('ComeniusDixitBot/Dixit4_pairs/*jpg')

img=[]
for k in range(0,len(cards)):
    img=imread(cards[k])
    imsave('ComeniusDixitBot/Dixit4/card'+str(2*k)+'.jpg',img[20:1010:3,85:770:3])
    imsave('ComeniusDixitBot/Dixit4/card'+str(2*k+1)+'.jpg',img[20:1010:3,770:1455:3])
