import bisect
import numpy as np

from crossSection import CrossSection
from misc import interpolate_edge, reverse_bisect_left
from pprint import pprint

class CrossSectionManager:

    def __init__(self, source_default_height, receiver_default_height):
        self.cross_sections = {}
        self.receiver_triangles = {}

        self.source_default_height = source_default_height
        self.receiver_default_height= receiver_default_height
    
    def get_cross_section(self, receiver, path, tin, ground_type_manager, building_manager, source_height, receiver_height, reflection_heights=0):
        cross_section = CrossSection(path, receiver, reflection_heights)

        #Find the triangle of the tin in which the receiver is located.
        if receiver in self.receiver_triangles.keys():
            receiver_triangle = self.receiver_triangles[receiver]
        else:
            init_tr = tin.find_vts_near_pt(receiver)
            receiver_triangle = tin.find_receiver_triangle(init_tr, receiver)
            self.receiver_triangles[receiver] = receiver_triangle

        #Create the cross section from the receiver to the source point        
        cross_section.get_cross_section(receiver_triangle, tin, ground_type_manager, building_manager, source_height, receiver_height)

        if receiver not in self.cross_sections.keys():
            self.cross_sections[receiver] = []
        
        self.cross_sections[receiver].append(cross_section)
        
        return cross_section
    
    def get_intermediate_cross_section_collinear_source(self, source_point, cross_section, source_height, receiver_height, receiver):

        # find where the intermediate sources lie in the 'complete' cross-section

        # check if the cross section is going in the positive or negative direction
        if cross_section.vertices[-1][0] - cross_section.vertices[0][0] < 0:
            split_idx = reverse_bisect_left(cross_section.vertices, source_point)

        # if the path is parallel with the x axis, check if the y axis is in negative direction.
        elif cross_section.vertices[-1][0] - cross_section.vertices[0][0] == 0 and cross_section.vertices[-1][1] - cross_section.vertices[0][1] < 0:
            split_idx = reverse_bisect_left(cross_section.vertices, source_point)

        # the x direction is positive, or y is in positive direction
        else:
            split_idx = bisect.bisect_left(cross_section.vertices, source_point)

        part_path_direct = cross_section.vertices[split_idx:]
        source_ground_height = interpolate_edge(cross_section.vertices[split_idx - 1], cross_section.vertices[split_idx], source_point)
        part_path_direct = [(source_point[0], source_point[1], source_ground_height)] + part_path_direct

        cross_section_collinear_point = CrossSection([source_point], receiver, 0)
        cross_section_collinear_point.vertices = part_path_direct
        cross_section_collinear_point.extension = {
            0: ["source", source_height],
            len(cross_section_collinear_point.vertices) - 1 : ["receiver", receiver_height]
        }
        part_path_direct_material = [cross_section.materials[split_idx]] + cross_section.materials[split_idx:]
        cross_section_collinear_point.materials = part_path_direct_material
        
        # Key must already exist, so no need to check.
        self.cross_sections[receiver].append(cross_section_collinear_point)
        return
    
    def get_cross_sections_direct(self, direct_paths, tin, ground_type_manager, building_manager, source_height, receiver_height):
        """
        Explanation: Finds cross sections for all propagation paths, both direct. and saves them in a dicitonary with cross_sections objects.
        ---------------
        Input:
            propagation_paths_dict_direct : dictionary - receiver is key, value is a list with the sources 
            propagation_paths_dict_reflect : dictionary - receiver is key, value is a list with the reflection point and the source
            source_height : float - height above ground for the source (defines in main.py)
            receiver_height : float - height above ground for the receiver (defined in main.py)
            tin : GroundTin object - stores the DTM in a triangle datastructure
            ground_type_manager : GroundTypeManager object - stores all the groundtype objects
            building_manager : BuildingManager object - stores all the building objects
        ---------------
        Output:
            void (fills self.cross_section_manager for each receiver with a list of paths)
        """

        #
        i = 0
        for receiver, ray_intersects in direct_paths.items():
            print(i, receiver)
            i += 1
            #For each ray, grab all the source points between the receiver and the ray_end
            for ray_end, source_points in ray_intersects.items():
                #Create cross section for the furthest away point
                furthest_source_point = source_points[-1]
                cross_section = self.get_cross_section(receiver, [furthest_source_point], tin, ground_type_manager, building_manager, source_height, receiver_height)

                # create cross sections for intermediate source points, if available
                for source_point in source_points[:-1]:
                    #print("got collinear path")
                    self.get_intermediate_cross_section_collinear_source(
                        source_point, 
                        cross_section, 
                        source_height, 
                        receiver_height, 
                        receiver
                        )

        return

    def get_cross_sections_reflection(self, reflection_path, tin, ground_type_manager, building_manager, source_height, receiver_height):

        # can work with single and multi order reflection.
        # for each reflection
        for i, reflection_points_list in enumerate(reflection_path.reflection_points):
            #take the heights
            reflection_heights = reflection_path.reflection_heights[i]
            path = reflection_points_list
            path.append(reflection_path.source)

            self.get_cross_section(reflection_path.receiver, path, tin, ground_type_manager, building_manager, source_height, receiver_height, reflection_heights)
    
    def write_obj(self, filename):
        """
        Explanation: Write the paths of this receiver to an obj file, calls write_cross_section_to_obj
        ---------------
        Input:
            filename : string - filename, including path and extension(.obj)
        ---------------
        Output:
            void (writes obj file)
        """
        i = 0
        for receiver, cross_sections in self.cross_sections.items():
            self.write_cross_section_to_obj(str(i) + filename, cross_sections)
            i += 1

    def write_cross_section_to_obj(self, obj_filename, cross_sections):
        print("=== Writing {} ===".format(obj_filename))

        with open(obj_filename, 'w') as f_out:
            vts_count_lst = [0]
            counter = 0
            for cross_section in cross_sections:
                path = cross_section.vertices
                path = np.array(path)
                counter = counter + len(path)
                vts_count_lst.append(counter)
                for v in path:
                    f_out.write("v {:.2f} {:.2f} {:.2f}\n".format(v[0], v[1], v[2]))
            
            #print(vts_count_lst)
            for i, cross_section in enumerate(cross_sections):
                path = cross_section.vertices
                base = vts_count_lst[i]
                f_out.write("l")
                for i in range(len(path)):
                    f_out.write(" " + str(base + i + 1))
                f_out.write("\n")