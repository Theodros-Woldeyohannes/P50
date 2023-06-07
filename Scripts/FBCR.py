#Import Modules, Set Environments

import arcpy
import os
from arcpy import env
from arcpy.sa import *
import sys

path = os.path.dirname(sys.path[0])
env.workspace = path
env.overwriteOutput = True

#pass license error exception so error messages are loaded into Python

class LicenseError(Exception):
    pass

#Get user inputs, Define as new variables

lb = int(arcpy.GetParameterAsText(0))
up = int(arcpy.GetParameterAsText(1))
inc = int(arcpy.GetParameterAsText(2))
valdata = arcpy.GetParameterAsText(3)
inRast = arcpy.GetParameterAsText(4)
outVIT = arcpy.GetParameterAsText(5)
d_var = arcpy.GetParameterAsText(6)

#make feature layer from input feature class
Radiat = arcpy.MakeFeatureLayer_management(valdata)

#Make range of desired sample subsets based on user inputs, Define as new variable

levels = range(lb,up,inc)

#For each sample subset: Create random points using input shapefile as template, Make random points feature layer,
#Join (spatial) input shapefile data to random points

for x in levels:
    arcpy.AddMessage('creating point feature ' + str(x))
    arcpy.CreateRandomPoints_management('randompts', str(x), Radiat, number_of_points_or_field = x)
    arcpy.AddMessage('joining point feature ' + str(x))
    rndpts = arcpy.MakeFeatureLayer_management(r'randompts/' + str(x) + '.shp', out_layer = 'rndpts')
    arcpy.SpatialJoin_analysis(target_features = rndpts, join_features = Radiat, out_feature_class = r'Extracted Points/' + str(x), match_option = 'CLOSEST')

#Make list of random points, Define as new varibale
#Create empty list to hold input rasters
#Split input Raster list

pointsdir = os.listdir(path + '\\randompts')
inRasterList = []
inRastList = inRast.split(";")

#Use try except statements to handle license errors
#Check out Spatial Analyst Extension
#Read in rasters and append to raster list
#Make random points feature layers, Extract raster data to points
#Count how many rasters are read in

try:
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        raise LicenseError
    i = 0
    for r in inRastList:
        arcpy.AddMessage('Reading in Rasters')
        inRasterList.append(arcpy.Raster(r))
        i = i + 1
    for x in pointsdir:
        if x[-3:] == 'shp':
            arcpy.AddMessage('extracting ')
            points = arcpy.MakeFeatureLayer_management(r'Extracted Points/' + str(x), 'points')
            arcpy.AddMessage('saving ' + str(x))
            extract = ExtractMultiValuesToPoints(points, inRasterList)



    #Make list of extracted points, Define as new variable
    #Define input for Forest Based Classification and Regression (FBCR) as extracted points
    #Define dependent variabe from user input
    #List field objects for extracted points, Define variable as empty list, Retrieve name of field and append to variable list (explan)
    #Define new list as number of fields (count of rasters) from end of FBCR input (fields holding extracted raster values)
    #For each raster value, append Field Name and FBCR distribution type to new empty list (explan_sub), append this list to new empty list (explan_var),
    ##Clear explan_sub before interating though next field, explan_var is the final explanatory variable object before input into FBCR
    #Use Update Cursor to delete missing values (i.e. -9999) from FBCR input
    #Define output file, output importance table, prediction type, number of trees, percent of data available to decision trees (sample size),
    #percent of data set aside for training
    #Run FBCR


    currdir = os.listdir(path + '\\Extracted Points')
    for x in currdir:
        if x[-3:] == 'shp' and x[:-4] != 'Clipped_data':
            arcpy.AddMessage('Running FBCR for ' + str(x[:-4]))
            FBCR_input = arcpy.MakeFeatureLayer_management(r'Extracted Points/' + x, 'FBCR_input')
            dependent = d_var
            explan_var = []
            explan_sub = []
            fields = arcpy.ListFields(FBCR_input)
            explan = []
            for field in fields:
                explan.append(field.name)

            explan_list = explan[-i:]
            for e in explan_list:
                explan_sub.append(e)
                explan_sub.append("false")
                explan_var.append(explan_sub)
                explan_sub = []
                sql = e + ' = ' + '-9999'
                with arcpy.da.UpdateCursor(FBCR_input, e, sql) as cursor:
                    for row in cursor:
                        cursor.deleteRow()

            del cursor

            outF = None
            output_importance_table = r'Importance/' + x[:-4]
            prediction_type = "TRAIN"
            number_of_trees = 100
            sample_size = 100
            percentage_for_training = 10
            arcpy.stats.Forest(prediction_type, FBCR_input, dependent, None, explan_var, None, None, None, None, None, None,
                None, None, outF, output_importance_table, True, number_of_trees, None, None, sample_size, None, percentage_for_training)

    #Make list of output variable importance tables, Define as new variable
    #Convert tables to csv

    resdir = os.listdir(path + '\\Importance')

    for file in resdir:
        if file[-4:] == '.dbf':
            arcpy.AddMessage('converting ' + file + ' to csv')
            arcpy.conversion.TableToTable(r'Importance/' + file, outVIT, file[:-4] + '.csv')

#Print any license and tool errors

except LicenseError:
    print("Spatial Analyst license is unavailable")
except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))










