import fiona
import math
import misc
import time

class ReflectionPath:

    def __init__(self,sources,receivers,footprints):
        self.sources = sources
        self.receivers = receivers
        self.footprints = footprints

    def get_line_equation(self,p1,p2):
        """
        Explanation:A function that reads two points and returns the ABC parameters of the line composed by these points.
        ---------------
        Input:
        p1 [x(float),y(float)]
        p2 [x(float),y(float)]
        ---------------
        Output:
        parameters [a_norm(float),b_norm(float),c_norm(float)]
        """
        # EQUATION OF A LINE IN THE 2D PLANE:
        # A * x + B * y + C = 0
        a = p2[1] - p1[1]
        b = -(p2[0] - p1[0])
        c = -a*p1[0] -b*p1[1]
        m = math.sqrt(a*a + b*b)
        a_norm = a/m
        b_norm = b/m
        c_norm = c/m
        # EQUATION OF A LINE IN THE 2D PLANE WITH NORMALISED (UNIT) NORMAL VECTORs:
        # A' * x + B' * y + C' = 0
        parameters = [a_norm,b_norm,c_norm]
        return parameters # THE PARAMETERS OF THE NORMALISED LINE.

    def get_mirror_point(self,p1,parameters):
        """
        Explanation: A function that reads a point and the parameters of a line and returns the mirror point of p1 regarding this line.
        ---------------
        Input:
        p1 [x(float),y(float)]
        parameters [a_norm(float),b_norm(float),c_norm(float)]
        ---------------
        Output:
        p_mirror [x(float),y(float)]
        """
        # THE SIGNED DISTANCE D FROM P1 TO THE LINE L, I.E. THE ONE WITH THE PARAMETERS.
        d = parameters[0]*p1[0] + parameters[1]*p1[1] + parameters[2]
        p_mirror_x = p1[0] - 2*parameters[0]*d
        p_mirror_y = p1[1] - 2*parameters[1]*d
        return [p_mirror_x,p_mirror_y]

    def get_closest_point(self,p1,parameters):
        """
        Explanation: A function that reads a point and the parameters of a line and returns the mirror point of p1 regarding this line.
        ---------------
        Input:
        p1 [x(float),y(float)]
        parameters [a_norm(float),b_norm(float),c_norm(float)]
        ---------------
        Output:
        p_mirror [x(float),y(float)]
        """
        # THE SIGNED DISTANCE D FROM P1 TO THE LINE L, I.E. THE ONE WITH THE PARAMETERS.
        d = parameters[0]*p1[0] + parameters[1]*p1[1] + parameters[2]
        p_mirror_x = p1[0] - parameters[0]*d
        p_mirror_y = p1[1] - parameters[1]*d
        return [p_mirror_x,p_mirror_y]

    def line_intersect(self, line1, line2):
        """
        Explanation: this functions returns the intersection points (source points) of both lines
        ---------------
        Input:
        line1: the line segment of the receiver point
        line2: the line segment of the source
        ---------------
        Output:
        point : it returns the point where both line segments intersect
        """
        d = (line2[1][1] - line2[0][1]) * (line1[1][0] - line1[0][0]) - (line2[1][0] - line2[0][0]) * (line1[1][1] - line1[0][1])
        if d:
            uA = ((line2[1][0] - line2[0][0]) * (line1[0][1] - line2[0][1]) - (line2[1][1] - line2[0][1]) * (line1[0][0] - line2[0][0])) / d
            uB = ((line1[1][0] - line1[0][0]) * (line1[0][1] - line2[0][1]) - (line1[1][1] - line1[0][1]) * (line1[0][0] - line2[0][0])) / d
        else:
            return False
        if not(0 <= uA <= 1 and 0 <= uB <= 1):
            return False 
        x = line1[0][0] + uA * (line1[1][0] - line1[0][0])
        y = line1[0][1] + uA * (line1[1][1] - line1[0][1])
        return [x,y]
    
    def split_lineseg(self,n,lineseg):
        # ATTENTION !: THIS FUNCTION SPLITS ALL THE LINE SEGMENTS IN THE MODEL INTO A FIXED NUMBER OF SUB-SEGMENTS (N), REGARDLESS OF THE
        # LENGHT OF THE SEGMENT. AS A CONSEQUENCE, SMALL WALLS WILL HAVE VERY SMALL SUB-SEGMENTS, WHEREAS LONG WALLS WILL NOT.
        # AS AN ALTERNATIVE, "split_lineseg2" IS BEING USED IN THIS PROGRAM. IT SPLITS ALL WALLS INTO SUB-SEGMENTS WITH A PRE-DEFINED LENGTH (DIM). 
        """
        Explanation: A function that takes a line segment and splits it into multiple sub-segments, according to a specific number.
        ---------------
        Input:
        n: the number of line sub-segments in which lineseg will be divided into
        lineseg: the line segment in matter [[x1,y1],[xn,yn]]
        ---------------
        Output:
        ref_list: a list of all vertices of lineseg (polyline), including the two outermost and original ones.
        [[x1,y1],[x2,y2],[x3,y3].....[xn,yn]]
        """
        delta_x = lineseg[1][0] - lineseg[0][0] # delta_x can be positive, negative or zero, depending on the direction of the line.
        delta_y = lineseg[1][1] - lineseg[0][1] # delta_x can be positive, negative or zero, depending on the direction of the line.
        vertex = lineseg[0]
        ref_list = [vertex]
        for number in range(n):
            x = vertex[0] + delta_x/n
            y = vertex[1] + delta_y/n
            vertex = [x,y]
            ref_list.append(vertex)
        return ref_list

    def split_lineseg2(self,dim,lineseg):
        """
        Explanation: A function that takes a line segment and splits it into multiple sub-segments, each one of them with lenght = 'dim'
        ---------------
        Input:
        dim: the length of each sub-segment in which lineseg will be divided into
        lineseg: the line segment in matter [[x1,y1],[xn,yn]]
        ---------------
        Output:
        ref_list: a list of all vertices of lineseg (polyline), including the two outermost and original ones.
        [[x1,y1],[x2,y2],[x3,y3].....[xn,yn]]
        """
        delta_x = lineseg[1][0] - lineseg[0][0]
        delta_y = lineseg[1][1] - lineseg[0][1]
        length = math.sqrt(delta_x**2 + delta_y**2)
        n = math.floor(length//dim)
        ref_list = [lineseg[0]]
        for number in range(n):
            h = (number+1)*dim
            x = ((h * delta_x) / length) + lineseg[0][0]
            y = ((h * delta_y) / length) + lineseg[0][1]
            inter = [x,y]
            ref_list.append(inter)
        if ref_list[(len(ref_list)-1)] == lineseg[1]:
            pass
        else:
            ref_list.append(lineseg[1])
        return ref_list

    def get_candidate_point(self,dim):
        """
        Explanation: A function that gets all the walls from f_dict and create candidate reflection points.
        ---------------        
        Input:
        n: the number (int) foi segments in which the wall will be divided into.
        ---------------
        Output:
        void
        """
        for bag_id in f_dict:
            h_dak = f_dict[bag_id]['h_dak']
            walls = f_dict[bag_id]['walls']
            for wall in walls:
                ref_list = self.split_lineseg2(dim,wall)
                for point in ref_list:
                    point.append(h_dak)
                    candidate = [wall[0],point,wall[1]]
                    c_list.append(candidate)

    def get_first_paths(self,s,r):
        """
        Explanation: A function that reads a source point and a receiver and computes all possible first-order reflection paths,
        according to buildings that are stored in f_dict (separate dictionary)
        ---------------        
        Input:
        source s    [x,y,(z)]
        receiver r  [x,y,(z)]
        ---------------
        Output:
        A list of all (independent) points that are capable of reflecting the sound wave from source to receiver.:
        l = [ [ p1, p2, p3, .... pn ] , [ h1, h2, h3, .... hn ] ]
        such that:
        p = coordinates of the reflection point [x(float),y(float)]
        h = height value of the building in which the reflection point lies into (float)
        the n-th element of "p_list" corresponds to the n-th element of "h_list".
        """
        coords   = [ ]
        heights  = [ ]
        for bag_id in f_dict:
            h_dak = f_dict[bag_id]['h_dak']
            walls = f_dict[bag_id]['walls']
            for wall in walls:
                test_r = misc.side_test( wall[0], wall[1], r[:2]) #r[:2] makes the function to ignore an eventual 'z' value.
                test_s = misc.side_test( wall[0], wall[1], s[:2]) #s[:2] makes the function to ignore an eventual 'z' value.
                if test_r > 0 and test_s > 0: # This statement guarantees that S-REF and REF-R are entirely outside the polygon.
                    s_mirror = self.get_mirror_point(s,self.get_line_equation(wall[0],wall[1]))
                    ref = self.line_intersect(wall,[s_mirror,r[:2]])
                    if type(ref) == list:
                        coords.append(ref)
                        heights.append(h_dak)
                        ref_z = ref
                        ref_z.append(h_dak)
                        p1_list.append([s,ref_z,r])
        print('1st-order reflection. numer of paths:',len(coords))
        return [ coords, heights ] #[ [p1, p2, ..., pn], [h1, h2, ..., hn] ] 
    
    def get_second_paths(self,s,r,t):
        """
        Explanation: A function that reads a source point and a receiver and computes all possible SECOND-ORDER reflection paths,
        according to buildings that are stored in f_dict (separate dictionary)
        ---------------        
        Input:
        number n : number of sub-segments in wich the line will be divided.
        source s    [x,y,(z)]
        receiver r  [x,y,(z)]
        ---------------
        Output:
        A list of all (independent) point lists that are capable of reflecting the sound wave from source to receiver.:
        l = [ [ [p11, p12], [p21, p22], [p31, p32], .... [pn1, pn2] ] , [ [h11, h12], [h21, h22], [h31, h32], .... [hn1, hn2] ]
        such that:
        pn(1)(2) = coordinates of the reflection point [x(float),y(float)]
        hn = height value of the building in which the reflection point lies into (float)
        the n-th element of "p_list" corresponds to the n-th element of "h_list".
        """
        coords   = [ ]
        heights  = [ ]
        for candidate in c_list:
            #ref_list = []
            for bag_id in f_dict:
                h_dak = f_dict[bag_id]['h_dak']
                walls = f_dict[bag_id]['walls']
                for wall in walls:
                    test_c = misc.side_test( wall[0], wall[1], candidate[1][:2]) #r[:2] makes the function to ignore an eventual 'z' value.
                    test_s = misc.side_test( wall[0], wall[1], s[:2]) #s[:2] makes the function to ignore an eventual 'z' value.
                    if test_c > 0 and test_s > 0: # This statement guarantees that S-REF and REF-CANDIDATE are entirely outside the polygon.
                        s_mirror = self.get_mirror_point(s,self.get_line_equation(wall[0],wall[1]))
                        b = self.line_intersect(wall,[s_mirror,candidate[1][:2]])
                        if type(b) == list:
                            test_b = misc.side_test( candidate[0], candidate[2], b[:2])
                            test_r = misc.side_test( candidate[0], candidate[2], r[:2])
                            if test_b > 0 and test_r > 0:
                                b_mirror = self.get_mirror_point(b,self.get_line_equation(candidate[0], candidate[2]))
                                dist = math.sqrt(((b_mirror[0]-candidate[1][0])**2)+((b_mirror[1]-candidate[1][1])**2))
                                if dist > 0.1:
                                    if abs(misc.side_test( b_mirror, candidate[1][:2], r)) <= t:
                                        # GET CLOSEST POINT FROM R TO B_MIRROR_CANDIDATE[1]
                                        r_closest = self.get_closest_point(r,(self.get_line_equation(b_mirror,candidate[1])))
                                        r_closest.append(r[2])
                                        coords.append([b,candidate[1][:2]])
                                        heights.append([h_dak,candidate[1][2]])
                                        b_z = b
                                        b_z.append(h_dak)
                                        p2_list.append([s,b_z,candidate[1],r_closest])
        print('2nd-order reflection. numer of paths:',len(coords))
        return [ coords, heights ] #[ [ [p11, p12], [p21, p22], .... [pn1, pn2] ] , [ [h11, h12], [h21, h22], .... [hn1, hn2] ]

def read_buildings(input_file,dictionary):
    """
    Explanation: A function that reads footprints and stores all walls as [p1,p2] and absolute heights (float) of these.
    ---------------
    Input:
    input_file: a .gpkg file containing the footprints of the buildings.
    dictionary: an empty 'f_dict' dictionary in __main__
    ---------------
    Output:
    void.
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            bag_id = feature['properties']['bag_id']
            dictionary[bag_id] = { }
            z = feature['properties']['h_dak']
            dictionary[bag_id]['h_dak'] = z
            f_geom_coord = feature['geometry']['coordinates']
            f_geom_type = feature['geometry']['type']
            if f_geom_type == 'Polygon':
                for polygon_index in range(len(f_geom_type)):
                    polygon_object = f_geom_type[polygon_index]
                    walls = []
                    for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                        a = list(polygon_object[coord_index])
                        b = list(polygon_object[coord_index+1])
                        wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                        walls.append(wall_2D)
                    dictionary[bag_id]['walls'] = walls
            if f_geom_type == 'MultiPolygon':
                for multi_polygon_index in range(len(f_geom_coord)):
                    multi_polygon_object = f_geom_coord[multi_polygon_index]
                    for polygon_index in range(len(multi_polygon_object)):
                        polygon_object = multi_polygon_object[polygon_index]
                        walls = []
                        for coord_index in range(len(polygon_object[:(len(polygon_object)-1)])):
                            a = list(polygon_object[coord_index])
                            b = list(polygon_object[coord_index+1])
                            wall_2D = [a[:len(a)-1],b[:len(b)-1]]
                            walls.append(wall_2D)
                        dictionary[bag_id]['walls'] = walls
    layer.close()

def read_points(input_file,dictionary):
    """
    Explanation: A function that reads points and store their ids (int) and coordinates as [x,y].
    ---------------
    Input:
    input_file: a .gpkg file containing the points (with z coordinates)
    dictionary: an empty dictionary in __main__ (either s_dict for sources or r_dict for receivers)
    ---------------
    Output:
    void.
    """
    with fiona.open(input_file) as layer:
        for feature in layer:
            source_id = feature['properties']['id']
            p_geom_type = feature['geometry']['type']
            p_geom_coord = feature['geometry']['coordinates']
            if p_geom_type == 'Point':
                coord_obj = list(p_geom_coord)
            if p_geom_type == 'MultiPoint':
                for point in p_geom_coord:
                    coord_obj = list(point)
            dictionary[source_id] = coord_obj
    layer.close()

def write_candidates(output_file,lista):
    """
    Explanation: A function that writes a CSV file with all candidate points. It is used for visualising these points in QGIS.
    ---------------
    Input:
    output_file: the directory/name of the csv file to be created.
    lista: a list containing all candidate points in the following schema:
    [candidate_x, candidate_y, h_dak]
    ---------------
    Output:
    void.
    """
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    for candidate in lista:
        count += 1
        line = '%d \t PointZ (%f %f %f) \n' % (count,candidate[1][0],candidate[1][1],candidate[1][2])
        fout.write(line)
    fout.close()
    #PointZ (93539.68248698 441892 1.4)

def write_output_1st(output_file,lista):
    """
    Explanation: A function that writes a CSV file with the reflected paths. It is used for visualising the paths in QGIS.
    ---------------
    Input:
    output_file: the directory/name of the csv file to be created.
    lista: a list containing all the 1st order propagation paths in the following schema:
    [ [source_x, source_y, source_z,] , [reflection_x, reflection_y, h_dak], [receiver_x, receiver_y, receiver_z] ] 
    ---------------
    Output:
    void.
    """
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    for path in lista:
        count += 1
        sou = path[0]
        ref = path[1]
        rec = path[2]
        line = '%d \t MultiLineStringZ ((%f %f %f, %f %f %f, %f %f %f)) \n' % (count,sou[0],sou[1],sou[2],ref[0],ref[1],0,rec[0],rec[1],rec[2]) 
        fout.write(line)
    fout.close()
    #MultiLineStringZ ((93528.02305619 441927.11005859 2.5, 93567.67848824 441908.81858497 0, 93539.68248698 441892 1.4))

def write_output_2nd(output_file,lista):
    """
    Explanation: A function that writes a CSV file with the reflected paths. It is used for visualising the paths in QGIS.
    ---------------
    Input:
    output_file: the directory/name of the csv file to be created.
    lista: a list containing all the 1st order propagation paths in the following schema:
    [ [source_x, source_y, source_z,] , [b_ref_x, b_ref_y, b_ref_z], [c_ref_x, c_ref_y, c_ref_z], [receiver_x, receiver_y, receiver_z] ] 
    ---------------
    Output:
    void.
    """
    fout = open(output_file,'w')
    line = 'fid \t geometry \n'
    fout.write(str(line))
    count = 0
    for path in lista:
        # path = [s,b_z,candidate,r]
        count += 1
        sou =   path[0]
        b_ref = path[1]
        c_ref = path[2]
        rec =   path[3]
        line = '%d \t MultiLineStringZ ((%f %f %f, %f %f %f, %f %f %f, %f %f %f)) \n' % (count,sou[0],sou[1],sou[2],b_ref[0],b_ref[1],b_ref[2],c_ref[0],c_ref[1],c_ref[2],rec[0],rec[1],rec[2]) 
        fout.write(line)
    fout.close()
    #MultiLineStringZ ((93528.02305619 441927.11005859 2.5, 93567.67848824 441908.81858497 0, 93539.68248698 441892 1.4))

if __name__ == "__main__":
    start = time.time()
    f_dict = { }
    s_dict = { }
    r_dict = { }
    c_list = [ ]
    p1_list = [ ]
    p2_list = [ ]

    # DATASETS FOR 'MID PRESENTATION'
    read_buildings('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/03_midpresentation/buildings_lod_13.gpkg',f_dict)
    read_points('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/03_midpresentation/sources.gpkg',s_dict)
    read_points('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/03_midpresentation/receivers.gpkg',r_dict)

    reflection_path = ReflectionPath(s_dict,r_dict,f_dict)
    reflection_path.get_candidate_point(0.025) # DIM 0.025

    write_candidates('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/03_midpresentation/candidates0025.csv',c_list)

    for source in s_dict:
        for receiver in r_dict:
            print('source:',source,'receiver',receiver)
            reflection_path.get_first_paths(s_dict[source],r_dict[receiver])
            reflection_path.get_second_paths(s_dict[source],r_dict[source],0.1) # THRESHOLD 0.1
            print()
    
    print('len(p1_list)')
    print(len(p1_list))
    print()
    print('len(p2_list)')
    print(len(p2_list))

    write_output_1st('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/03_midpresentation/path_1st.csv',p1_list)
    write_output_2nd('//Users/denisgiannelli/Documents/DOCS_TU_DELFT/_4Q/GEO1101/06_DATA/03_midpresentation/path_2nd_dim00025_t01.csv',p2_list)

    end = time.time()
    processing_time = end - start
    print('processing time:',round(processing_time,2),'s')