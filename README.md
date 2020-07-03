# Automated noise modelling based on a TIN

Noise simulations require finding the paths between multiple receiver and source points. In the current approach, only 3D polylines can be used as input to describe the terrain. These 3D polylines are semi-automatically generated, based on the principle of describing the terrain profile with as few height lines as possible.
In order to propose a more efficient, standardised and economic modelling approach, a partnership between RIVM/RWS and the 3D Geoinformation Group at TU Delft was launched in 2017, aiming to generate these height lines automatically from the available datasets, namely AHN3, BAG, and BGT, which are publicly available via PDOK for free. However, it was then proposed to prove that the paths between receiver and source points can be directly generated from a TIN without creating the height lines.
The following report provides proof of concept to the hypothesis: ‘Using a TIN directly allows automated 3D noise modelling according to the guidelines of CNOSSOS-EU’. A code was written to generate the paths between receiver and source points using an LoD2 TIN. The paths were then checked visually and were fed to test_Cnossos software to prove their validity. Finally, noise maps were generated and compared to noise maps generated with the current method.

For an explanation of the project and how the algorithm works, please visit the [repository](https://repository.tudelft.nl) (this will be updated)

This repository is for the 3D Noise Modelling Synthesis Project of the course GEO1011 at the MSc Geomatics program at the Delft Unversity of Technology.

This project is part of the research on [automated reconstruction of 3D input data for noise studies](https://3d.bk.tudelft.nl/projects/noise3d/) at the 3D geoinformation research group of Delft Unversity of Technology.

The final presentation can also be viewed on [Youtube](https://www.youtube.com/watch?v=Lf49yOw0eRo)

## Latest Release

https://zenodo.org/badge/latestdoi/259080654

## Installation

*how to install the software, on which platform*

This program consists of a set of python and shell script files. To run python files, [python](https://www.python.org/downloads/windows/) is required . It was only tested it with Python 3.7.

To run Shell script files [Git Bash](https://git-scm.com/download/win) was used, which in turn uses the MINGW64 compiler.

In order to compute the noise level for a cross section, [Test_Cnossos](https://github.com/genell/Cnossos-EU-SWE) is used. This software works only on windows!

Used Python libraries:
* pathlib
* Shapely (geometry and strtree)
* fiona
* time
* Numpy
* bisect
* xml.etree.cElementTree
* math
* os
* sys
* collections
* Scipy.spatial
* Json

## Usage

To create xml files for each path from source to receiver the main.py program is run.

To run the program the following command can be ran on the command line:

python main.py [constrained_tin] [semantics] [receivers] [sources] [output_folder]

Where:

constrained_tin = the file path to the constrained tin, this should be a 'objp' file type

semantics = the file path to the semantics, these are the buildings and ground types of the area

receivers = the file path to the receiver points

sources = the file path to the sources that generate noise, this should be a 'gml' file type

output_folder = this is the folder where the files will be outputted

### Generating an OBJP file

Since the objp file format is a new file format we provide a way to generate it. Currently only cityjson to objp is supported.

To create an objp file a program is provided, the create_objp.py file. To run the program run the following command:

python create_objp.py [input_file] [output_folder]

Where:

input_file = The file which is used as input to create the objp file. Currently only a cityjson file in which every boundary is a triangle can be used.

output_folder = The folder where the constrained tin objp file will be placed.

### Generating noise levels

Of course the final result should be something where every receiver has a noise level associated with it. To generate this you run the test_cnossos.sh script in the following manner:

./test_cnossos.sh [test_cnossos_release] [code_file_path] [xml_input_path] [xml_output_path] [receiver_dict] [receiver_shape_file]

Where:

test_cnossos_release = The file path to the test_cnossos release folder.

code_file_path = The path to where the python code noise_maps.py is located. This will generally be in the same folder as the test_cnossos.sh file and can thus the input can be '.'.

xml_input_path = The path to the folder of all the xml files printed by the main.py program.

xml_output_path = The path to the folder where the output of each xml file should go.

receiver_dict = The path to the file which maps receiver id to coordinates. This is generated by the main.py program and will be located in the output_folder with the name 'receiver_dict.txt'.

receiver_shape_file = The path to the file where the receivers with their noise value will be stored as a shapefile.

lastly, Test_cnossos prints a lot of information, this can cost a lot of time when computing many paths. This can be largely decreased by writing the output to another file. This can be done by adding " >> out.txt" to the command.

### Complete Pipeline

While the main.py program runs the main algorithm, there are multiple steps to the entire pipeline. We provide a way to run the entire timeline in one (1) command:

./complete.sh [input_file] [objp_output_folder] [semantics] [receivers] [sources] [output_folder] [test_cnossos_release] [code_file_path] [receiver_shape_file]

Where:

input_file = The file which is used as input to create the objp file. Currently only a cityjson file in which every boundary is a triangle can be used.

objp_output_folder = The folder where the constrained tin objp file will be placed.

semantics = The file path to the semantics, these are the buildings and ground types of the area

receivers = The file path to the receiver points

sources = The file path to the sources that generate noise, this should be a 'gml' file type

output_folder = This is the folder where the files will be outputted

test_cnossos_release = The file path to the test_cnossos release folder.

code_file_path = The path to where the python code noise_maps.py is located. This will generally be in the same folder as the test_cnossos.sh file and can thus the input can be '.'.

receiver_shape_file = The path to the file where the receivers with their noise value will be stored as a shapefile.

As with generating noise levels, running time can be largely reduced by adding " >> out.txt" at the end of the command.

## Limitations

*what are the things that one would expect from this software but it doesn't do them, or not correctly*

#### propagation paths
Noise can propagate in multiple ways, direct (line of sight), vertical diffracting (direct from source to receiver, where it diffracts over buildings / terrain in the cross section), reflecting (where the order is the number of reflections) and horizontal diffracting (around building corners).
This algorithm supports direct, vertical diffracted (as Test_Cnossos supports it), and 1st order reflected paths.
Therefore horizontal diffracted and multi order reflections are not yet supported (2nd order reflected is implemented but not used in the current release.)
Secondly, sound does not necessarily propagate in straight lines, this is a simplification, called homogenous conditions. There are also favourable (where the sound does not propagate in straight lines, but in curves) and unfavourable conditions (where the sound waves are curved towards the sky). Currently, on a horizontal level the algorithm supports only homogenous conditions. On a vertical level it support what is supported by Test_cnossos, which is homogenous and favourable conditions.

For first order reflections we use two tests to verify of the theoretical reflection path is valid.
The first test is a relative building size test te remove reflections near the edge of a building or on small buildings.
The second test is a relative building height test in the case of buildings with common walls. In this case the reflected building requires to be at least 1 meter higher then the adjacent building in front of the reflecting wall.
These tests filter out about all invalid paths. But in some scenario's paths are validated as correct, where they are not (false positive). This is further explained in the report (link at the top of the ReadMe)

#### Spikes
When there is a discrepancy between the precision of vertices in the constrained TIN and the semantics (buildings) in some cases (where the semantics file polygon is rounded of to the inner side, compared to the building in the constrained TIN) a reflection on that wall will have a spike in the cross section, making the computed value incorrect for that cross section.

#### Noise sources
the noise level of a road source is computed using a default noise per meter, and an estimation of the segment length of the noise source. Therefore it does not take speed limit, cars per hour or other types of sources in consideration

#### Materials
In Test_Cnossos a material can be assigned to each line segment in the cross section to describe the material in that part of the cross section. Currently the algorithm supports three materials, as the input consists of three types.
Buildings are always reflecting with a material 'A0'. This does not absorb any noise and has a sigma of 20000 kPa.s/m^2
The ground material input has a absorption value of either 0 or 1. For these values the respective materials 'G' and 'C' are selected.
The 'G' material does not absorb any sound and has a sigma of 20000 kPa.s/m^2. (refered to as asphalt or concrete)
the 'C' material does absorb all sound (g = 1) and has a sigma of 80 kPa.s/m^2. (refered to as turf, grass, loose soil)
However, in reality there are many more materials with different characteristics.

#### Barriers
Noise barriers, placed along highways, are not commonly represented (correctly) in the DTM. They are also not part of the BAG (Building address data of the Netherlands). Usually they are represented by means a line with a certain height. The algorithm does not support this, therefore this can either be added in the code, or barriers should be added as a building to the input.

#### Semantics
For now, the code only reads in the absorption index if set as 'bodemfactor' and the building part id if set as 'part_id'.

#### Test_cnossos error
During the development of this algorithm, it was noticed that in very few occasions (1 in 2000 paths) and error was raised by the Test_Cnossos software.
The reason of this error has not yet been found. The following two errors were noticed:

../../PropagationPath/MeanPlane.cpp, Line 56\
Expression: dist3 > 0

also, in even fewer cases the following error was noted:

File: ../../PropagationPath/PropagationPath.h, Line 409\
Expression: cp[pos_max].z_path <= cp[pos_max].pos.z

## Authors

The authors of this project are:\
Constantijn Dinklo\
Denis Giannelli\
Laurens van Rijssel\
Maarit Prusti\
Nadine Hobeika

We are all students from the master Geomatics at the Technical University of Delft.
We were supported by two tutors from the TU Delft:

Jantien Stoter\
Balazs Dukai

We were also supported by the RIVM and Rijkswaterstaat represented by:

Arnaud Kok (RIVM)\
Rob van Loon (RIVM)\
Renez Nota (Rijkswaterstaat)
