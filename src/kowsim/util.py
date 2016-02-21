# -*- coding: utf-8 -*-
import math, csv 

def dot2d(vec1, vec2):
    return vec1.x() * vec2.x() + vec1.y() * vec2.y()
 
def len2d(vec):
    return math.sqrt( vec.x()*vec.x() + vec.y()*vec.y() )
 
def dist2d(p1, p2):
   dx = p1.x() - p2.x()
   dy = p1.y() - p2.y()
   return math.sqrt( dx**2 + dy**2 )
