import bisect
import misc
import numpy as np
import xml.etree.cElementTree as ET

class XmlParser:
    
    def __init__(self, path, ext, mat):
        self.vts = np.array(path)
        self.mat = mat
        self.ext = ext

    def normalize_path(self):
        """
        Explination: Move 3D Cartesian coordinates relative to the starting point (receiver) by subtraction P0 from everypoint
        Make all height >= 0
        make the path in positive x and y direction
        ---------------
        Input: void
        ---------------
        Output: void
        """
        # move all vertices relative to first vertex
        self.vts -= self.vts[0]
        # make all height >= 0
        z_min = np.min(self.vts[:,2])
        if(z_min < 0): self.vts[:,2] -= z_min

        # unfold the path, if it is direct
        #if(len(self.ext) <= 2):
        #    self.vts = np.array([[(x ** 2 + y ** 2) ** 0.5, 0, z] for [x,y,z] in self.vts])

        # Make it in positive x and y direction
        #self.vts[:,0] = abs(self.vts[:,0])
        #self.vts[:,1] = abs(self.vts[:,1])
        

    def get_offsets_perpendicular(self, start, end):
        """
        Explination:
            calculates the perpendicular distance from points to the the line
        ---------------
        Input: 
            Start: integer - id of the start point
            end: integer - id of the end point
        ---------------
        Output: 
            numpy array - array of the offsets of points along line segment
        """
        p_start = self.vts[start]
        p_end = self.vts[end]
        line_length = ((p_end[2] - p_start[2]) ** 2 + (p_end[0] - p_start[0]) ** 2) ** 0.5
        offsets = []

        for id in range(start+1, end):
            # do side test (return lenght of line x perpendicualr distace) so devide it by the length and voila
            diff = abs(misc.side_test((p_start[0], p_start[2]), (p_end[0], p_end[2]), (self.vts[id,0], self.vts[id,2]))) / line_length
            offsets.append(diff)

        return np.array(offsets)

    def douglas_Peucker(self, threshold):
        """
        Explination:
            simplifies the path using douglas peucker algorithm
        ---------------
        Input: 
            Threshold: the minimal perpendicular distance between a line and a point for the point to be imported.
        ---------------
        Output: 
            void (updates self.vts)
        """
        # === create initial path ===
        # initalize simple path with all points that have an extension (source, receiver, barrier, etc)
        path_simple = []
        assert(len(self.ext) > 1)
        for key in self.ext:
            bisect.insort(path_simple, key)

        # maintain the line material, insert every points where the material changes
        for i in range(len(self.mat)-1):
            if(self.mat[i] != self.mat[i+1]):
                if i not in self.ext:
                    bisect.insort(path_simple, i)

        # == insert relevant points ===
        i = 0
        while(i < len(path_simple) - 1):
            start = path_simple[i]
            end = path_simple[i+1]

            if(end - start < 2):
                i += 1 # go to bext segment
                continue

            # Get the offset between the line from start to end, and the points in between
            offsets = self.get_offsets_perpendicular(start, end)
            
            # get the id of the highest offset
            id_max = np.argmax(offsets)

            # Check if the offset is above the treshold, if so, add the point to the list
            if(offsets[id_max] > threshold):
                # Make sure to get the right id, id_max starts at 0, but 0 is already 1 further than the start point.
                path_simple.insert(i+1, id_max + start + 1)
            else:
                i += 1
        
        # === post-processing; update extension dictionary, materials and vertices ===
        # Update the extensions with the new positions in the list.
        for id, id_old in enumerate(path_simple):
            if id_old in self.ext and id != id_old:
                # Create a new key, with the correct id, and assign is het value of the old id that is popped.
                self.ext[id] = self.ext.pop(id_old)

        self.mat = [self.mat[id] for id in path_simple]
        self.vts = np.array([self.vts[id] for id in path_simple])

    def write_xml(self, filename, Lw, validate):
        """
        Explination:
            1. create a element tree and set general information
            2. insert points in tree
            3. set point types (source, receiver etc)
            4. write to file
        ---------------
        Input: 
            filename of the output file (including the path)
        ---------------
        Output: void (writes output file)
        """
        # intialize element tree
        root = ET.Element("CNOSSOS-EU", version="1.001")
        method = ET.SubElement(root, "method")

        # Set the Method (same for all)
        ET.SubElement(method, "select", id="JRC-2012")

        # when validate is True, then the xml file will be validated by the TestCnossos software, if validate is false it is not checked, this will save time when we know the input in horizontal and orientation is correct
        if(not validate):
            options = ET.SubElement(method, "options")
            ET.SubElement(options, "option", id="CheckHorizontalAlignment", value="false")
            ET.SubElement(options, "option", id="ForceSourceToReceiver", value="false")
            ET.SubElement(options, "option", id="CheckSoundPowerUnits", value="false")
            # ET.SubElement(options, "option", id="CheckLateralDiffraction", value="false") maybe add this to fix error.
            

        meteo = ET.SubElement(method, "meteo", model="DEFAULT")
        ET.SubElement(meteo, "pFav").text = "0.3"
        
        # create the path
        path = ET.SubElement(root, "path")

        for id in range(len(self.vts)):
            # create a control point
            cp = ET.Element("cp")

            # insert the pos (position)
            pos = ET.SubElement(cp, "pos")
            ET.SubElement(pos, "x").text = "{:.2f}".format(self.vts[id,0])
            ET.SubElement(pos, "y").text = "{:.2f}".format(self.vts[id,1])
            ET.SubElement(pos, "z").text = "{:.2f}".format(self.vts[id,2])
            
            # Insert the material
            ET.SubElement(cp, "mat", id=self.mat[id])

            # append the created control point to the path
            path.append(cp)

        for id, val in self.ext.items():
            # set the first point as receiver
            ext = ET.Element("ext")
            ext_type = ET.SubElement(ext, val[0])

            # if its a source, this comes before the height
            if(val[0] == "source"):
                ET.SubElement(ext_type, "h").text = "{:.2f}".format(val[1])
                # Compute the right noise level based on the source line length
                power_levels = Lw['power'] + 10 * np.log10(val[2])
                power_levels_str = ""
                for dB in power_levels:
                    power_levels_str += " {:.1f}".format(dB)

                ET.SubElement(ext_type, "Lw", 
                    sourceType=Lw['sourceType'],
                    measurementType=Lw['measurementType'],
                    frequencyWeighting=Lw['frequencyWeighting']
                ).text = power_levels_str

            # If the extension type is wall or edge (refelction or diffraction, store the height and the material)
            elif (val[0] == "wall" or val[0] == "edge"):
                ET.SubElement(ext_type, "h").text = "{:.2f}".format(val[1])
                ET.SubElement(ext_type, "mat", id=val[2])
            
            # currently only when the extension is receiver, only store the relative height above ground.
            else:
                ET.SubElement(ext_type, "h").text = "{:.2f}".format(val[1])

            # add this extension to the right path element (control point)
            path[id].append(ext)

        # create a tree from the whole root to the tree and write it to a file.
        tree = ET.ElementTree(root)
        tree.write(filename, encoding="UTF-8", xml_declaration=True)
